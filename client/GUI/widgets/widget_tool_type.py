from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from Core.app_logging import get_logger
from ..BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_widget_tool_type import Ui_widget_tool_type


class WidgetToolType(BaseScreen, Ui_widget_tool_type):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.lbl_number_tool.setWordWrap(True)
        self.lbl_number_tool.setMaximumHeight(40)
        self.name = ""
        self.tool_type_id = -1
        self.event_select_tool = lambda *args, **kwargs: logger.debug("event_select_tool %s %s", args, kwargs)

    def set_data(self, tool_data):
        logger.debug("WidgetToolType set_data tool_data=%s", tool_data)

        tool_type = tool_data["tool"]

        """Устанавливает текст. Реализуется в каждом экране."""
        self.lbl_number_tool.setText(tool_type.name)
        self.tool_description.setText(tool_type.description)
        self.group_name.setText(tool_data["group"].name)
        self.load_count.setText(str(tool_data["count"]))
        self.name = tool_type.name
        self.status.setText("Доступно" if tool_data["count"] else "Отсутствует")
        self.tool_type_id = tool_type.id

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
        self.event_select_tool((self.tool_type_id, self.name, self.group_name.text(), self.tool_description.text()), "btn_tool_name")