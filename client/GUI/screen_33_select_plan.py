import traceback
from Core.app_logging import get_logger
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_33_select_plan import Ui_screen_33_select_plan
from PyQt5.QtCore import QEvent, QTimer

from .widgets.widget_plan import WidgetPlan


class screen_33_select_plan(BaseScreen, Ui_screen_33_select_plan):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_plan = lambda *args, **kwargs: logger.debug("screen_33_select_plan %s %s", args, kwargs)

        self.value = None
        self.trigger = None

        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.timeout_back = int(self.lbl_timeout_back.text())
        self.__timeout_back = self.timeout_back
        self.event_timeout_back = lambda *args, **kwargs: self.hide()

    def check_visibility(self):
        if self.timeout_back > 1:
            self.timeout_back = self.timeout_back - 1
            self.lbl_timeout_back.setText(str(self.timeout_back))
        else:
            self.timeout_back = self.__timeout_back
            self.lbl_timeout_back.setText(str(self.timeout_back))
            self.event_timeout_back("timeout_back")

    def showEvent(self, event):
        """Событие, которое срабатывает, когда виджет показывается."""
        super().showEvent(event)
        self.visibility_timer.start(1000)
        self.timeout_back = self.__timeout_back

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back

    def set_data(self, *args, **kwargs):
        logger.debug("screen_33_select_plan set_data args=%s kwargs=%s", args, kwargs)
        """
        Устанавливает текстовые данные для виджетов WidgetSummary.

        Ожидается, что данные передаются в виде:
        [{'datetime': datetime.datetime, 'user_name': str, 'user_family': str, ...}, ...]

        Каждый элемент отображается как отдельный виджет в listWidget.
        """
        try:
            data_list = args[0]  # Список данных, переданный первым аргументом
            if not isinstance(data_list, list):
                print("Ошибка: Ожидается список словарей.")
                return

            self.listWidget.clear()  # Очищаем список перед добавлением новых данных

            for data in data_list:
                if not isinstance(data, dict):
                    logger.warning("Ошибка: Ожидается словарь, получено: %s", type(data))
                    continue

                # Создаем виджет WidgetPlan и передаем данные
                widget_plan = WidgetPlan()
                widget_plan.set_data(**data)
                widget_plan.event_select_plan = self.handle_select_plan

                # Создаем элемент списка для listWidget
                list_item = QListWidgetItem(self.listWidget)
                list_item.setSizeHint(widget_plan.sizeHint())  # Устанавливаем размер

                # Добавляем в список и связываем с виджетом
                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget_plan)

        except Exception as e:
            logger.exception("Ошибка в set_data: %s", e)

    def get_data(self):
        logger.debug("screen_33_select_plan get_data")
        try:
            if self.value:
                return {"plan_id": self.value[0], "plan_designation": self.value[1], "plan_name": self.value[2]}
        except Exception:
            logger.exception("screen_33_select_plan get_data")

    def handle_select_plan(self, *args, **kwargs):
        logger.debug("screen_33_select_plan handle_select_plan args=%s kwargs=%s", args, kwargs)
        self.value, self.trigger = args
        self.event_select_plan(self.value[0], self.trigger)
