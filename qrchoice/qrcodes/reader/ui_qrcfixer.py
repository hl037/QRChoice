# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_qrcfixer.ui'
##
## Created by: Qt User Interface Compiler version 6.3.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGraphicsView,
    QHBoxLayout, QHeaderView, QListView, QSizePolicy,
    QSplitter, QToolButton, QTreeView, QVBoxLayout,
    QWidget)

from .custom import ImageView

class Ui_QRCFixer(object):
    def setupUi(self, QRCFixer):
        if not QRCFixer.objectName():
            QRCFixer.setObjectName(u"QRCFixer")
        QRCFixer.resize(1200, 800)
        icon = QIcon()
        iconThemeName = u"applications-development"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        QRCFixer.setWindowIcon(icon)
        self.horizontalLayout_3 = QHBoxLayout(QRCFixer)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.view = ImageView(QRCFixer)
        self.view.setObjectName(u"view")
        self.view.viewport().setProperty("cursor", QCursor(Qt.CrossCursor))
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setProperty("zoomStep", 0.125000000000000)

        self.horizontalLayout.addWidget(self.view)


        self.horizontalLayout_3.addLayout(self.horizontalLayout)

        self.splitter = QSplitter(QRCFixer)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.runChooser = QComboBox(self.verticalLayoutWidget)
        self.runChooser.setObjectName(u"runChooser")

        self.verticalLayout.addWidget(self.runChooser)

        self.im_list = QTreeView(self.verticalLayoutWidget)
        self.im_list.setObjectName(u"im_list")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.im_list.sizePolicy().hasHeightForWidth())
        self.im_list.setSizePolicy(sizePolicy)
        self.im_list.setEditTriggers(QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed)
        self.im_list.setRootIsDecorated(False)
        self.im_list.setItemsExpandable(False)
        self.im_list.setHeaderHidden(False)
        self.im_list.setExpandsOnDoubleClick(False)
        self.im_list.header().setVisible(True)
        self.im_list.header().setStretchLastSection(False)

        self.verticalLayout.addWidget(self.im_list)

        self.splitter.addWidget(self.verticalLayoutWidget)
        self.verticalLayoutWidget_2 = QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayout_2 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.qrc_list = QListView(self.verticalLayoutWidget_2)
        self.qrc_list.setObjectName(u"qrc_list")

        self.verticalLayout_2.addWidget(self.qrc_list)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.im_remove = QToolButton(self.verticalLayoutWidget_2)
        self.im_remove.setObjectName(u"im_remove")
        icon1 = QIcon(QIcon.fromTheme(u"trash-empty"))
        self.im_remove.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.im_remove)

        self.qrc_add = QToolButton(self.verticalLayoutWidget_2)
        self.qrc_add.setObjectName(u"qrc_add")
        self.qrc_add.setEnabled(False)
        icon2 = QIcon()
        iconThemeName = u"list-add"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.qrc_add.setIcon(icon2)
        self.qrc_add.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.qrc_add)

        self.qrc_del = QToolButton(self.verticalLayoutWidget_2)
        self.qrc_del.setObjectName(u"qrc_del")
        self.qrc_del.setEnabled(False)
        icon3 = QIcon()
        iconThemeName = u"list-remove"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.qrc_del.setIcon(icon3)

        self.horizontalLayout_2.addWidget(self.qrc_del)

        self.qrc_detect = QToolButton(self.verticalLayoutWidget_2)
        self.qrc_detect.setObjectName(u"qrc_detect")
        icon4 = QIcon()
        iconThemeName = u"zoom-next"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.qrc_detect.setIcon(icon4)
        self.qrc_detect.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.qrc_detect)

        self.undo = QToolButton(self.verticalLayoutWidget_2)
        self.undo.setObjectName(u"undo")
        icon5 = QIcon()
        iconThemeName = u"edit-undo"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.undo.setIcon(icon5)

        self.horizontalLayout_2.addWidget(self.undo)

        self.redo = QToolButton(self.verticalLayoutWidget_2)
        self.redo.setObjectName(u"redo")
        icon6 = QIcon()
        iconThemeName = u"edit-redo"
        if QIcon.hasThemeIcon(iconThemeName):
            icon6 = QIcon.fromTheme(iconThemeName)
        else:
            icon6.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.redo.setIcon(icon6)

        self.horizontalLayout_2.addWidget(self.redo)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.splitter.addWidget(self.verticalLayoutWidget_2)

        self.horizontalLayout_3.addWidget(self.splitter)


        self.retranslateUi(QRCFixer)

        QMetaObject.connectSlotsByName(QRCFixer)
    # setupUi

    def retranslateUi(self, QRCFixer):
        QRCFixer.setWindowTitle(QCoreApplication.translate("QRCFixer", u"QRCode Fixer", None))
        self.im_remove.setText(QCoreApplication.translate("QRCFixer", u"...", None))
        self.qrc_add.setText("")
        self.qrc_del.setText(QCoreApplication.translate("QRCFixer", u"...", None))
        self.qrc_detect.setText(QCoreApplication.translate("QRCFixer", u"...", None))
        self.undo.setText("")
        self.redo.setText("")
    # retranslateUi

