from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from GUI.BaseScreen import BaseScreen
from GUI.widgets.ui_classes.widget_25_tool_issued import Ui_widget_25_tool_issued as Ui


class WidgetToolIssued(BaseScreen, Ui):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def set_data(self, group):
        """Устанавливает текстовые данные для отображения."""
        pass

    def get_data(self):
        pass