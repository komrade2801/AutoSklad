import traceback

from PyQt5 import QtGui
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_9_select_tool_by_plan import Ui_screen_9_select_tool_by_plan
from DB.Models.Tools import Tools
from PyQt5.QtCore import QEvent
from .widgets.widget_select_tool import WidgetSelectTool
from .widgets.widget_plan_tool import WidgetPlanTool


class screen_9_select_tool_by_plan(BaseScreen, Ui_screen_9_select_tool_by_plan):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_tool = lambda *args, **kwargs: print("screen_9_select_tool_by_plan", *args, **kwargs)

        self.plan_id_val = -1
        self.value = None
        self.trigger = None

    def set_data(self, *args, **kwargs):
        print("screen_9_select_tool_by_plan set_data")
        print(args)
        print(kwargs)
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        try:
            data = args[0]

            plan_name = data[2]
            self.lbl_plan_number.setText(plan_name)

            self.plan_id_val = data[3]

            tools = data[0]
            if not tools:
                return
            self.listWidget.clear()  # Очищаем список перед добавлением новых данных

            has_all_tools = True

            for tool_data in tools:
                print(tool_data)

                if not tool_data['has_tools']:
                    has_all_tools = False

                # Создаём кастомный виджет
                widget = WidgetPlanTool()
                widget.set_data(tool_data)  # Передаём данные в кастомный виджет
                widget.event_select_tool = self.handle_select_tool
                # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                list_item = QListWidgetItem(self.listWidget)
                list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget)

            if has_all_tools:
                icon_path = ":/icons/ok.png"
                self.btn_ok.setDisabled(False)
            else:
                icon_path = ":/icons/ok_disabled.png"
                self.btn_ok.setDisabled(True)
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.On)
            self.btn_ok.setIcon(icon1)

        except Exception as e:
            print(traceback.format_exc())
            print(e)
    pass

    def get_data(self, *args, **kwargs):
        print(f"screen_9_select_tool_by_plan get_data {args} {kwargs} {self.value}")
        try:
            if self.value:
                return {"tool_type_id": self.value[0], "name": self.value[1], "group_name": self.value[2], "tool_description": self.value[3]}
            else:
                return {"plan_id": self.plan_id_val}
        except:
            print(traceback.format_exc())


    def handle_select_tool(self, *args, **kwargs):
        print("screen_9_select_tool_by_plan handle_select_tool")
        print(args)
        print(kwargs)
        self.value, self.trigger = args
        self.event_select_tool(self.value[0], self.trigger)
