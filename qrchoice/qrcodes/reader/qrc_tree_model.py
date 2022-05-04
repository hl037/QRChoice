import sys
from dataclasses import dataclass
from functools import cached_property, wraps
from contextlib import contextmanager
import sqlalchemy as sa
from PySide6.QtWidgets import (
    QApplication, QWidget, QGraphicsView, QUndoView,
    QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPolygonItem,
    QGraphicsRectItem, QGraphicsItemGroup, QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
)
from PySide6.QtGui import (
    QPixmap, QPolygonF, QUndoCommand, QUndoStack, QIcon, QPainterPath, QBrush, QColor
)
from PySide6.QtCore import (
    Qt,Slot, Signal, QObject,
    QPointF, QRectF, QPoint,
    QAbstractItemModel, QModelIndex, QPersistentModelIndex, QItemSelectionModel,
)

from ...database import DB, _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter
from . import QRChoiceRun


from ...debug_utils import *


NON_EDITABLE_BRUSH = QBrush(QColor(0xff, 0x88, 0x00, 0x55))

def dicho(l, e, cmp):
  """
  Perform dichotomic search and return index of element just after
  """
  i = 0
  j = len(l)
  while i != j :
    k = (i + j) // 2
    c = cmp(l[k], e)
    if c == 0 :
      return k
    if c < 0 :
      i = k + 1
    else :
      j = k
  return i


class DBWrapper(object):
  """
  A DB Wrapper to implement later smarter cache to avoid to much requests
  """
  stmt_run_sel = sa.select(R)
  stmt_im_sel = sa.select(I).where(I.run_id == sa.bindparam('run_id'))
  stmt_qrc_sel = sa.select(C).where(C.img_id == sa.bindparam('im_id'))
  stmt_run_sel = sa.select(R)
  stmt_im_sel = sa.select(I).where(I.run_id == sa.bindparam('run_id'))
  stmt_qrc_sel = sa.select(C).where(C.img_id == sa.bindparam('im_id'))
  _im_id = sa.bindparam('im_id')
  stmt_qrc_sel_extra = sa.select(C).where(
    (C.img_id == I.id) &
    (I.id != _im_id) &
    (I.target == sa.bindparam('im_target')) &
    (I.target_id == sa.bindparam('im_target_id'))
  )
  del _im_id
  
  def __init__(self, db:DB):
    self.db = db
    self.cur_run = None
    self.cur_im = None
    self._run = None
    self._im = None
    self._qrc = None
    self._extra_qrc_row = None

  def session(self):
    return self.db.session()

  def run(self, S:sa.orm.Session):
    if self._run is None :
      self._run = S.scalars(self.stmt_run_sel).all()
    return self._run
    
  def im(self, S:sa.orm.Session, run_id):
    if self.cur_run != run_id :
      self.cur_run = run_id
      self._im = S.scalars(self.stmt_im_sel, {'run_id': run_id}).all()
    return self._im

  def qrc(self, S:sa.orm.Session, im_id):
    if self.cur_im != im_id :
      self.cur_im = im_id
      self._qrc = list(S.scalars(self.stmt_qrc_sel, {'im_id': im_id}).all())
      data = { qrc.data for qrc in self._qrc }
      self._extra_qrc_row = len(self._qrc)
      im = S.get(I, im_id)
      if im.target_id :
        for qrc in S.scalars(self.stmt_qrc_sel_extra, {'im_id': im_id, 'im_target': im.target, 'im_target_id':im.target_id}) :
          if qrc.data not in data :
            data.add(qrc.data)
            self._qrc.append(qrc)
        

    return self._qrc

  def runCount(self, S:sa.orm.Session):
    return len(self.run(S))

  def imCount(self, S:sa.orm.Session, run_id):
    return len(self.im(S, run_id))

  def qrcCount(self, S:sa.orm.Session, im_id):
    return len(self.qrc(S, im_id))

  def getRun(self, S:sa.orm.Session, ind):
    return self.run(S)[ind]

  def getIm(self, S:sa.orm.Session, run_id, ind):
    return self.im(S, run_id)[ind]

  def getQrc(self, S:sa.orm.Session, im_id, ind):
    return self.qrc(S, im_id)[ind]
  
  def isExtraQrc(self, S:sa.orm.Session, im_id, ind):
    self.qrc(S, im_id)
    return ind >= self._extra_qrc_row

  @contextmanager
  def noCache(self):
    self.cur_im, self.cur_run, self._qrc, self._im, self._run, self._extra_qrc_row = None, None, None, None, None, None
    yield
    self.cur_im, self.cur_run, self._qrc, self._im, self._run, self._extra_qrc_row = None, None, None, None, None, None
    


  def commit(self, S: sa.orm.Session, objs, invalidate_im=False, invalidate_run=False):
    n_objs = [ S.merge(obj) for obj in objs ]
    ic('')
    ic('commit', n_objs)
    S.add_all(n_objs)
    S.flush()
    for obj in n_objs :
      S.refresh(obj)
    if invalidate_im :
      self.cur_im = None
    if invalidate_run :
      self.cur_run = None
    ic(n_objs)
    return n_objs
      
  def remove(self, S: sa.orm.Session, objs, invalidate_im=False, invalidate_run=False):
    n_objs = [ S.merge(obj) for obj in objs ]
    ic('')
    ic('remove', n_objs)
    for obj in n_objs :
      S.delete(obj)
    S.flush()
    if invalidate_im :
      self.cur_im = None
    if invalidate_run :
      self.cur_run = None
      
  def toggle_ignore(self, S:sa.orm.Session, run_id, row):
    im = self.getIm(S, run_id, row)
    im.ignore = not im.ignore
    S.add(im)
    S.commit()
    self.cur_run = None

  def pre_dispatch(self, S:sa.orm.Session, im:I) -> tuple[set[int], bool]:
    same_target_stmt = sa.select(I.id).where((I.target == sa.bindparam('target')) & (I.target_id == sa.bindparam('target_id')))
    changed_im = {im.id}
    r = S.get(R, im.run_id)
    run = QRChoiceRun(self.db, r)
    old_target = im.target, im.target_id
    if im.target_id is not None :
      changed_im.update(S.scalars(same_target_stmt, {'target': im.target, 'target_id':im.target_id}))
    run.dispatch(S, [im.id])
    S.refresh(im)
    if im.target_id is not None :
      changed_im.update(S.scalars(same_target_stmt, {'target': im.target, 'target_id':im.target_id}))
    new_target = im.target, im.target_id
    return changed_im, old_target != new_target



  
rootmi = QModelIndex()

@dataclass(frozen=True, slots=True)
class _ModelNode(object):
  """
  Class to hold a node (so that it can be retrieve with the node dict only)
  """
  kind: int
  id: int
  row: int
  col: int
  parent: '_ModelNode'
  
  def __hash__(self):
    return hash((self.kind, self.id, None if self.parent is None else self.parent.id, self.col))

  def __eq__(self, oth):
    if isinstance(oth, tuple) :
      kind, id, parent_id, col = oth
      if self.kind == kind and self.id == id and self.col == col :
        if self.parent is None :
          return parent_id is None
        return self.parent.id == parent_id
      return False
    else :
      return self.kind == oth.kind and self.id == oth.id and self.parent == oth.parent and self.col == oth.col

  def as_tuple(self):
    return self.kind, self.id, (self.parent.id if self.parent else None), self.col

class UndoStackModelMixin(object):
  """
  Mixin for handling an undo stack
  """
  class ModelEditCommand(QUndoCommand):
    def __init__(self, model:QAbstractItemModel, mi:QModelIndex, val, role:int):
      super().__init__()
      self.model = model
      self.mi = self.model.indexToPersistent(mi)
      self.new_val = val
      self.role = role
      self.old_val = self.model.data(mi, self.role)
      self._success = False
      self.setText(f'db change role: {role}')
        

    def redo(self):
      mi = self.model.persistentToIndex(self.mi)
      self._success = self.model.doSetData(mi, self.new_val, self.role)

    def undo(self):
      mi = self.model.persistentToIndex(self.mi)
      self.model.doSetData(mi, self.old_val, self.role)
      
  def __init__(self, stack:QUndoStack, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.undoStack = stack

  def indexToPersistent(self, mi:QModelIndex):
    raise NotImplementedError()

  def persistentToIndex(self, p):
    raise NotImplementedError()
    
  def setData(self, mi:QModelIndex, val, role:int):
    cmd = self.ModelEditCommand(self, mi, val, role)
    self.undoStack.push(cmd)
    if not cmd._success :
      cmd.setObsolete(True)
    return cmd._success

  
  
  
class QRCTreeModel(UndoStackModelMixin, QAbstractItemModel):
  """
  Model to display a list of images in a run, the image stored in them, and the qrc found.
  """
  Run = 0
  Im = 1
  Qrc = 2

  DBRole  = Qt.UserRole + 0
  PolygonRole = Qt.UserRole + 1

  class AddQrcCmd(QUndoCommand):
    """
    Command to add / remove 
    """
    def __init__(self, model:'QRCTreeModel', parent_mi:QModelIndex, box):
      super().__init__()
      assert parent_mi != rootmi
      key = parent_mi.internalPointer() # type: _ModelNode
      assert key.kind == model.Im
      self.model = model
      self.parent_mi = parent_mi
      with model.dbw.session() as S :
        count = model.dbw.qrcCount(S, key.id)
      self.obj = C(
        img_id=key.id,
        data=None,
        box=box,
      )
      self.setText(f'Add qrc')

    def redo(self):
      self.obj = self.model._commit(self.parent_mi, (self.obj,), invalidate_im = True)[0]

    def undo(self):
      self.model._remove(self.parent_mi, (self.obj,), invalidate_im = True)
      
  class RemQrcCmd(QUndoCommand):
    """
    Command to add / remove 
    """
    def __init__(self, model:'QRCTreeModel', parent_mi:QModelIndex, row:int, count:int):
      super().__init__()
      assert parent_mi != rootmi
      key = parent_mi.internalPointer() # type: _ModelNode
      assert key.kind == model.Im
      self.model = model
      self.parent_mi = parent_mi
      with self.model.dbw.session() as S :
        l = model.dbw.qrc(S, key.id)
      self.objs = l[row:row+count]
      self.setText(f'Remove qrc')

    @ic_indent
    def redo(self):
      self.model._remove(self.parent_mi, self.objs, invalidate_im = True)

    @ic_indent
    def undo(self):
      self.objs = self.model._commit(self.parent_mi, self.objs, invalidate_im = True)

  class RemImCmd(QUndoCommand):
    """
    Command to mark ignore on an image
    """
    def __init__(self, model:'QRCTreeModel', parent_mi:QModelIndex, row):
      super().__init__()
      assert parent_mi != rootmi
      key = parent_mi.internalPointer() # type: _ModelNode
      assert key.kind == model.Run
      self.model = model
      self.parent_mi = parent_mi
      self.row = row
      self.setText('Toggle image')

    @ic_indent
    def redo(self):
      self.model._toggle_ignore(self.parent_mi, self.row)
      
    @ic_indent
    def undo(self):
      self.model._toggle_ignore(self.parent_mi, self.row)
  
  def __init__(self, db:DB, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.dbw = DBWrapper(db)
    self._nodes = dict() # type: dict[_ModelNode, _ModelNode]
    self._updating_children = set() # type: set[tuple[int, int]]

  def _is_updating(self, mi:QModelIndex):
    key = mi.internalPointer()
    if key is None :
      return False
    return (key.kind, key.id) in self._updating_children
    

  def _hold(self, *args):
    k = _ModelNode(*args)
    return self._nodes.setdefault(k, k)

  def _list_nodes(self):
    return sorted([ k.as_tuple() for k in self._nodes.keys() ])

  def hasChildren(self, parent:QModelIndex):
    return (parent == rootmi or parent.internalPointer().kind < self.Qrc)
  
  # def _invalidate(self, parentNode:_ModelNode, start):
  #   toInvalidate = [[], [], []]
  #   fn = self.dbw.im, self.dbw.qrc
  #   if parentNode is None :
  #     toInvalidate[0] = [ obj.id for obj in self.dbw.run()[start:] ]

  #   elif (k := parentNode.kind) == self.Qrc :
  #     return
  #   
  #   else :
  #     toInvalidate[k + 1] = [ obj.id for obj in fn[k](parentNode.id)[start:] ]

  #   for i in range(2) :
  #     l = toInvalidate[i]
  #     if l :
  #       for id in l :
  #         del self._nodes[(i, id)]
  #         toInvalidate[i + 1].extend(fn[i](id))
  #   for id in toInvalidate[-1] :
  #     del self._nodes[(2, id)]

  def _invalidate_qrcs(self, im_node:_ModelNode, ids):
    for id in ids :
      self._nodes.pop((self.Qrc, id, im_node.id, 0), None)

  def parent(self, mi: QModelIndex):
    if mi == rootmi :
      return QModelIndex()
    else :
      key = mi.internalPointer()
      if isinstance(key, dict) :
        breakpoint()
      if key.kind == 0 :
        return QModelIndex()
      return self.createIndex(key.parent.row, 0, key.parent) 

  def index(self, row, column, parent=QModelIndex()):
    with self.dbw.session() as S :
      if parent == rootmi :
        return self.createIndex(row, column, self._hold(self.Run, self.dbw.getRun(S, row).id, row, column, None))
      key = parent.internalPointer() # type: _ModelNode
      if key.kind == self.Run :
        return self.createIndex(row, column, self._hold(self.Im, self.dbw.getIm(S, key.id, row).id, row, column, key))
      if key.kind == self.Im :
        return self.createIndex(row, column, self._hold(self.Qrc, self.dbw.getQrc(S, key.id, row).id, row, column, key))
      return QModelIndex()

  def indexToPersistent(self, mi:QModelIndex):
    if mi == rootmi :
      return None
    key = mi.internalPointer() # type: _ModelNode
    return key.as_tuple()
  
  def persistentToIndex(self, p):
    if p is None :
      return rootmi
    key = self._nodes[p]
    return self.createIndex(key.row, 0, key)
  
  def rowCount(self, parent=QModelIndex()):
    if self._is_updating(parent) :
      return 0
    with self.dbw.session() as S :
      if parent == rootmi :
        return self.dbw.runCount(S)
      key = parent.internalPointer() # type: _ModelNode
      if key.kind == self.Run :
        return self.dbw.imCount(S, key.id)
      if key.kind == self.Im :
        return self.dbw.qrcCount(S, key.id)
    return 0

  def columnCount(self, parent=QModelIndex()):
    if parent == rootmi :
      return 1
    key = parent.internalPointer() # type: _ModelNode
    if key.kind == self.Run :
      return 3
    else :
      return 1
  
  def data(self, mi:QModelIndex, role=Qt.DisplayRole):
    with self.dbw.session() as S :
      if mi == rootmi :
        return None
      key = mi.internalPointer() # type: _ModelNode
      
      if key.kind == self.Run :
        if role == Qt.DisplayRole :
          ref = self.dbw.getRun(S, key.row)
          return f'{ref.id}: {ref.data}'
        elif role == self.DBRole :
          return self.dbw.getRun(S, key.row)
        return None
      
      if key.kind == self.Im :
        ref = self.dbw.getIm(S, key.parent.id, key.row)
        if role == Qt.DisplayRole :
          col = mi.column()
          if col == 0 :
            return f'{ref.image_name}'
          elif col == 1 :
            return f'{ref.target}'
          else :
            return f'{ref.target_id}'
        elif role == Qt.ForegroundRole :
          if ref.ignore :
            return QBrush(QColor(0xbb, 0xbb, 0xbb, 0xff))
          else :
            return None
        elif role == self.DBRole :
          return ref
        return None
      
      if key.kind == self.Qrc :
        ref = self.dbw.getQrc(S, key.parent.id, key.row)
        current= not self.dbw.isExtraQrc(S, key.parent.id, key.row)
        if role == Qt.DisplayRole :
          if ref.data is None :
            d = '<Not read>'
          else :
            d = ref.data
          if current :
            return f'{ref.id}: {d}'
          else :
            return f'(from im {ref.img_id}) {ref.id}: {d}'
        elif role == Qt.BackgroundRole :
          if current :
            return None
          else :
            return NON_EDITABLE_BRUSH
        elif role == Qt.EditRole :
          return ref.data
        elif role == self.DBRole :
          return ref
        elif role == self.PolygonRole :
          return [ [x, y] for x, y in ref.box ]
        return None
      return None
        

  def doSetData(self, mi:QModelIndex, val, role:int):
    if mi == rootmi :
      raise RuntimeError('Root item is not editable')
    key = mi.internalPointer() # type: _ModelNode
    if key.kind != self.Qrc:
      raise RuntimeError('Only QRC are editable')
    with self.dbw.session() as S :
      qrc = self.dbw.getQrc(S, key.parent.id, key.row)
      emit_roles = [role]
      if role == Qt.EditRole :
        qrc.data = val
      elif role == self.PolygonRole :
        qrc.box = val
        emit_roles.append(self.DBRole)
      else :
        return False
      self.dbw.commit(S, (qrc, ))
      S.commit()
      return True

  def removeRows(self, row:int, count:int, parent_mi:QModelIndex):
    if parent_mi == rootmi :
      return False
    key = parent_mi.internalPointer()
    if key.kind != self.Im :
      return False
    self.undoStack.push(self.RemQrcCmd(self, parent_mi, row, count))
    return True

  def flags(self, mi:QModelIndex):
    if mi == rootmi :
      return 0
    key = mi.internalPointer() # type: _ModelNode
    if key.kind != self.Qrc :
      return Qt.ItemIsSelectable | Qt.ItemIsEnabled
    else :
      with self.dbw.session() as S :
        if self.dbw.isExtraQrc(S, key.parent.id, key.row) :
          return Qt.NoItemFlags
        else :
          return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

  def _toggle_ignore(self, parent_mi:QModelIndex, row):
    with self.dbw.session() as S :
      self.dbw.toggle_ignore(S, parent_mi.internalPointer().id, row)
      mi = self.index(row, 0, parent_mi)
      self._dispatch(S, mi)
      S.commit()
    self.dataChanged.emit(mi, self.index(row, 2, parent_mi))

  def toggleIgnoreImage(self, mi:QModelIndex):
    self.undoStack.push(self.RemImCmd(self, mi.parent(), mi.row()))
  
  def _commit(self, parent_mi:QModelIndex, *args, count=None, **kwargs):
    if count is None :
      count = 1
    parent = parent_mi.internalPointer() if parent_mi != rootmi else None
    with self.dbw.session() as S :
      rv = self.dbw.commit(S, *args, **kwargs)
      if parent.kind != self.Im :
        raise RuntimeError('Only qrc are editable')
      self._dispatch(S, parent_mi)
      S.commit()
      for o in rv :
        S.refresh(o)
    return rv
    
  def _remove(self, parent_mi:QModelIndex, *args, count=None, **kwargs):
    if count is None :
      count = 1
    parent = parent_mi.internalPointer() if parent_mi != rootmi else None
    with self.dbw.session() as S :
      self.dbw.remove(S, *args, **kwargs)
      if parent.kind != self.Im :
        raise RuntimeError('Only qrc are editable')
      self._dispatch(S, parent_mi)
      S.commit()
  
  def _dispatch(self, S:sa.orm.Session, mi:QModelIndex):
    pmi = mi.parent()
    key = mi.internalPointer() # type: _ModelNode
    assert key.kind == self.Im
    with self.dbw.noCache() :
      im = self.dbw.getIm(S, key.parent.id, key.row)
    changed_ims, cur_changed = self.dbw.pre_dispatch(S, im)
    with self.dbw.noCache() :
      with self.dbw.session() as S2 :
        cache = { im.id: ind for ind, im in enumerate(self.dbw.im(S2, key.parent.id)) }
        remove_inds = [ (cache[cim_id], cim_id) for cim_id in changed_ims ]
        removes = [ (ind, [ q.id for q in self.dbw.qrc(S2, cim_id) ], cim_id) for ind, cim_id in remove_inds ]
    for ind, qrc_ids, cim_id in removes :
      cmi = mi.siblingAtRow(cache[cim_id])
      count = len(qrc_ids)
      if count :
        self.beginRemoveRows(cmi, 0, count - 1)
        self._updating_children.add((self.Im, cim_id))
        self._invalidate_qrcs(cmi.internalPointer(), qrc_ids)
        self.endRemoveRows()
      else :
        self._updating_children.add((self.Im, cim_id))
    S.commit()
    if cur_changed :
      self.dataChanged.emit(mi.siblingAtColumn(1), mi.siblingAtColumn(2))
    with self.dbw.noCache() :
      inserts = [ (ind, [ q.id for q in self.dbw.qrc(S, cim_id) ], cim_id) for ind, cim_id in remove_inds ]
    for ind, qrc_ids, cim_id in inserts :
      cmi = mi.siblingAtRow(cache[cim_id])
      count = len(qrc_ids)
      if count :
        self.beginInsertRows(cmi, 0, count - 1)
        self._updating_children.remove((self.Im, cim_id))
        self.endInsertRows()
      else :
        self._updating_children.remove((self.Im, cim_id))
      

