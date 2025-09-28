import traceback

from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_21_summary import Ui_screen_21_summary
from PyQt5.QtCore import QEvent, QTimer

from .widgets.widget_summary import WidgetSummary


class screen_21_summary(BaseScreen, Ui_screen_21_summary):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

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
        print("screen_21_summary set_data")
        print(args)
        print(kwargs)
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

            if args[1] and args[1] == 'btn_down':
                data_list.sort(reverse=False, key=self.history_sort_func)
            else:
                data_list.sort(reverse=True, key=self.history_sort_func)

            for data in data_list:
                if not isinstance(data, dict):
                    print(f"Ошибка: Ожидается словарь, получено: {type(data)}")
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
            print(traceback.format_exc())
            print(f"Ошибка в set_data: {e}")


    def get_data(self):
        pass

    def history_sort_func(self, e):
        return e['datetime']
