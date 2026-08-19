import traceback
from Core.app_logging import get_logger
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_21_summary import Ui_screen_21_summary

from .widgets.widget_summary import WidgetSummary


class screen_21_summary(BaseScreen, Ui_screen_21_summary):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        logger.debug("screen_21_summary set_data args=%s kwargs=%s", args, kwargs)
        """
        Устанавливает текстовые данные для виджетов WidgetSummary.

        Ожидается, что данные передаются в виде:
        [{'datetime': datetime.datetime, 'user_name': str, 'user_family': str, ...}, ...]

        Каждый элемент отображается как отдельный виджет в listWidget.
        """
        try:
            data_list, source = self.split_set_data_args(args, kwargs)
            if not isinstance(data_list, list):
                logger.warning("Ошибка: Ожидается список словарей.")
                return

            self.listWidget.clear()  # Очищаем список перед добавлением новых данных

            if source == 'btn_down':
                data_list.sort(reverse=False, key=self.history_sort_func)
            else:
                data_list.sort(reverse=True, key=self.history_sort_func)

            for data in data_list:
                if not isinstance(data, dict):
                    logger.warning("Ошибка: Ожидается словарь, получено: %s", type(data))
                    continue

                # Создаем виджет WidgetSummary и передаем данные
                widget_summary = WidgetSummary()
                widget_summary.set_data(**data)

                # Создаем элемент списка для listWidget
                list_item = QListWidgetItem(self.listWidget)
                list_item.setSizeHint(widget_summary.sizeHint())  # Устанавливаем размер

                # Добавляем в список и связываем с виджетом
                self.listWidget.addItem(list_item)
                self.listWidget.setItemWidget(list_item, widget_summary)

        except Exception as e:
            logger.exception("Ошибка в set_data: %s", e)


    def get_data(self):
        pass

    def history_sort_func(self, e):
        return e['datetime']
