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
    QPixmap, QPolygonF, QUndoCommand, QUndoStack, QIcon, QPainterPath, QBrush, QColor
)
from PySide6.QtCore import (
    Qt,Slot, Signal, QObject,
    QPointF, QRectF, QPoint,
    QAbstractItemModel, QModelIndex, QPersistentModelIndex, QItemSelectionModel,
)

from .areadetect import QRCDetectWidget
from .qrc_tree_model import *

from .ui_qrcfixer import Ui_QRCFixer

from ...debug_utils import *




class QRCFixer(QWidget):
  """
  
  """
  
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
    self.view.setScene(GraphicsScene(self))
    
    undo_act = self.undoStack.createUndoAction(self.ui.undo)
    undo_act.setIcon(QIcon.fromTheme(u"edit-undo"))
    self.ui.undo.setDefaultAction(undo_act)
    
    redo_act = self.undoStack.createRedoAction(self.ui.redo)
    redo_act.setIcon(QIcon.fromTheme(u"edit-redo"))
    self.ui.redo.setDefaultAction(redo_act)
    
    self.im_selection = QItemSelectionModel(self.tree_model, self)
    
    self.qrc_selection = QItemSelectionModel(self.tree_model, self)
    self.qrcBoxes = QRCBoxes(self.tree_model, self.scene, self.qrc_selection)
    
    self.ui.runChooser.setModel(self.tree_model)
    if self.tree_model.rowCount(self.ui.runChooser.rootModelIndex()) :
      self.changeImListRoot(self.ui.runChooser.currentIndex())
      
    self.item_im = QGraphicsPixmapItem() # type:QGraphicsPixmapItem
    self.scene.addItem(self.item_im)
    
    self.qrcBuilder = QRCBuilder(self.scene, self.undoStack, self.tree_model)

    self.detectWidget = QRCDetectWidget()

    self.ui.view.noMoveClick.connect(self.noMoveClick)

    self.ui.runChooser.currentIndexChanged.connect(self.changeImListRoot)
    self.ui.im_list.activated.connect(self._imActivated)
    self.imActivated.connect(self.qrcBoxes.setRootIndex)
    self.imActivated.connect(self.changeQrcListRoot)
    self.imActivated.connect(self.loadIm)
    self.imActivated.connect(self.cleanQrcBuilder)
    self.imActivated.connect(self.handleAddQrcState)

    self.ui.qrc_add.toggled.connect(self.setQrcBuilderActive)
    self.qrcBuilder.activated.connect(self.onQrcBuilderActivated)
    self.qrcBuilder.deactivated.connect(self.onQrcBuilderDeactivated)
    self.qrc_selection.currentChanged.connect(self.onCurrentQrcChanged)
    self.qrc_selection.currentChanged.connect(self.handleDelQrcState)

    self.ui.qrc_detect.toggled.connect(self.detectWidget.setVisible)
    self.tree_model.dataChanged.connect(self.changeDetectBox)

    self.ui.qrc_del.clicked.connect(self.removeQrc)

    self.detectWidget.dataApplied.connect(self.onDataApplied)
    
    self.ui.im_remove.clicked.connect(self.toggleImIgnore)

  imActivated = Signal(QModelIndex)
  
  @Slot()
  def toggleImIgnore(self):
    mi = self.im_selection.currentIndex()
    self.tree_model.toggleIgnoreImage(mi)

  @Slot()
  def _imActivated(self, mi:QModelIndex):
    target = mi.siblingAtColumn(0)
    self.imActivated.emit(target)

  @Slot()
  def removeQrc(self):
    index = self.qrc_selection.currentIndex()
    self.tree_model.removeRow(index.row(), index.parent()) 

  @Slot(QModelIndex)
  def handleDelQrcState(self, mi:QModelIndex):
    self.ui.qrc_del.setEnabled(mi != rootmi)
    
  @Slot(QModelIndex)
  def handleAddQrcState(self, mi:QModelIndex):
    self.ui.qrc_add.setEnabled(mi != rootmi)
      

  @Slot(bool)
  def setQrcBuilderActive(self, active):
    if active :
      self.qrcBuilder.activate(self.ui.qrc_list.rootIndex())
    else :
      self.qrcBuilder.deactivate()

  @Slot(QModelIndex)
  def onQrcBuilderActivated(self, parent_mi:QModelIndex):
    self.im_selection.select(parent_mi, QItemSelectionModel.ClearAndSelect)
    self.im_selection.setCurrentIndex(parent_mi, QItemSelectionModel.SelectCurrent)
    self.imActivated.emit(parent_mi)
    self.qrc_selection.clear()
    self.ui.qrc_add.setChecked(True)

  @Slot()
  def onQrcBuilderDeactivated(self):
    self.ui.qrc_add.setChecked(False)

  @Slot(int)
  def changeImListRoot(self, ind:int):
    self.ui.im_list.setModel(self.tree_model)
    self.ui.im_list.setSelectionModel(self.im_selection)
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
    self.detectWidget.setIm(im.image)

  @Slot(QModelIndex)
  def cleanQrcBuilder(self, mi:QModelIndex):
    if mi != self.qrcBuilder.parent_mi :
      self.qrcBuilder.deactivate()

  @Slot(QModelIndex)
  def onCurrentQrcChanged(self, mi:QModelIndex):
    if mi != rootmi :
      self.qrcBuilder.deactivate()
      box = self.tree_model.data(mi, QRCTreeModel.PolygonRole)
      self.detectWidget.setBox(box)
    else :
      self.detectWidget.setBox(None)
      
  @Slot(QModelIndex, QModelIndex, 'QList<int>')
  @ic_indent
  def changeDetectBox(self, topleft:QModelIndex, botright:QModelIndex, roles:list[int]) :
    if len(roles) != 0 and QRCTreeModel.PolygonRole not in roles :
      return
    current_qrc_mi = self.qrc_selection.currentIndex()
    if current_qrc_mi == rootmi :
      return
    
    current_im_mi = self.im_selection.currentIndex().siblingAtColumn(0)
    if topleft.parent() != current_im_mi :
      return

    if not (topleft.row() <= current_qrc_mi.row() <= botright.row()) :
      return
    box = self.tree_model.data(current_qrc_mi, QRCTreeModel.PolygonRole)
    self.detectWidget.setBox(box)

  

  @Slot(QPointF)
  def noMoveClick(self, pos:QPointF):
    if self.qrcBuilder.isActive() :
      self.qrcBuilder.addPoint(pos)
    else :
      self.qrc_selection.clearCurrentIndex()
      self.qrc_selection.clearSelection()

  @Slot(str)
  def onDataApplied(self, s:str):
    mi = self.qrc_selection.currentIndex()
    if mi != rootmi :
      self.tree_model.setData(mi, s, Qt.EditRole)

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

class QRCBoxes(HandlerManager):
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
      self.editable = mi.flags() & Qt.ItemIsEditable
      if self.editable :
        self.setBrush(QBrush(QColor(0x00, 0x88, 0xff, 0x55)))
      else :
        self.setBrush(NON_EDITABLE_BRUSH)
      
    def mousePressEvent(self, ev:QGraphicsSceneMouseEvent):
      super().mousePressEvent(ev)
      if not self.editable :
        return
      self.qrcBoxes.selection.select(self.mi, QItemSelectionModel.ClearAndSelect)
      self.qrcBoxes.selection.setCurrentIndex(self.mi, QItemSelectionModel.SelectCurrent)
      ev.accept()


  def __init__(self, tree_model: QRCTreeModel, scene:QGraphicsScene, selection:QItemSelectionModel):
    self.tree_model = tree_model
    self.scene = scene
    self.selection = selection
    self.selection.currentChanged.connect(self.changeCurrent)
    self.tree_model.dataChanged.connect(self.changeData)
    self.tree_model.rowsInserted.connect(self.onRowsInserted)
    self.tree_model.rowsRemoved.connect(self.onRowsRemoved)
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

  def commitHandlePosition(self, ind:int):
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
  def setRootIndex(self, parent_mi:QModelIndex):
    if parent_mi == self.parent_mi :
      return
    self.parent_mi = parent_mi
    self.changeCurrent(rootmi, self.current)
    for p in self.polys :
      self.scene.removeItem(p)
    qrc_count = self.tree_model.rowCount(parent_mi)
    if qrc_count == 0 :
      self.boxes = []
      self.polys = []
    else :
      indices = [ self.tree_model.index(row, 0, parent_mi) for row in range(qrc_count) ]
      self.polys = [ self.PolygonItem(self, mi) for mi in indices ]
      for p in self.polys :
        self.scene.addItem(p)
      self.changeData(indices[0], indices[-1], [QRCTreeModel.PolygonRole])
    ic('setRoot', self.parent_mi.internalPointer(), len(self.polys))

  @Slot(QModelIndex, int, int)
  @ic_indent
  def onRowsInserted(self, parent_mi:QModelIndex, first, last):
    if parent_mi != self.parent_mi :
      return
    last += 1
    ic('PreRowsInserted', first, last, len(self.polys))
    if self.current != rootmi and self.current.row() >= first:
      self.current = self.tree_model.index(self.current.row() + last - first, 0, parent_mi)
    indices = [ self.tree_model.index(row, 0, parent_mi) for row in range(first, len(self.polys) + last - first) ]
    n_polys = [ self.PolygonItem(self, mi) for mi in indices[:last - first] ]
    self.polys[first:first] = n_polys
    self.boxes[first:first] = [None] * len(n_polys)
    for p in n_polys :
      self.scene.addItem(p)
    for i, p in enumerate(self.polys[last:], start=last) :
      p.mi = self.tree_model.index(i, 0, parent_mi)
    self.changeData(indices[0], indices[-1], [QRCTreeModel.PolygonRole])
    ic('PostRowsInserted', len(self.polys))
  
  
  @Slot(QModelIndex, int, int)
  @ic_indent
  def onRowsRemoved(self, parent_mi:QModelIndex, first, last):
    if parent_mi != self.parent_mi :
      return
    last += 1
    for p in self.polys[first:last] :
      self.scene.removeItem(p)
    del self.polys[first:last]
    del self.boxes[first:last]
    for i, p in enumerate(self.polys[first:], start=first) :
      p.mi = self.tree_model.index(i, 0, parent_mi)
    ic('RowsRemoved', first, last, len(self.polys))
    self.current = rootmi
    # current is updated by the list view...
    # breakpoint() 
    # if self.current != rootmi :
    #   if self.current.row() >= last :
    #     self.current = self.tree_model.index(self.current.row() - last + first, 0, parent_mi)
    #   elif self.current.row() >= first :
    #     self.changeCurrent(QModelIndex(), self.current)








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
      self.setText('Add Handle')

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
      self.parent_mi = self.builder.parent_mi
      self.positions = [ QPointF(h.pos()) for h in self.builder.handles ]
      self.setText('Clear Handles')

    def redo(self):
      for h in self.builder.handles :
        self.builder.scene.removeItem(h)
      self.builder.handles.clear()
      self.builder._updatePath()
      self.builder._active = False
      self.builder.parent_mi = None
      self.builder.deactivated.emit()

    def undo(self):
      self.builder.handles[:] = [ Handle(self.builder, i) for i in range(len(self.positions)) ]
      for h, pos in zip(self.builder.handles, self.positions) :
         h.setPos(pos)
         self.builder.scene.addItem(h)
      self.builder._updatePath()
      self.builder._active = True
      self.builder.parent_mi = self.parent_mi
      self.builder.activated.emit(self.parent_mi)

  class CommitCmd(QUndoCommand):
    """
    Command to perform the commit...
    """
    def __init__(self, builder:'QRCBuilder', pos:QPointF):
      super().__init__()
      self.builder = builder
      self.clear = QRCBuilder.ClearCmd(builder)
      box = [ [ (_pos:=h.pos()).x(), _pos.y()] for h in self.builder.handles ]
      box.append([pos.x(), pos.y()])
      self.commit_cmd = self.builder.model.AddQrcCmd(self.builder.model, self.builder.parent_mi, box)
      self.setText('Commit qrc')
      

    def redo(self):
      self.clear.redo()
      self.commit_cmd.redo()

    def undo(self):
      self.commit_cmd.undo()
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
      self.setText('Move handle')

    def redo(self):
      self.builder.handles[self.ind].setPos(self.dst)
      self.builder._updatePath()

    def undo(self):
      self.builder.handles[self.ind].setPos(self.src)
      self.builder._updatePath()

  class ActivateCmd(QUndoCommand):
    """
    Command to start component activity
    """
    def __init__(self, builder:'QRCBuilder', parent_mi:QModelIndex):
      super().__init__()
      self.builder = builder
      self.parent_mi = parent_mi
      self.setText('StartAdd qrc')

    def redo(self):
      self.builder._active = True
      self.builder.parent_mi = self.parent_mi
      self.builder.activated.emit(self.parent_mi)

    def undo(self):
      self.builder._active = False
      self.builder.deactivated.emit()
      
  def __init__(self, scene:QGraphicsScene, undoStack:QUndoStack, model:QRCTreeModel):
    super().__init__()
    self.scene = scene
    self.undoStack = undoStack
    self.model = model
    self.handles = [] # type: list[Handle]
    self.path = QGraphicsPathItem()
    self.parent_mi = None
    self._move_cmd = None
    self._active = False

  activated = Signal(QModelIndex)
  deactivated = Signal()

  @Slot(QPointF)
  def addPoint(self, p:QPointF):
    if len(self.handles) + 1 < 4 :
      self.undoStack.push(self.AddHandleCmd(self, p))
    else :
      self.undoStack.push(self.CommitCmd(self, p))

  def activate(self, parent_mi:QModelIndex):
    if self._active and self.parent_mi == parent_mi :
      return
    if not self._active :
      self.undoStack.push(self.ActivateCmd(self, parent_mi))
    else :
      assert False
    
  def deactivate(self):
    if not self._active :
      return
    self.undoStack.push(self.ClearCmd(self))

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


