from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen
from .ui_classes.Ui_widget_34_plan_tool import Ui_widget_34_plan_tool


class WidgetPlanTool(BaseScreen, Ui_widget_34_plan_tool):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tool_type_id = -1
        self.name_val = ""
        self.groups_id_val = -1
        self.description_val = ""
        self.status_val = ""


    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def set_data(self, tool_data):
        """Устанавливает текстовые данные для отображения."""
        tool_type = tool_data["tool_type"]
        self.tool_type_id = tool_type.id
        self.name_val = str(tool_type.name)
        self.groups_id_val = tool_type.groups_id
        self.description_val = str(tool_type.description)
        self.status_val = "В наличии" if tool_data["has_tools"] else "Недостаточно"

        self.plan_count.setText(str(tool_data["plan_count"]))
        self.load_count.setText(str(tool_data["load_count"]))
        self.status.setText(self.status_val)
        self.lbl_number_tool.setText(self.name_val)

    def get_data(self):
        pass

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(self.width(), self.height())

    def mousePressEvent(self, event):
        """Обработка нажатия мыши на виджет."""
        super().mousePressEvent(event)  # Сохраняем стандартное поведение
        self.widget_clicked.emit()  # Генерируем сигнал клика по виджету
        self.event_select_tool((self.tool_type_id, self.name_val, self.groups_id_val, self.description_val), "btn_tool_name")