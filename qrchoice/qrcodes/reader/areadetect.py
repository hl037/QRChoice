import numpy as np

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

import PIL
from PIL import Image
from PIL.ImageQt import ImageQt
import pillowOkularViewer

from . import zbarReader

from .ui_qrcdetectwidget import Ui_QRCDetectWidget


from icecream import ic


def shoelace(points:np.ndarray):
  I=np.arange(points.shape[0])
  X=points[...,0] 
  X = X - np.mean(X)
  Y=points[...,1] 
  Y = Y - np.mean(Y)
  return np.abs(np.sum(X[I-1] * Y[I] - X[I] * Y[I-1]) * 0.5)


def makeCClockwise(points:np.ndarray):
  if shoelace(points) < 0 :
    points = np.flip(points, 0)
  return points



def extractArea(im:Image, points:np.ndarray):
  points = makeCClockwise(points)
  I=np.arange(points.shape[0])
  X=points[...,0] 
  X = X - np.mean(X)
  Y=points[...,1] 
  Y = Y - np.mean(Y)
  DX = X[I] - X[I-1]
  DY = Y[I] - Y[I-1]
  D = np.sqrt(X*X + Y*Y)
  ml = int(np.max(D) * 2)
  return im.transform((ml, ml), Image.QUAD, points.ravel())



class QRCDetectWidget(QWidget):
  """
  
  """
  
  def _qtinit(self):
    super().__init__()
    self.ui = Ui_QRCDetectWidget()
    self.ui.setupUi(self)
    

  def __init__(self):
    self._qtinit()
    self._im = None
    self._box = None
    self.pixmap = QPixmap()

  def setIm(self, path:str):
    self._im = Image.open(path)
    self._update()

  def setBox(self, box:list[list[int]]):
    if box :
      self._box = np.array(box)
    else :
      self._box = None
    self._update()

  def _update(self):
    if self._im is None or self._box is None :
      self._base_extracted = None
      self.pixmap.swap(QPixmap())
      self.ui.imViewer.setPixmap(self.pixmap)
      self.ui.info.setText('')
      return
    self.ui.info.setText('')
    self._base_extracted = extractArea(self._im, self._box)
    res = self.pixmap.convertFromImage(ImageQt(self._base_extracted))
    self.ui.imViewer.setPixmap(self.pixmap)

    



