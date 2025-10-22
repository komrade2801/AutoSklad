from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal


class MyLineEdit(QLineEdit):
    focus_in = pyqtSignal(str)  # Сигнал при получении фокуса
    focus_out = pyqtSignal(str)  # Сигнал при потере фокуса

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trigger_length = 4
        self.length_trigger_enable = True


    def focusInEvent(self, event):
        super().focusInEvent(event)

        self.setReadOnly(False)
        # self.setStyleSheet("color: rgb(0, 0, 0);")
        self.setStyleSheet("color: #000000;\n"
            "background-color: #CAE2FF;\n"
            "border-width: 2px;\n"
            "border-style: groove;\n"
            "border-color: #15293D;\n"
            "border-radius: 0px;")
        # self.setText("")
        self.focus_in.emit(self.objectName())  # Отправляем сигнал с именем объекта


    def focusOutEvent(self, event):
        super().focusOutEvent(event)

        self.setReadOnly(False)
        # self.setStyleSheet("color: rgb(0, 0, 0);")
        self.setStyleSheet("color: #000000;\n"
            "background-color: #CAE2FF;\n"
            "border-width: 2px;\n"
            "border-style: groove;\n"
            "border-color: #15293D;\n"
            "border-radius: 0px;")
        self.focus_out.emit(self.objectName())  # Отправляем сигнал с именем объекта



