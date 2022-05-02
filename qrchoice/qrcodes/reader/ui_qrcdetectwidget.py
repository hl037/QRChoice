# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_qrcdetectwidget.ui'
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
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QHBoxLayout, QLabel,
    QLayout, QListView, QPushButton, QSizePolicy,
    QSpacerItem, QToolButton, QVBoxLayout, QWidget)

class Ui_QRCDetectWidget(object):
    def setupUi(self, QRCDetectWidget):
        if not QRCDetectWidget.objectName():
            QRCDetectWidget.setObjectName(u"QRCDetectWidget")
        QRCDetectWidget.resize(728, 416)
        self.verticalLayout = QVBoxLayout(QRCDetectWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.imViewer = QLabel(QRCDetectWidget)
        self.imViewer.setObjectName(u"imViewer")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imViewer.sizePolicy().hasHeightForWidth())
        self.imViewer.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.imViewer)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.remFilter = QToolButton(QRCDetectWidget)
        self.remFilter.setObjectName(u"remFilter")
        icon = QIcon()
        iconThemeName = u"list-remove"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.remFilter.setIcon(icon)

        self.horizontalLayout_3.addWidget(self.remFilter)

        self.clearFilters = QToolButton(QRCDetectWidget)
        self.clearFilters.setObjectName(u"clearFilters")
        icon1 = QIcon()
        iconThemeName = u"edit-clear"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.clearFilters.setIcon(icon1)

        self.horizontalLayout_3.addWidget(self.clearFilters)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.filterView = QListView(QRCDetectWidget)
        self.filterView.setObjectName(u"filterView")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.filterView.sizePolicy().hasHeightForWidth())
        self.filterView.setSizePolicy(sizePolicy1)
        self.filterView.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.filterView.setResizeMode(QListView.Fixed)

        self.verticalLayout_3.addWidget(self.filterView)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.filterButtons = QVBoxLayout()
        self.filterButtons.setObjectName(u"filterButtons")

        self.verticalLayout_2.addLayout(self.filterButtons)

        self.info = QLabel(QRCDetectWidget)
        self.info.setObjectName(u"info")
        self.info.setMinimumSize(QSize(200, 0))

        self.verticalLayout_2.addWidget(self.info)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.filterArgs = QLabel(QRCDetectWidget)
        self.filterArgs.setObjectName(u"filterArgs")
        self.filterArgs.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.horizontalLayout_4.addWidget(self.filterArgs)

        self.copyArgs = QPushButton(QRCDetectWidget)
        self.copyArgs.setObjectName(u"copyArgs")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.copyArgs.sizePolicy().hasHeightForWidth())
        self.copyArgs.setSizePolicy(sizePolicy2)

        self.horizontalLayout_4.addWidget(self.copyArgs)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.detect = QPushButton(QRCDetectWidget)
        self.detect.setObjectName(u"detect")
        icon2 = QIcon()
        iconThemeName = u"zoom-next"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.detect.setIcon(icon2)

        self.horizontalLayout_2.addWidget(self.detect)

        self.apply = QPushButton(QRCDetectWidget)
        self.apply.setObjectName(u"apply")
        icon3 = QIcon()
        iconThemeName = u"dialog-ok-apply"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)
        
        self.apply.setIcon(icon3)

        self.horizontalLayout_2.addWidget(self.apply)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(QRCDetectWidget)

        QMetaObject.connectSlotsByName(QRCDetectWidget)
    # setupUi

    def retranslateUi(self, QRCDetectWidget):
        QRCDetectWidget.setWindowTitle(QCoreApplication.translate("QRCDetectWidget", u"Form", None))
        self.imViewer.setText("")
        self.remFilter.setText("")
        self.clearFilters.setText("")
        self.info.setText("")
        self.filterArgs.setText("")
        self.copyArgs.setText(QCoreApplication.translate("QRCDetectWidget", u"Copy", None))
        self.detect.setText(QCoreApplication.translate("QRCDetectWidget", u"Detect", None))
        self.apply.setText(QCoreApplication.translate("QRCDetectWidget", u"Apply", None))
    # retranslateUi

