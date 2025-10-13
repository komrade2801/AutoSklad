from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen
from .ui_classes.Ui_widget_20_count_tool import Ui_widget_20_count_tool


class WidgetCountTool(BaseScreen, Ui_widget_20_count_tool):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)


    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def set_data(self, name, count):
        """Устанавливает текстовые данные для отображения."""
        self.lbl_count.setText(str(count))
        self.lbl_status.setText('Ок')
        self.lbl_number_tool.setText(str(name))

    def get_data(self):
        pass
    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(440, 135)