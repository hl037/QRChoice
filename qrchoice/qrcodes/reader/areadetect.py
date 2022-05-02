from functools import reduce
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QWidget, QGraphicsView, QUndoView, QPushButton,
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
    QAbstractItemModel, QModelIndex, QItemSelectionModel, QAbstractListModel
)

from PIL import Image
from PIL.ImageQt import ImageQt
import pillowOkularViewer

from . import zbarReader
from ...im_enhancer import imfilters, ImFilter, FilterQueue

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


class ImFilterObject(object):
  """
  Wrapper around ImFilter
  """
  def __init__(self, target:ImFilter):
    self.target = target
    addHandler = None # type:  AddFilterHandler

  @Slot()
  def add(self):
    if self.addHandler is not None :
      self.addHandler.addFilter(self.target)

imfilterObjects = [ ImFilterObject(f) for f in imfilters ]


class AddFilterHandler(object):
  def addFilter(self, f):
    raise NotImplementedError()

class QRCDetectWidget(AddFilterHandler, QWidget):
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
    self._filtered = None
    self.filtersModel = FiltersModel()

    self.ui.detect.clicked.connect(self.detect)
    self.ui.apply.clicked.connect(self.apply)
    self.ui.copyArgs.clicked.connect(self.copyFilterArgs)
    
    self.ui.filterView.setModel(self.filtersModel)
    self.ui.remFilter.clicked.connect(self.removeFilter)
    self.ui.clearFilters.clicked.connect(self.filtersModel.reset)
    self.filtersModel.rowsInserted.connect(self.filter)
    self.filtersModel.rowsRemoved.connect(self.filter)
    self.filtersModel.modelReset.connect(self.filter)
    
    self.filterButtons = []

    for f in imfilterObjects :
      pb = QPushButton()
      pb.setText(f.target.name)
      self.ui.filterButtons.addWidget(pb)
      f.addHandler = self
      pb.clicked.connect(f.add)


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
    self.filter()

  @Slot()
  def filter(self):
    args = ' '.join(f.short_name for f in self.filtersModel.filterList)
    self.ui.filterArgs.setText(f'qrchoice im-enhance -f "{args}"')
    self._filtered = FilterQueue.reduce(self.filtersModel.filterList, self._base_extracted)
    res = self.pixmap.convertFromImage(ImageQt(self._filtered))
    self.ui.imViewer.setPixmap(self.pixmap)

  @Slot()
  def copyFilterArgs(self):
    QApplication.clipboard().setText(self.ui.filterArgs.text())

  dataApplied = Signal(str)

  @Slot()
  def detect(self):
    res = zbarReader.readQRCodes(self._filtered)
    self.ui.info.setText(f'Résultat :\n{repr(res)}')
    if res :
      self.data = res[0][0]
    else :
      self.data = ''

  @Slot()
  def apply(self):
    self.dataApplied.emit(self.data)

  def addFilter(self, f):
    row = self.currentRow()
    self.filtersModel.addFilter(f, row)

  @Slot()
  def removeFilter(self):
    row = self.currentRow()
    self.filtersModel.removeFilter(row)

  def currentRow(self):
    mi = self.ui.filterView.currentIndex()
    if mi != rootmi :
      return mi.row()
    return None
      
    

    

rootmi = QModelIndex()



    

class FiltersModel(QAbstractListModel):
  """
  Model of image filters
  """
  def __init__(self):
    super().__init__()
    self.filterList = [] # type: list[ImFilter]

  def rowCount(self, mi:QModelIndex):
    if not mi.isValid() :
      return len(self.filterList)
    return 0

  def data(self, mi:QModelIndex, role:int):
    if role == Qt.DisplayRole :
      return self.filterList[mi.row()].name

  @Slot()
  def reset(self):
    self.beginResetModel()
    self.filterList.clear()
    self.endResetModel()

  def addFilter(self, filter, pos = None):
    if pos is None :
      pos = len(self.filterList)
    ic(pos)
    self.beginInsertRows(rootmi, pos, pos)
    self.filterList.insert(pos, filter)
    self.endInsertRows()

  def removeFilter(self, pos=None):
    if pos is None :
      pos = len(self.filterList) - 1
    ic(pos)
    self.beginRemoveRows(rootmi, pos, pos)
    del self.filterList[pos]
    self.endRemoveRows()



