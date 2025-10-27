from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen
from .ui_classes.Ui_widget_8_9_tool import Ui_widget_8_9_tool


class WidgetSelectTool(BaseScreen, Ui_widget_8_9_tool):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.name = ""
        self.tool_description = ""
        self.status = -1
        self.event_select_tool = lambda *args, **kwargs: print(*args, **kwargs)

    def set_data(self, tool):
        print("WidgetSelectTool set_data")
        print(tool)
        print(tool['group'])
        print(tool['tool'])
        print(tool['cell'])
        """Устанавливает текст. Реализуется в каждом экране."""
        self.lbl_number_tool.setText(tool['tool'].name)
        self.tool_description = tool['tool'].description
        self.group_name.setText(tool['group'].name)
        self.cell_number.setText(str(tool['cell'].number))
        self.name = tool['tool'].name
        # self.lbl_status.setText("2")
        self.status = tool['tool'].id



    def get_data(self):
        pass

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(self.width(), self.height())

    def mousePressEvent(self, event):
        """Обработка нажатия мыши на виджет."""
        super().mousePressEvent(event)  # Сохраняем стандартное поведение
        self.widget_clicked.emit()  # Генерируем сигнал клика по виджету
        self.event_select_tool((self.status, self.name, self.group_name.text(), self.tool_description), "btn_tool_name")