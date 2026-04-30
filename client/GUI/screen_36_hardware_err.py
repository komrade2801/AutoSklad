from PyQt5 import QtWidgets, QtCore, QtGui

from GUI.BaseScreen import BaseScreen


class screen_36_hardware_err(BaseScreen):
    def __init__(self):
        super().__init__()
        self.setObjectName("screen_36_hardware_err")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QtWidgets.QLabel("Сбой оборудования", self)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font-size: 34px; font-weight: 700;")
        root.addWidget(title)

        icon = QtWidgets.QLabel(self)
        icon.setAlignment(QtCore.Qt.AlignCenter)
        icon.setMinimumHeight(96)
        pixmap = QtGui.QPixmap(":/icons/error.png")
        if not pixmap.isNull():
            icon.setPixmap(
                pixmap.scaled(
                    96,
                    96,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
            )
        root.addWidget(icon)

        body = QtWidgets.QLabel(
            "Контроллер не прошел проверку связи или не завершил "
            "калибровку/парковку.\n"
            "Проверьте питание, кабель и состояние платы, затем вернитесь на главный экран.",
            self,
        )
        body.setWordWrap(True)
        body.setAlignment(QtCore.Qt.AlignCenter)
        body.setStyleSheet("color: #FFFFFF; font-size: 22px;")
        root.addWidget(body, 1)

        self.btn_back = QtWidgets.QPushButton("Назад", self)
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setMinimumHeight(72)
        self.btn_back.setStyleSheet(
            "QPushButton {"
            "color: #FFFFFF;"
            "background-color: #f09022;"
            "border-radius: 8px;"
            "font-weight: 600;"
            "font-size: 25px;"
            "}"
        )
        root.addWidget(self.btn_back)

    def set_data(self, *args, **kwargs):
        pass

    def get_data(self):
        return None
