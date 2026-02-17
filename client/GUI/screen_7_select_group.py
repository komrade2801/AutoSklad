from Core.app_logging import get_logger
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_7_select_group import Ui_screen_7_select_group

from PyQt5.QtCore import QEvent

from .widgets.widget_select_group import WidgetSelectGroup
from DB.Models.Group import Group


class screen_7_select_group(BaseScreen, Ui_screen_7_select_group):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_group = lambda *args, **kwargs: logger.debug("screen_7_select_group %s %s", args, kwargs)
        self.trigger_name = "btn_select_group_names"
        self.value = None
        self.trigger = None
    def populate_list(self):
        for group in self.groups:
            widget = WidgetSelectGroup(self.trigger_name)
            widget.set_data(group, 0)
            widget.key_pressed.connect(self.on_group_selected)  # Подключаем обработчик сигнала

            list_item = QListWidgetItem(self.listWidget)
            list_item.setSizeHint(widget.sizeHint())
            self.listWidget.addItem(list_item)
            self.listWidget.setItemWidget(list_item, widget)

    def on_group_selected(self, group_id):
        logger.debug("Группа с ID %s выбрана.", group_id)

    def set_data(self, *args, **kwargs):
        logger.debug("screen_7_select_group set_data args=%s kwargs=%s", args, kwargs)
        """Устанавливает текст. Реализуется в каждом экране."""
        """
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        groups = args[0]
        logger.debug("args[0]=%s", args[0])
        self.listWidget.clear()  # Всегда очищаем список (в т.ч. когда групп с инструментом 0 — чтобы не показывать устаревшие)
        if not groups:
            return
        logger.debug("groups=%s", groups)
        if not isinstance(groups, dict):
            return

        # Логирование: список групп, количество инструментов по группам
        groups_list = [
            {"id": g.id, "name": g.name, "count": c}
            for g, c in groups.items()
        ]
        root_groups_list = [
            {"id": g.id, "name": g.name, "count": c}
            for g, c in groups.items()
            if g.paren_group_id == 0
        ]
        logger.info(
            "screen_7_select_group: полученный список групп (всего %d): %s",
            len(groups_list),
            groups_list,
        )
        logger.info(
            "screen_7_select_group: корневые группы для отображения (%d): %s",
            len(root_groups_list),
            root_groups_list,
        )
        logger.info(
            "screen_7_select_group: список инструментов по номенклатуре (количество по группам): %s",
            {g.name: c for g, c in groups.items()},
        )
        # print(groups[0])
        # print(isinstance(groups[0], Group))
        # print(type(Group))
        # if not isinstance(groups[0], Group):
        #     return

        try:
            for group, count in groups.items():
                logger.debug("group=%s", group)

                if group.paren_group_id != 0:
                    continue
                # Создаём кастомный виджет
                widget = WidgetSelectGroup(self.trigger_name)
                widget.set_data(group, count)  # Передаём данные в кастомный виджет
                widget.event_select_group = self.handle_select_group
                logger.debug("widget=%s", widget)
                list_item = QListWidgetItem(self.listWidget)
                list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета
                logger.debug("list_item=%s", list_item)

                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget)
        except Exception as e:
            logger.exception("screen_7_select_group set_data: %s", e)
        pass

    def handle_select_group(self, *args, **kwargs):
        self.value, self.trigger = args
        self.event_select_group(self.value[0], self.trigger)

    def get_data(self):
        try:
            if self.value:
                return {"group_id": self.value[0], "group_name": self.value[1]}
        except Exception:
            logger.exception("screen_7_select_group get_data")

