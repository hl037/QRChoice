# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_qrcfixer.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGraphicsView, QHBoxLayout,
    QListView, QSizePolicy, QSplitter, QToolButton,
    QVBoxLayout, QWidget)

from .custom import ImageView

class Ui_QRCFixer(object):
    def setupUi(self, QRCFixer):
        if not QRCFixer.objectName():
            QRCFixer.setObjectName(u"QRCFixer")
        QRCFixer.resize(667, 875)
        icon = QIcon(QIcon.fromTheme(u"applications-development"))
        QRCFixer.setWindowIcon(icon)
        self.horizontalLayout_3 = QHBoxLayout(QRCFixer)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.view = ImageView(QRCFixer)
        self.view.setObjectName(u"view")
        self.view.viewport().setProperty("cursor", QCursor(Qt.CrossCursor))
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
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

        self.im_list = QListView(self.verticalLayoutWidget)
        self.im_list.setObjectName(u"im_list")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.im_list.sizePolicy().hasHeightForWidth())
        self.im_list.setSizePolicy(sizePolicy)

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
        self.qrc_add = QToolButton(self.verticalLayoutWidget_2)
        self.qrc_add.setObjectName(u"qrc_add")
        icon1 = QIcon(QIcon.fromTheme(u"list-add"))
        self.qrc_add.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.qrc_add)

        self.toolButton_4 = QToolButton(self.verticalLayoutWidget_2)
        self.toolButton_4.setObjectName(u"toolButton_4")
        icon2 = QIcon(QIcon.fromTheme(u"list-remove"))
        self.toolButton_4.setIcon(icon2)

        self.horizontalLayout_2.addWidget(self.toolButton_4)

        self.qrc_detect = QToolButton(self.verticalLayoutWidget_2)
        self.qrc_detect.setObjectName(u"qrc_detect")
        icon3 = QIcon(QIcon.fromTheme(u"zoom-next"))
        self.qrc_detect.setIcon(icon3)

        self.horizontalLayout_2.addWidget(self.qrc_detect)

        self.toolButton = QToolButton(self.verticalLayoutWidget_2)
        self.toolButton.setObjectName(u"toolButton")
        icon4 = QIcon(QIcon.fromTheme(u"document-save"))
        self.toolButton.setIcon(icon4)

        self.horizontalLayout_2.addWidget(self.toolButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.splitter.addWidget(self.verticalLayoutWidget_2)

        self.horizontalLayout_3.addWidget(self.splitter)


        self.retranslateUi(QRCFixer)

        QMetaObject.connectSlotsByName(QRCFixer)
    # setupUi

    def retranslateUi(self, QRCFixer):
        QRCFixer.setWindowTitle(QCoreApplication.translate("QRCFixer", u"QRCode Fixer", None))
        self.qrc_add.setText("")
        self.toolButton_4.setText(QCoreApplication.translate("QRCFixer", u"...", None))
        self.qrc_detect.setText(QCoreApplication.translate("QRCFixer", u"...", None))
        self.toolButton.setText("")
    # retranslateUi

