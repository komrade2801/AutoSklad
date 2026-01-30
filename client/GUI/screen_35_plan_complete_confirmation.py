import traceback

from Core.app_logging import get_logger
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_35_plan_complete_confirmation import Ui_screen_35_plan_complete_confirmation
from PyQt5.QtCore import QEvent, QTimer

from .widgets.widget_plan_complete_tool import WidgetPlanCompleteTool


class screen_35_plan_complete_confirmation(BaseScreen, Ui_screen_35_plan_complete_confirmation):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.value = None
        self.plan_id = None
        self.tool_list = None

    def set_data(self, *args, **kwargs):
        logger.debug("screen_35_plan_complete_confirmation set_data args=%s kwargs=%s", args, kwargs)
        """
        Устанавливает текстовые данные для виджетов WidgetSummary.

        Ожидается, что данные передаются в виде:
        [{'datetime': datetime.datetime, 'user_name': str, 'user_family': str, ...}, ...]

        Каждый элемент отображается как отдельный виджет в listWidget.
        """
        try:
            plan = args[0]

            self.plan_id = plan['plan_id']
            self.plan_number.setText(plan['designation'])

            tool_list = plan['tool_list']  # Список данных, переданный первым аргументом
            if not isinstance(tool_list, list):
                logger.warning("Ошибка: Ожидается список словарей.")
                return

            self.tool_list = plan['tool_list']

            self.listWidget.clear()  # Очищаем список перед добавлением новых данных

            for tool in tool_list:
                if not isinstance(tool, dict):
                    logger.warning("Ошибка: Ожидается словарь, получено: %s", type(tool))
                    continue

                if tool['load_count'] == 0:
                    continue

                # Создаем виджет WidgetPlan и передаем данные
                widget = WidgetPlanCompleteTool()
                widget.set_data(tool)

                # Создаем элемент списка для listWidget
                list_item = QListWidgetItem(self.listWidget)
                list_item.setSizeHint(widget.sizeHint())  # Устанавливаем размер

                # Добавляем в список и связываем с виджетом
                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget)

        except Exception as e:
            logger.exception("Ошибка в set_data: %s", e)

    def get_data(self):
        logger.debug("screen_35_plan_complete_confirmation get_data")
        # value = {"plan_id": self.plan_id}
        value = {"plan_id": self.plan_id, "tool_list": self.tool_list}
        return value