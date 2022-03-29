
from PySide6.QtCore import Qt, Property, Slot, Signal, QPointF, QPoint
from PySide6.QtGui import QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QGraphicsView, QGraphicsItemGroup, QGraphicsRectItem

from icecream import ic

UNIT_PER_STEP = 120 # 15° = 120 * (1/8)

class ImageView(QGraphicsView):
  """
  Custom graphics view to allow zoom
  """
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.zoomStep_val = 1/8
    self.wheelIntegral = 0
    self._stored_cursor = None
    self._sendNoMove = True
    self._moving = False
    self._lastPos = None
    self._clickPos = None
    self._clickScenePos = None

  def setDragMode(self, *args, **kwargs):
    #ori = self.viewport().cursor()
    super().setDragMode(*args, **kwargs)
    #self.viewport().setCursor(ori)

  def mousePressEvent(self, ev:QMouseEvent):
    super().mousePressEvent(ev)
    
    if not ev.isAccepted() and ev.buttons() & Qt.LeftButton :
      self._stored_cursor = self.viewport().cursor()
      self.viewport().setCursor(Qt.ClosedHandCursor)
      self._sendNoMove = True
      self._moving = True
      self._lastPos = ev.position().toPoint()
      self._clickPos = ev.globalPos()
      self._clickScenePos = self.mapToScene(ev.pos())
    else :
      self._sendNoMove = False
      
  def mouseMoveEvent(self, ev:QMouseEvent):
    if self._moving and ev.buttons() & Qt.LeftButton :
      hBar = self.horizontalScrollBar()
      vBar = self.verticalScrollBar()
      p = ev.position().toPoint()
      delta = p - self._lastPos
      self._lastPos = p
      hBar.setValue(hBar.value() + (delta.x() if self.isRightToLeft() else -delta.x()));
      vBar.setValue(vBar.value() - delta.y());
    super().mouseMoveEvent(ev)
    if ev.buttons() :
      if self._sendNoMove :
        p = ev.globalPos() - self._clickPos
        if max(abs(p.x()), abs(p.y())) > 5 :
          self._sendNoMove = False

  def mouseReleaseEvent(self, *args, **kwargs):
    if self._stored_cursor :
      self.viewport().setCursor(self._stored_cursor)
    super().mouseReleaseEvent(*args, **kwargs)
    
    if self._sendNoMove :
      self.noMoveClick.emit(self._clickScenePos)
    else :
      self._sendNoMove = True
    self._clickPos = None
    self._stored_cursor = None
    self._moving = False
    self._lastPos = None
    self._clickPos = None
    self._clickScenePos = None

  noMoveClick = Signal(QPointF)

  @property
  def zoomStep(self):
    return self.zoomStep_val
  
  @zoomStep.setter
  def zoomStep(self, val):
    self.zoomStep_val = val

  def wheelEvent(self, ev:QWheelEvent):
    self.wheelIntegral += ev.angleDelta().y()
    q, r = divmod(self.wheelIntegral, UNIT_PER_STEP)
    if q != 0 :
      f = (1 + self.zoomStep) ** q
      self.wheelIntegral = r
      self.scale(f, f)
        


