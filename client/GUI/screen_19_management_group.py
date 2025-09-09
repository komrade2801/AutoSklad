import traceback

from PyQt5.QtWidgets import QListWidgetItem

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_19_management_group import Ui_screen_19_management_group
from PyQt5.QtCore import QEvent

from GUI.widgets.widget_select_group import WidgetSelectGroup


class screen_19_management_group(BaseScreen, Ui_screen_19_management_group):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_group = lambda *args, **kwargs: print("screen_19_management_group", *args, **kwargs)

        self.value = None
        self.trigger = None
        self.trigger_name = "btn_warehouse_select_tools"
    def populate_list(self):
        for group in self.groups:
            widget = WidgetSelectGroup(self.trigger_name)
            widget.set_data(group)
            widget.key_pressed.connect(self.on_group_selected)  # Подключаем обработчик сигнала

            list_item = QListWidgetItem(self.listWidget)
            list_item.setSizeHint(widget.sizeHint())
            self.listWidget.addItem(list_item)
            self.listWidget.setItemWidget(list_item, widget)

    def on_group_selected(self, group_id):
        print(f"Группа с ID {group_id} выбрана.")

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        groups = args[0]
        if not groups:
            return
        self.listWidget.clear()  # Очищаем список перед добавлением новых данных
        try:
            for group in groups:
                # Создаём кастомный виджет
                widget = WidgetSelectGroup(self.trigger_name)
                widget.set_data(groups[group]['group'])  # Передаём данные в кастомный виджет
                widget.event_select_group = self.handle_select_group
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
        self.event_select_group(self.value[0], self.trigger)

    def get_data(self):
        try:
            return {"group_id": self.value[0], "group_name": self.value[1]}
        except:
            print(traceback.format_exc())
