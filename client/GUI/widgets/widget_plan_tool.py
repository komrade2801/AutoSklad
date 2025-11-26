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
        # self.status_val = ""
        self.select_count_value = 0
        self.load_count_value = 0


    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def set_data(self, tool_data, toolsUpdateFunc):
        """Устанавливает текстовые данные для отображения."""
        tool_type = tool_data["tool_type"]
        self.load_count_value = tool_data["load_count"]
        self.tool_type_id = tool_type.id
        self.name_val = str(tool_type.name)
        self.groups_id_val = tool_type.groups_id
        self.description_val = str(tool_type.description)
        # self.status_val = "В наличии" if tool_data["has_tools"] else "Недостаточно"

        self.select_count.setText(str(self.select_count_value))
        self.plan_count.setText(str(tool_data["plan_count"]))
        self.load_count.setText(str(self.load_count_value))
        # self.status.setText(self.status_val)
        self.lbl_number_tool.setText(self.name_val)

        self.btn_count_up.clicked.connect(lambda: self.changeSelectCount(tool_type.id, toolsUpdateFunc, True))
        self.btn_count_down.clicked.connect(lambda: self.changeSelectCount(tool_type.id, toolsUpdateFunc, False))

    def get_data(self):
        pass

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(self.width(), self.height())

    # def mousePressEvent(self, event):
    #     """Обработка нажатия мыши на виджет."""
    #     super().mousePressEvent(event)  # Сохраняем стандартное поведение
    #     self.widget_clicked.emit()  # Генерируем сигнал клика по виджету
    #     self.event_select_tool((self.tool_type_id, self.name_val, self.groups_id_val, self.description_val), "btn_tool_name")

    def changeSelectCount(self, tool_id, toolsUpdateFunc, increase: bool = True):
        print(f"changeSelectCount increase {increase}")
        if increase:
            if self.select_count_value < self.load_count_value:
                self.select_count_value += 1
        else:
            if self.select_count_value > 0:
                self.select_count_value -= 1

        self.select_count.setText(str(self.select_count_value))

        toolsUpdateFunc(tool_id, self.select_count_value)