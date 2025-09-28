import traceback

from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_20_management_tool import Ui_screen_20_management_tool
from PyQt5.QtCore import QEvent

from .widgets.widget_count_tool import WidgetCountTool


class screen_20_management_tool(BaseScreen, Ui_screen_20_management_tool):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_management_group = lambda *args, **kwargs: print("screen_19_management_group", *args, **kwargs)

        self.value = None
        self.trigger = None

    def populate_list(self):
        print("screen_20_management_tool populate_list")
        print(self.groups)
        for group in self.groups:
            widget = WidgetCountTool()
            widget.set_data(group, 0)
            widget.key_pressed.connect(self.on_group_selected)  # Подключаем обработчик сигнала

            list_item = QListWidgetItem(self.listWidget)
            list_item.setSizeHint(widget.sizeHint())
            self.listWidget.addItem(list_item)
            self.listWidget.setItemWidget(list_item, widget)

    def set_data(self, *args, **kwargs):
        print("screen_20_management_tool set_data")
        print(args)
        print(kwargs)
        """Устанавливает текст. Реализуется в каждом экране.
        Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        if not args[0]:
            return
        tools = args[0][0]
        if not tools:
            return

        name = args[0][1]
        self.lbl_name_group.setText(name)

        self.listWidget.clear()  # Очищаем список перед добавлением новых данных
        try:
            print(tools)
            for tool in tools:
                # Создаём кастомный виджет
                widget = WidgetCountTool()
                widget.set_data(tool.name, len(tools))  # Передаём данные в кастомный виджет
                widget.event_select_management_group = self.handle_select_group
                # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                list_item = QListWidgetItem(self.listWidget)
                list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета
                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        pass


    def handle_select_group(self, *args, **kwargs):
        self.value, self.trigger = args
        self.event_select_management_group(self.value[0], self.trigger)

    def get_data(self):
        print(f"screen_20_management_tool get_data. value {self.value}")
        try:
            if self.value:
                return {"group_id": self.value[0], "group_name": self.value[1]}
        except:
            print(traceback.format_exc())
