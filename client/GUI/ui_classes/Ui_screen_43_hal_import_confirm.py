# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_screen_43_hal_import_confirm(object):
    def setupUi(self, screen_43_hal_import_confirm):
        screen_43_hal_import_confirm.setObjectName("screen_43_hal_import_confirm")
        screen_43_hal_import_confirm.resize(480, 800)
        screen_43_hal_import_confirm.setStyleSheet("QWidget{\n"
"    background-color: #2e4461;\n"
"}\n"
"QLabel {\n"
"    background: none;\n"
"    color: #FFFFFF;\n"
"    border-width: 0px;\n"
"    border-radius: 0px;\n"
"    font-family: \"Roboto\", Sans-serif;\n"
"}\n"
"QPushButton {\n"
"    color: #FFFFFF;\n"
"    background-color: #f09022;\n"
"    border-width: 0px;\n"
"    border-radius: 8px;\n"
"    font-weight: 600;\n"
"    font-family: \"Roboto\", Sans-serif;\n"
"}")
        self.verticalLayout = QtWidgets.QVBoxLayout(screen_43_hal_import_confirm)
        self.verticalLayout.setContentsMargins(24, 24, 24, 24)
        self.verticalLayout.setSpacing(16)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lbl_title = QtWidgets.QLabel(screen_43_hal_import_confirm)
        self.lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 34px; font-weight: 700;")
        self.lbl_title.setObjectName("lbl_title")
        self.verticalLayout.addWidget(self.lbl_title)
        self.lbl_icon = QtWidgets.QLabel(screen_43_hal_import_confirm)
        self.lbl_icon.setMinimumSize(QtCore.QSize(0, 96))
        self.lbl_icon.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_icon.setPixmap(QtGui.QPixmap(":/icons/down.png"))
        self.lbl_icon.setScaledContents(False)
        self.lbl_icon.setObjectName("lbl_icon")
        self.verticalLayout.addWidget(self.lbl_icon)
        self.lbl_body = QtWidgets.QLabel(screen_43_hal_import_confirm)
        self.lbl_body.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_body.setStyleSheet("font-size: 22px;")
        self.lbl_body.setWordWrap(True)
        self.lbl_body.setObjectName("lbl_body")
        self.verticalLayout.addWidget(self.lbl_body)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.btn_ok = QtWidgets.QPushButton(screen_43_hal_import_confirm)
        self.btn_ok.setMinimumSize(QtCore.QSize(0, 72))
        self.btn_ok.setStyleSheet("QPushButton { color: #FFFFFF; background-color: #f09022; border-radius: 8px; font-weight: 600; font-size: 25px; min-height: 72px; }")
        self.btn_ok.setObjectName("btn_ok")
        self.verticalLayout.addWidget(self.btn_ok)
        self.btn_back = QtWidgets.QPushButton(screen_43_hal_import_confirm)
        self.btn_back.setMinimumSize(QtCore.QSize(0, 72))
        self.btn_back.setStyleSheet("QPushButton { color: #FFFFFF; background-color: #f09022; border-radius: 8px; font-weight: 600; font-size: 25px; min-height: 72px; }")
        self.btn_back.setObjectName("btn_back")
        self.verticalLayout.addWidget(self.btn_back)

        self.retranslateUi(screen_43_hal_import_confirm)
        QtCore.QMetaObject.connectSlotsByName(screen_43_hal_import_confirm)

    def retranslateUi(self, screen_43_hal_import_confirm):
        _translate = QtCore.QCoreApplication.translate
        screen_43_hal_import_confirm.setWindowTitle(_translate("screen_43_hal_import_confirm", "screen_43_hal_import_confirm"))
        self.lbl_title.setText(_translate("screen_43_hal_import_confirm", "Импорт координат"))
        self.lbl_body.setText(_translate("screen_43_hal_import_confirm", "Импортировать координаты из файла?"))
        self.btn_ok.setText(_translate("screen_43_hal_import_confirm", "ОК"))
        self.btn_back.setText(_translate("screen_43_hal_import_confirm", "Отмена"))
from ..img import resources_rc
