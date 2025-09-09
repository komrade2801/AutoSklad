import traceback

from PyQt5.QtWidgets import QListWidgetItem

from DB.Models.Tools import Tools
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_9_select_tool_for_plan_by_barcode import Ui_screen_9_select_tool_for_plan_by_barcode
from PyQt5.QtCore import QEvent
from GUI.widgets.widget_select_tool import WidgetSelectTool


class screen_9_select_tool_for_plan_by_barcode(BaseScreen, Ui_screen_9_select_tool_for_plan_by_barcode):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_tool = lambda *args, **kwargs: print("screen_9_select_tool_for_plan_by_barcode", *args, **kwargs)

        self.value = None
        self.trigger = None

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        try:
            plan = args[0][0]
            self.lbl_plan_number.setText(plan.name)

            tools = args[0][1]
            if not tools:
                return
            self.listWidget.clear()  # Очищаем список перед добавлением новых данных
            try:
                for tool in tools:
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
        self.value, self.trigger = args
        self.event_select_tool(self.value[0], self.trigger)
