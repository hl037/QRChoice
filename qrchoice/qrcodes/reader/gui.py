import sys
from dataclasses import dataclass
from functools import cached_property, wraps
import sqlalchemy as sa
from PySide6.QtWidgets import (
    QApplication, QWidget, QGraphicsView, QUndoView,
    QGraphicsScene, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPolygonItem,
    QGraphicsRectItem, QGraphicsItemGroup, QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
)
from PySide6.QtGui import (
    QPixmap, QPolygonF, QUndoCommand, QUndoStack, QIcon, QPainterPath
)
from PySide6.QtCore import (
    Qt,Slot, Signal, QObject,
    QPointF, QRectF, QPoint,
    QAbstractItemModel, QModelIndex, QItemSelectionModel,
)

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
  PolygonRole = Qt.UserRole + 1
  
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
      elif role == self.PolygonRole :
        return [ [x, y] for x, y in self.dbw.getQrc(key.parent.id, key.row).box ]
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
    emit_roles = [role]
    if role == Qt.EditRole :
      qrc.data = val
    elif role == self.PolygonRole :
      qrc.box = val
      emit_roles.append(self.DBRole)
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
      return Qt.ItemIsSelectable | Qt.ItemIsEnabled
    else :
      return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

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
      
    self.view.setScene(GraphicsScene(self))
    self.item_im = QGraphicsPixmapItem() # type:QGraphicsPixmapItem
    self.scene.addItem(self.item_im)
    
    self.qrc_selection = QItemSelectionModel(self.tree_model, self)
    self.qrcBoxes = QRCBoxes(self.tree_model, self.scene, self.qrc_selection)
    
    self.qrcBuilder = QRCBuilder(self.scene, self.undoStack)

    self.ui.view.noMoveClick.connect(self.noMoveClick)

    self.ui.runChooser.currentIndexChanged.connect(self.changeImListRoot)
    self.ui.im_list.activated.connect(self.qrcBoxes.setRootIndex)
    self.ui.im_list.activated.connect(self.changeQrcListRoot)
    self.ui.im_list.activated.connect(self.loadIm)

    self.ui.qrc_add.toggled.connect(self.qrcBuilder.setActive)
    self.qrcBuilder.activeChanged.connect(self.ui.qrc_add.setChecked)


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
    self.ui.qrc_list.setSelectionModel(self.qrc_selection)

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

  @Slot(QPointF)
  def noMoveClick(self, pos:QPointF):
    ic('NO MOVE CLICK')
    if self.qrcBuilder.isActive() :
      self.qrcBuilder.addPoint(pos)
    else :
      self.qrc_selection.clearCurrentIndex()
      self.qrc_selection.clearSelection()

  def exec(self):
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    self.show()
    self.undoView.show()
    self.app.exec()


class GraphicsScene(QGraphicsScene):
  pass

class HandlerManager(object):
  """
  Abstract class for an object that can manage Handles
  """

  def startMoveHandle(self, id:int, originalPos:QPointF):
    pass

  def updateHandlePosition(self, id:int, pos:QPointF):
    pass

  def commitHandlePosition(self, id:int):
    pass
    
    
class Handle(QGraphicsItemGroup):
  def __init__(self, manager:HandlerManager, id, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.manager = manager
    self.id = id
    self.rect = QGraphicsRectItem(QRectF(QPointF(-20,-20), QPointF(20,20))) # TODO: make it configurable
    self.addToGroup(self.rect)

  def mousePressEvent(self, ev:QGraphicsSceneMouseEvent):
    super().mousePressEvent(ev)
    self.manager.startMoveHandle(self.id, self.pos())
    ev.accept()

  def mouseMoveEvent(self, ev:QGraphicsSceneMouseEvent):
    super().mouseMoveEvent(ev)
    self.setPos(self.pos() + ev.scenePos() - ev.lastScenePos())
    self.manager.updateHandlePosition(self.id, self.pos())
    ev.accept()

  def mouseReleaseEvent(self, ev:QGraphicsSceneMouseEvent):
    super().mouseReleaseEvent(ev)
    self.manager.commitHandlePosition(self.id)
    ev.accept()

class QRCBoxes(object):
  """
  Class to manage the qrc boxes
  """

  class PolygonItem(QGraphicsPolygonItem):
    """
    Class to manage the polygon (select it when clicked)
    """
    def __init__(self, qrcBoxes:'QRCBoxes', mi:QModelIndex, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.qrcBoxes = qrcBoxes
      self.mi = mi
      
    def mousePressEvent(self, ev:QGraphicsSceneMouseEvent):
      super().mousePressEvent(ev)
      self.qrcBoxes.selection.select(self.mi, QItemSelectionModel.ClearAndSelect)
      self.qrcBoxes.selection.setCurrentIndex(self.mi, QItemSelectionModel.SelectCurrent)
      ev.accept()


  def __init__(self, tree_model: QRCTreeModel, scene:QGraphicsScene, selection:QItemSelectionModel):
    self.tree_model = tree_model
    self.scene = scene
    self.selection = selection
    self.selection.currentChanged.connect(self.changeCurrent)
    self.tree_model.dataChanged.connect(self.changeData)
    self.polys = [] #type: list[QGraphicsPolygonItem]
    self.boxes = [] #type: list[list[int]]
    self.current = rootmi # type: QModelIndex
    self.parent_mi = None
    self.handles = []

  @property
  def cur_box(self):
    return self.boxes[self.current.row()]

  @Slot(QModelIndex, QModelIndex)
  def changeCurrent(self, mi:QModelIndex, prev:QModelIndex):
    if self.current == mi :
      return
    self.current = mi
    
    #clear previous
    #TODO: change poly brush
    for h in self.handles :
      self.scene.removeItem(h)
    self.handles.clear() #Free instances
    
    #invalid mi -> don't select anything else
    if not mi.isValid() or mi.parent() != self.parent_mi :
      return
    
    #Else -> create handles
    box = self.cur_box
    for i, (x, y) in enumerate(box) :
      h = Handle(self, i)
      self.handles.append(h) # Here is where we incref
      h.setPos(x, y)
      self.scene.addItem(h)
    #TODO: change poly brush

  def updateHandlePosition(self, ind:int, pos:QPointF):
    box = self.cur_box
    box[ind][:] = pos.x(), pos.y()
    self.polys[self.current.row()].setPolygon(self.makePoly(box))

  def commitHandlePosition(self):
    self.tree_model.setData(self.current, [ [x, y] for x, y in self.cur_box ], QRCTreeModel.PolygonRole)
    

  def makePoly(self, box:list[list[int]]):
    return QPolygonF([ QPointF(x, y) for x, y in box ])

  @Slot(QModelIndex, QModelIndex, 'QList<int>')
  def changeData(self, topleft:QModelIndex, botright:QModelIndex, roles:list[int]) :
    if topleft.parent() != self.parent_mi :
      return

    if QRCTreeModel.PolygonRole in roles :
      b = topleft.row()
      e = botright.row() + 1
      indices = [ self.tree_model.index(row, 0, self.parent_mi) for row in range(b, e) ]
      self.boxes[b:e] = [ self.tree_model.data(index, QRCTreeModel.PolygonRole) for index in indices ]
      for poly, box in zip(self.polys[b:e], self.boxes[b:e]) :
        poly.setPolygon(self.makePoly(box))
      #handles
      if self.current.isValid() and b <= self.current.row() <= e:
        for h, (x, y) in zip(self.handles, self.boxes[self.current.row()]) :
          h.setPos(x, y)
        

  @Slot(QModelIndex)
  def setRootIndex(self, mi:QModelIndex):
    if mi == self.parent_mi :
      return
    self.parent_mi = mi
    self.changeCurrent(rootmi, self.current)
    qrc_count = self.tree_model.rowCount(mi)
    indices = [ self.tree_model.index(row, 0, mi) for row in range(qrc_count) ]
    for p in self.polys :
      self.scene.removeItem(p)
    self.polys = [ self.PolygonItem(self, mi) for mi in indices ]
    for p in self.polys :
      self.scene.addItem(p)
    self.changeData(indices[0], indices[-1], [QRCTreeModel.PolygonRole])


class QRCBuilder(HandlerManager, QObject):
  """
  Class to build a QRCode
  """
  
  class AddHandleCmd(QUndoCommand):
    """
    Command to add an handle to the QRC polygon
    """
    def __init__(self, builder:'QRCBuilder', pos:QPointF):
      super().__init__()
      self.builder = builder
      self.pos = pos

    def redo(self):
      h = Handle(self.builder, len(self.builder.handles))
      h.setPos(self.pos)
      self.builder.handles.append(h)
      self.builder.scene.addItem(h)
      self.builder._updatePath()


    def undo(self):
      self.builder.scene.removeItem(self.builder.handles[-1])
      del self.builder.handles[-1]
      self.builder._updatePath()
  
  class ClearCmd(QUndoCommand):
    """
    Command to clear the CodeBuilder (after a commit or a focus loss)
    """
    def __init__(self, builder:'QRCBuilder'):
      super().__init__()
      self.builder = builder
      self.positions = [ h.pos() for h in self.builder.handles ]

    def redo(self):
      for h in self.builder.handles :
        self.builder.scene.removeItem(h)
      self.builder.handles.clear()
      self.builder._updatePath()
      self.builder._active = False
      self.builder.activeChanged.emit(False)

    def undo(self):
      self.builder.handles[:] = [ Handle(self.builder, i) for i in range(len(self.positions)) ]
      for h, pos in zip(self.builder.handles, self.positions) :
        h.setPos(pos)
        self.builder.scene.addItem(h)
      self.builder._updatePath()
      self.builder._active = True
      self.builder.activeChanged.emit(True)

  class CommitCmd(QUndoCommand):
    """
    Command to perform the commit...
    """
    def __init__(self, builder:'QRCBuilder', pos:QPointF):
      super().__init__()
      self.builder = builder
      self.pos = pos
      self.clear = QRCBuilder.ClearCmd(builder)

    def redo(self):
      self.clear.redo()
      #TODO: Actually commit
      ic('COMMIT')

    def undo(self):
      #TODO: Decommit
      ic('DECOMMIT')
      self.clear.undo()

  class MoveHandleCmd(QUndoCommand):
    """
    Command to undo/redo a handle move
    """
    def __init__(self, builder:'QRCBuilder', ind:int, src:QPointF):
      super().__init__()
      self.builder = builder
      self.ind = ind
      self.src = src
      self.dst = None

    def redo(self):
      self.builder.handles[self.ind].setPos(self.dst)
      self.builder._updatePath()

    def undo(self):
      self.builder.handles[self.ind].setPos(self.src)
      self.builder._updatePath()

  class SetActiveCmd(QUndoCommand):
    """
    Command to start component activity
    """
    def __init__(self, builder:'QRCBuilder'):
      super().__init__()
      self.builder = builder

    def redo(self):
      self.builder._active = True
      self.builder.activeChanged.emit(True)

    def undo(self):
      self.builder._active = False
      self.builder.activeChanged.emit(False)

  def __init__(self, scene:QGraphicsScene, undoStack:QUndoStack):
    super().__init__()
    self.scene = scene
    self.undoStack = undoStack
    self.handles = [] # type: list[Handle]
    self.path = QGraphicsPathItem()
    self._move_cmd = None
    self._active = False

  activeChanged = Signal(bool)

  @Slot(QPointF)
  def addPoint(self, p:QPointF):
    if len(self.handles) + 1 < 4 :
      self.undoStack.push(self.AddHandleCmd(self, p))
    else :
      self.undoStack.push(self.CommitCmd(self, p))

  @Slot(bool)
  def setActive(self, active):
    ic()
    ic(self._active, active)
    if self._active == active :
      return
    if self._active :
      self.undoStack.push(self.ClearCmd(self))
    else :
      self.undoStack.push(self.SetActiveCmd(self))

  def startMoveHandle(self, ind:int, pos:QPointF):
    assert self._move_cmd is None
    self._move_cmd = self.MoveHandleCmd(self, ind, pos)
    
  def updateHandlePosition(self, id:int, pos:QPointF):
    self._updatePath()

  def commitHandlePosition(self, ind):
    assert self._move_cmd is not None
    self._move_cmd.dst = self.handles[ind].pos()
    self.undoStack.push(self._move_cmd)
    self._move_cmd = None

  def isActive(self):
    return self._active


  def _updatePath(self):
    if len(self.handles) > 1 :
      pp = QPainterPath(self.handles[0].pos())
      for h in self.handles :
        pp.lineTo(h.pos())
      self.path.setPath(pp)
      if self.path.scene() != self.scene :
        self.scene.addItem(self.path)
    else :
      if self.path.scene() == self.scene :
        self.scene.removeItem(self.path)


  

