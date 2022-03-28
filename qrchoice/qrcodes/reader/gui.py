import sys
from dataclasses import dataclass
from functools import cached_property, wraps
import sqlalchemy as sa
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsPolygonItem, QWidget, QUndoView
from PySide6.QtGui import QPixmap, QPolygonF, QUndoCommand, QUndoStack, QIcon
from PySide6.QtCore import Qt, QPointF, QAbstractItemModel, QModelIndex, Slot, Signal

from ...database import DB, _QRCDetectionRun as R, _QRCDetectionImg as I, _QRCDetectionQRC as C, getConverter

from .ui_qrcfixer import Ui_QRCFixer

from icecream import ic

base_prefix = 'ic> '
ic.prefix = base_prefix

ic_indent_level = 0

def ic_indent(f):
  @wraps(f)
  def _f(*args, **kwargs):
    global ic_indent_level
    old = ic.prefix
    ic(f.__name__)
    ic_indent_level += 1
    ic.prefix = '|  ' * ic_indent_level + ic.prefix
    try :
      return f(*args, **kwargs)
    finally :
      ic_indent_level -= 1
      ic.prefix = old
      print(ic.prefix[:-len(base_prefix)])
  return f
  #return _f


class DBWrapper(object):
  """
  A DB Wrapper to implement later smarter cache to avoid to much requests
  """
  stmt_run_sel = sa.select(R)
  stmt_im_sel = sa.select(I).where(I.run_id == sa.bindparam('run_id'))
  stmt_qrc_sel = sa.select(C).where(C.img_id == sa.bindparam('im_id'))
  
  def __init__(self, db:DB):
    self.db = db
    self.cur_run = None
    self.cur_im = None
    self._run = None
    self._im = None
    self._qrc = None

  def run(self):
    if self._run is None :
      with self.db.session() as S :
        self._run = S.scalars(self.stmt_run_sel).all()
    return self._run
    
  def im(self, run_id):
    if self.cur_run != run_id :
      self.cur_run = run_id
      with self.db.session() as S :
        self._im = S.scalars(self.stmt_im_sel, {'run_id': run_id}).all()
    return self._im

  def qrc(self, im_id):
    if self.cur_im != im_id :
      self.cur_im = im_id
      with self.db.session() as S :
        self._qrc = S.scalars(self.stmt_qrc_sel, {'im_id': im_id}).all()
    return self._qrc

  @ic_indent
  def runCount(self):
    return len(self.run())

  @ic_indent
  def imCount(self, run_id):
    return len(self.im(run_id))

  @ic_indent
  def qrcCount(self, im_id):
    return len(self.qrc(im_id))

  @ic_indent
  def getRun(self, ind):
    return self.run()[ind]

  @ic_indent
  def getIm(self, run_id, ind):
    return self.im(run_id)[ind]

  @ic_indent
  def getQrc(self, im_id, ind):
    return self.qrc(im_id)[ind]

  @ic_indent
  def commit(self, obj):
    with self.db.session() as S :
      S.merge(obj)
      S.commit()
  
rootmi = QModelIndex()

@dataclass(frozen=True, slots=True)
class _ModelNode(object):
  """
  Class to hold a node (so that it can be retrieve with the node dict only)
  """
  kind: int
  id: int
  row: int
  parent: '_ModelNode'

  def __hash__(self):
    return hash((self.kind, self.id))

  def __eq__(self, oth):
    if isinstance(oth, tuple) :
      kind, id, *_ = oth
      return self.kind == kind and self.id == id
    else :
      return self.kind == oth.kind and self.id == oth.id



class UndoStackModelMixin(object):
  """
  Mixin for handling an undo stack
  """
  class ModelEditCommand(QUndoCommand):
    def __init__(self, model:QAbstractItemModel, mi:QModelIndex, val, role:int):
      super().__init__()
      self.model = model
      self.mi = mi
      self.new_val = val
      self.role = role
      self.old_val = self.model.data(self.mi, self.role)
      self._success = False
        

    def redo(self):
      self._success = self.model.doSetData(self.mi, self.new_val, self.role)

    def undo(self):
      self.model.doSetData(self.mi, self.old_val, self.role)
      
  def __init__(self, stack:QUndoStack, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.undoStack = stack
    
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
  Polygon = Qt.UserRole + 1
  
  def __init__(self, db:DB, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.dbw = DBWrapper(db)
    self._nodes = dict() # type: dict[_ModelNode, _ModelNode]

  def _hold(self, *args):
    k = _ModelNode(*args)
    return self._nodes.setdefault(k, k)

  @ic_indent
  def hasChildren(self, parent:QModelIndex):
    return parent == rootmi or parent.internalPointer().kind < self.Qrc

  @ic_indent
  def parent(self, mi: QModelIndex):
    if mi == rootmi :
      return QModelIndex()
    else :
      key = mi.internalPointer()
      if key.kind == 0 :
        return QModelIndex()
      return self.createIndex(key.parent.row, 0, key.parent) 

  @ic_indent
  def index(self, row, column, parent=QModelIndex()):
    if parent == rootmi :
      return self.createIndex(row, column, self._hold(self.Run, self.dbw.getRun(row).id, row, None))
    key = parent.internalPointer() # type: _ModelNode
    if key.kind == self.Run :
      return self.createIndex(row, column, self._hold(self.Im, self.dbw.getIm(key.id, row).id, row, key))
    if key.kind == self.Im :
      return self.createIndex(row, column, self._hold(self.Qrc, self.dbw.getQrc(key.id, row).id, row, key))
    return QModelIndex()
  
  @ic_indent
  def rowCount(self, parent=QModelIndex()):
    if parent == rootmi :
      return self.dbw.runCount()
    key = parent.internalPointer() # type: _ModelNode
    if key.kind == self.Run :
      return self.dbw.imCount(key.id)
    if key.kind == self.Im :
      return self.dbw.qrcCount(key.id)
    return 0

  @ic_indent
  def columnCount(self, parent=QModelIndex()):
    return 1
  
  @ic_indent
  def data(self, mi:QModelIndex, role=Qt.DisplayRole):
    if mi == rootmi :
      return None
    key = mi.internalPointer() # type: _ModelNode
    
    if key.kind == self.Run :
      if role == Qt.DisplayRole :
        ref = self.dbw.getRun(key.row)
        return f'{ref.id}: {ref.data}'
      elif role == self.DBRole :
        return self.dbw.getRun(key.row)
      return None
    
    if key.kind == self.Im :
      if role == Qt.DisplayRole :
        ref = self.dbw.getIm(key.parent.id, key.row)
        return f'{ref.image}'
      elif role == self.DBRole :
        return self.dbw.getIm(key.parent.id, key.row)
      return None
    
    if key.kind == self.Qrc :
      if role == Qt.DisplayRole :
        ref = self.dbw.getQrc(key.parent.id, key.row)
        if ref.data is None :
          d = '<Not read>'
        else :
          d = ref.data
        return f'{ref.id}: {d}'
      elif role == Qt.EditRole :
        return self.dbw.getQrc(key.parent.id, key.row).data
      elif role == self.DBRole :
        return self.dbw.getQrc(key.parent.id, key.row)
      elif role == self.Polygon :
        return self.dbw.getQrc(key.parent.id, key.row).box
      return None
    
    return None



  @ic_indent
  def doSetData(self, mi:QModelIndex, val, role:int):
    if mi == rootmi :
      raise RuntimeError('Root item is not editable')
    key = mi.internalPointer() # type: _ModelNode
    if key.kind != self.Qrc:
      raise RuntimeError('Only QRC are editable')
    qrc = self.dbw.getQrc(key.parent.id, key.row)
    if role == Qt.EditRole :
      qrc.data = val
    elif role == self.Polygon :
      qrc.box = val
    else :
      return False
    self.dbw.commit(qrc)
    self.dataChanged.emit(mi, mi, [role])
    return True

  @ic_indent
  def flags(self, mi:QModelIndex):
    if mi == rootmi :
      return 0
    key = mi.internalPointer() # type: _ModelNode
    if key.kind != self.Qrc :
      return Qt.ItemIsEnabled | Qt.ItemIsEnabled
    else :
      return Qt.ItemIsEnabled | Qt.ItemIsEnabled | Qt.ItemIsEditable

class QRCFixer(QWidget):
  """
  
  """
  stmt_sel_qrc = sa.select(C).where(C.img_id == sa.bindparam('im_id'))
  def _qtinit(self):
    self.app = QApplication([])
    super().__init__()
    self.ui = Ui_QRCFixer()
    self.ui.setupUi(self)
    

  def __init__(self, db:DB):
    self._qtinit()
    self.db = db
    self.undoStack = QUndoStack()
    self.undoView = QUndoView(self.undoStack)
    self.tree_model = QRCTreeModel(db, self.undoStack)
    
    undo_act = self.undoStack.createUndoAction(self.ui.undo)
    undo_act.setIcon(QIcon.fromTheme(u"edit-undo"))
    self.ui.undo.setDefaultAction(undo_act)
    
    redo_act = self.undoStack.createRedoAction(self.ui.redo)
    redo_act.setIcon(QIcon.fromTheme(u"edit-redo"))
    self.ui.redo.setDefaultAction(redo_act)
    
    self.ui.runChooser.setModel(self.tree_model)
    if self.tree_model.rowCount(self.ui.runChooser.rootModelIndex()) :
      self.changeImListRoot(self.ui.runChooser.currentIndex())
      
    self.view.setScene(QGraphicsScene())
    self.item_im = QGraphicsPixmapItem() # type:QGraphicsPixmapItem
    self.scene.addItem(self.item_im)
    self.polys = [] # type: list[QGraphicsPolygonItem]

    self.ui.runChooser.currentIndexChanged.connect(self.changeImListRoot)
    self.ui.im_list.activated.connect(self.changeQrcListRoot)
    self.ui.im_list.activated.connect(self.loadIm)
    

  @Slot(int)
  def changeImListRoot(self, ind:int):
    self.ui.im_list.setModel(self.tree_model)
    new_index = self.tree_model.index(ind, 0, self.ui.runChooser.rootModelIndex())
    self.ui.im_list.setRootIndex(new_index)
    if not self.tree_model.rowCount(new_index):
      self.ui.qrc_list.setModel(None)

  @Slot(QModelIndex)
  def changeQrcListRoot(self, mi:QModelIndex):
    self.ui.qrc_list.setModel(self.tree_model)
    self.ui.qrc_list.setRootIndex(mi)

  @property
  def view(self):
    return self.ui.view

  @property
  def scene(self) -> QGraphicsScene:
    return self.view.scene()

  @Slot(QModelIndex)
  def loadIm(self, mi:QModelIndex):
    im = self.tree_model.data(mi, QRCTreeModel.DBRole)
    self.item_im.setPixmap(QPixmap(im.image))
    
    qrc_count = self.tree_model.rowCount(mi)
    indices = [ self.tree_model.index(row, 0, mi) for row in range(qrc_count) ]
    res = [ self.tree_model.data(index, QRCTreeModel.DBRole) for index in indices ]
    for p in self.polys :
      self.scene.removeItem(p)
    self.polys.clear()
    for qrc in res :
      self.polys.append(
        self.scene.addPolygon(
          QPolygonF([ QPointF(x, y) for x, y in qrc.box ])
        )
      )

  def exec(self):
    self.show()
    self.undoView.show()
    self.app.exec()
