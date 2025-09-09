from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from GUI.BaseScreen import BaseScreen
from GUI.widgets.ui_classes.widget_27_4_21_err_no_list_tool import Ui_widget_27_4_21_err_no_list_tool as Ui


class WidgetErrNoListTool(BaseScreen, Ui):
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
        self.lbl_name_error.setText(group['message'])
        self.lbl_data.setText(str(group['timestamp']))
    def get_data(self):
        pass

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(440, 135)