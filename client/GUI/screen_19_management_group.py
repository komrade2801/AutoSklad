import traceback
from Core.app_logging import get_logger
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_19_management_group import Ui_screen_19_management_group
from PyQt5.QtCore import QEvent

from .widgets.widget_select_group import WidgetSelectGroup

class screen_19_management_group(BaseScreen, Ui_screen_19_management_group):
    def __init__(self):
        super().__init__()
        self.enable_touch_scroll = True
        self.setupUi(self)
        self.event_select_group = lambda *args, **kwargs: logger.debug("screen_19_management_group %s %s", args, kwargs)

        self.value = None
        self.trigger = None
        self.trigger_name = "btn_warehouse_select_tools"

    def populate_list(self):
        for group in self.groups:
            widget = WidgetSelectGroup(self.trigger_name)
            widget.set_data(group)
            # Подключаем обработчик сигнала
            widget.key_pressed.connect(self.on_group_selected)

            list_item = QListWidgetItem(self.listWidget)
            list_item.setSizeHint(widget.sizeHint())
            self.listWidget.addItem(list_item)
            self.listWidget.setItemWidget(list_item, widget)

    def on_group_selected(self, group_id):
        logger.debug("Группа с ID %s выбрана.", group_id)

    def set_data(self, *args, **kwargs):
        logger.debug("screen_19_management_group set_data args=%s kwargs=%s", args, kwargs)
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде словаря:
        {group_id: {'group': Group, 'tools': list, 'cells': list}, ...}
        """
        self.value = None
        self.trigger = None

        groups = args[0]
        if not groups:
            return
        self.listWidget.clear()  # Очищаем список перед добавлением новых данных
        try:
            for group_id, group_data in groups.items():
                group = group_data['group']

                if group.paren_group_id != 0:
                    continue
                # Создаём кастомный виджет
                widget = WidgetSelectGroup(self.trigger_name)
                # Передаём данные в кастомный виджет
                widget.set_data(group, len(group_data['cells']))
                # Подключаем обработчик сигнала
                widget.key_pressed.connect(self.on_group_selected)
                widget.event_select_group = self.handle_select_group
                # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                list_item = QListWidgetItem(self.listWidget)
                # Используем размер из виджета
                list_item.setSizeHint(widget.sizeHint())

                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget)
        except Exception as e:
            logger.exception("screen_19_management_group set_data: %s", e)
        pass

    def handle_select_group(self, *args, **kwargs):
        self.value, self.trigger = args
        self.event_select_group(self.value[0], self.trigger)

    def get_data(self):
        if self.value is not None:
            return {"group_id": self.value[0], "group_name": self.value[1]}
        return None
