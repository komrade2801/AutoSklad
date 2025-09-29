from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen
from ..widgets.ui_classes.widget_8_9_tool import Ui_widget_8_9_tool


class WidgetSelectTool(BaseScreen, Ui_widget_8_9_tool):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.name = ""
        self.status = -1
        self.event_select_tool = lambda *args, **kwargs: print(*args, **kwargs)

    def set_data(self, *args, **kwargs):
        print("WidgetSelectTool set_data")
        print(args)
        print(kwargs)
        """Устанавливает текст. Реализуется в каждом экране."""
        self.lbl_number_tool.setText(args[0].name)
        self.tool_description.setText(args[0].description)
        self.group_name.setText(args[1].name)
        self.cell_number.setText(str(args[2].number))
        self.name = args[0].name
        # self.lbl_status.setText("2")
        self.status = args[0].id



    def get_data(self):
        pass

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(440, 65)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши на виджет."""
        super().mousePressEvent(event)  # Сохраняем стандартное поведение
        self.widget_clicked.emit()  # Генерируем сигнал клика по виджету
        self.event_select_tool((self.status, self.name, self.group_name.text(), self.tool_description.text()), "btn_tool_name")