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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialogButtonBox, QHBoxLayout,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

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

        self.horizontalLayout.addWidget(self.imViewer)

        self.info = QLabel(QRCDetectWidget)
        self.info.setObjectName(u"info")

        self.horizontalLayout.addWidget(self.info)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(QRCDetectWidget)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(QRCDetectWidget)

        QMetaObject.connectSlotsByName(QRCDetectWidget)
    # setupUi

    def retranslateUi(self, QRCDetectWidget):
        QRCDetectWidget.setWindowTitle(QCoreApplication.translate("QRCDetectWidget", u"Form", None))
        self.imViewer.setText("")
        self.info.setText(QCoreApplication.translate("QRCDetectWidget", u"test", None))
    # retranslateUi

