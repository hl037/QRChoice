# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_qrcdetectwidget.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLayout,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_QRCDetectWidget(object):
    def setupUi(self, QRCDetectWidget):
        if not QRCDetectWidget.objectName():
            QRCDetectWidget.setObjectName(u"QRCDetectWidget")
        QRCDetectWidget.resize(511, 306)
        self.verticalLayout = QVBoxLayout(QRCDetectWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.imViewer = QLabel(QRCDetectWidget)
        self.imViewer.setObjectName(u"imViewer")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imViewer.sizePolicy().hasHeightForWidth())
        self.imViewer.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.imViewer)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pushButton = QPushButton(QRCDetectWidget)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout_2.addWidget(self.pushButton)

        self.info = QLabel(QRCDetectWidget)
        self.info.setObjectName(u"info")

        self.verticalLayout_2.addWidget(self.info)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.detect = QPushButton(QRCDetectWidget)
        self.detect.setObjectName(u"detect")
        icon = QIcon(QIcon.fromTheme(u"zoom-next"))
        self.detect.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.detect)

        self.apply = QPushButton(QRCDetectWidget)
        self.apply.setObjectName(u"apply")
        icon1 = QIcon(QIcon.fromTheme(u"dialog-ok-apply"))
        self.apply.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.apply)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(QRCDetectWidget)

        QMetaObject.connectSlotsByName(QRCDetectWidget)
    # setupUi

    def retranslateUi(self, QRCDetectWidget):
        QRCDetectWidget.setWindowTitle(QCoreApplication.translate("QRCDetectWidget", u"Form", None))
        self.imViewer.setText("")
        self.pushButton.setText(QCoreApplication.translate("QRCDetectWidget", u"PushButton", None))
        self.info.setText(QCoreApplication.translate("QRCDetectWidget", u"test", None))
        self.detect.setText(QCoreApplication.translate("QRCDetectWidget", u"Detect", None))
        self.apply.setText(QCoreApplication.translate("QRCDetectWidget", u"Apply", None))
    # retranslateUi

