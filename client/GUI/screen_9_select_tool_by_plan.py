import traceback

from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_9_select_tool_by_plan import Ui_screen_9_select_tool_by_plan
from DB.Models.Tools import Tools
from PyQt5.QtCore import QEvent
from .widgets.widget_select_tool import WidgetSelectTool
from .widgets.widget_count_tool import WidgetCountTool


class screen_9_select_tool_by_plan(BaseScreen, Ui_screen_9_select_tool_by_plan):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_tool = lambda *args, **kwargs: print("screen_9_select_tool_by_plan", *args, **kwargs)

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

            tools = data[0]
            if not tools:
                return
            self.listWidget.clear()  # Очищаем список перед добавлением новых данных
            try:
                for tool_data in tools:
                    print(tool_data)
                    tool = tool_data['tool_type']
                    count = tool_data['count']
                    print(tool)
                    # Создаём кастомный виджет
                    widget = WidgetCountTool()
                    widget.set_data(tool.name, count)  # Передаём данные в кастомный виджет
                    widget.event_select_tool = self.handle_select_tool
                    # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                    list_item = QListWidgetItem(self.listWidget)
                    list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                    self.listWidget.addItem(list_item)
                    self.listWidget.setItemWidget(list_item, widget)
            except Exception as e:
                print(traceback.format_exc())
                plan = args[0][0]
                self.lbl_plan_number.setText(plan.name)

                tools = args[0]
                if not tools:
                    return
                self.listWidget.clear()  # Очищаем список перед добавлением новых данных
                try:
                    for tool in tools:
                        if isinstance(tool, Tools):
                            # Создаём кастомный виджет
                            widget = WidgetSelectTool()
                            widget.set_data(tool)  # Передаём данные в кастомный виджет
                            widget.event_select_tool = self.handle_select_tool
                            # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                            list_item = QListWidgetItem(self.listWidget)
                            list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                            self.listWidget.addItem(list_item)
                            self.listWidget.setItemWidget(list_item, widget)
                except Exception as e:
                    print(traceback.format_exc())
                    print(e)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
    pass

    def get_data(self, *args, **kwargs):
        try:
            if self.value:
                return {"tool_id": self.value[0], "name": self.value[1]}
        except:
            print(traceback.format_exc())


    def handle_select_tool(self, *args, **kwargs):
        print("screen_9_select_tool_by_plan handle_select_tool")
        print(args)
        print(kwargs)
        self.value, self.trigger = args
        self.event_select_tool(self.value[0], self.trigger)
