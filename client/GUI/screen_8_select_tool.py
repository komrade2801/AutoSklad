import traceback

from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_8_select_tool import Ui_screen_8_select_tool
from PyQt5.QtCore import QEvent

# from .widgets.widget_select_tool import WidgetSelectTool
from .widgets.widget_tool_type import WidgetToolType


class screen_8_select_tool(BaseScreen, Ui_screen_8_select_tool):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_tool = lambda *args, **kwargs: print("screen_8_select_tool", *args, **kwargs)

        self.value = None
        self.trigger = None

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        print("screen_8_select_tool set_data")
        print(args)
        print(kwargs)
        try:
            if not args[0]:
                return
            name = args[0][1]
            self.lbl_name_group.setText(name)

            tools = args[0][0]
            self.listWidget.clear()  # Всегда очищаем список (в т.ч. когда инструментов 0 — чтобы не показывать устаревший список)
            if not tools:
                return
            try:
                for tool in tools:
                    print(f"tool: {tool}")
                    # Создаём кастомный виджет
                    widget = WidgetToolType()
                    widget.set_data(tool)  # Передаём данные в кастомный виджет
                    widget.event_select_tool = self.handle_select_tool
                    # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                    list_item = QListWidgetItem(self.listWidget)
                    list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                    self.listWidget.addItem(list_item)
                    self.listWidget.setItemWidget(list_item, widget)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
            pass
        except:
            print(traceback.format_exc())

    def get_data(self, *args, **kwargs):
        print(f"screen_8_select_tool get_data. value {self.value}")
        try:
            if self.value:
                return {"tool_type_id": self.value[0], "name": self.value[1], "group_name": self.value[2], "tool_description": self.value[3]}
        except:
            print(traceback.format_exc())

    def handle_select_tool(self, *args, **kwargs):
        print("screen_8_select_tool handle_select_tool")
        print(args)
        print(kwargs)
        self.value, self.trigger = args
        self.event_select_tool(self.value[0], self.trigger)



