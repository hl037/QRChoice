
from PySide6.QtCore import Property
from PySide6.QtGui import QWheelEvent
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

  def setDragMode(self, *args, **kwargs):
    ori = self.viewport().cursor()
    super().setDragMode(*args, **kwargs)
    self.viewport().setCursor(ori)

  def mousePressEvent(self, *args, **kwargs):
    self._stored_cursor = self.viewport().cursor()
    super().mousePressEvent(*args, **kwargs)

  def mouseReleaseEvent(self, *args, **kwargs):
    super().mouseReleaseEvent(*args, **kwargs)
    self.viewport().setCursor(self._stored_cursor)
    

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
        


