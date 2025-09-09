from PyQt5.QtWidgets import QListWidgetItem

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_27_history_err import Ui_screen_27_history_err
from PyQt5.QtCore import QEvent
from GUI.widgets.widget_err_devices import WidgetErrDevices
from GUI.widgets.widget_err_identification import WidgetErrIdentification
from GUI.widgets.widget_err_identification_barcode import WidgetErrIdentificationBarcode
from GUI.widgets.widget_err_log_psw import WidgetErrLogPSW
from GUI.widgets.widget_err_no_list_tool import WidgetErrNoListTool
from GUI.widgets.widget_err_no_right_receiv_tool import WidgetErrNoRightReceiveTool
from GUI.widgets.widget_err_no_tool import WidgetErrNoTool
from GUI.widgets.widget_err_port_busy import WidgetErrPortBusy
from GUI.widgets.widget_err_timeout import WidgetErrTimeout


class screen_27_history_err(BaseScreen, Ui_screen_27_history_err):


    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def select_widget_for_error(self, error):
        """
        Выбирает соответствующий виджет для отображения ошибки на основе её типа.

        :param error: Объект ошибки с полем error_type.
        :return: Класс виджета, соответствующий типу ошибки.
        """
        # Сопоставление типов ошибок с виджетами
        widget_mapping = {
            'err_get_tools_by_plan_id': WidgetErrIdentification,
            "err_devices": WidgetErrDevices,
            "err_identification": WidgetErrIdentification,
            "err_barcode_user": WidgetErrIdentificationBarcode,
            "err_barcode_plan": WidgetErrIdentificationBarcode,
            "err_login": WidgetErrLogPSW,
            "err_no_list_tool": WidgetErrNoListTool,
            "err_rights": WidgetErrNoRightReceiveTool,
            "err_no_tool": WidgetErrNoTool,
            "err_port_busy": WidgetErrPortBusy,
            "err_timeout": WidgetErrTimeout,
            "err_request": WidgetErrDevices
        }

        # Получаем виджет из словаря на основе типа ошибки
        widget_class = widget_mapping[error]

        if not widget_class:
            raise ValueError(f"Не найден соответствующий виджет для типа ошибки: {error.error_type}")

        return widget_class


    def set_data(self, *args, **kwargs):
        """
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'error_type': 'err_devices', 'message': 'Error message', 'timestamp': '2025-01-19'}, ...]
        """

        errors = args[0]  # Ожидается, что первый аргумент - это список ошибок

        if not errors:
            self.listWidget.clear()  # Если данных нет, очищаем список
            return

        self.listWidget.clear()  # Очищаем список перед добавлением новых данных

        for error_data in errors:
            # Создаём экземпляр виджета на основе типа ошибки
            error_type = error_data.error_type
            error_message = error_data.message
            error_timestamp = error_data.timestamp

            # Получаем соответствующий класс виджета
            widget_class = self.select_widget_for_error(error_type)
            widget = widget_class()


            # Настраиваем виджет с использованием данных ошибки
            widget.set_data({
                'message': error_message,
                'timestamp': error_timestamp
            })

            # Создаём элемент для добавления в listWidget
            list_item = QListWidgetItem(self.listWidget)
            list_item.setSizeHint(widget.sizeHint())

            self.listWidget.addItem(list_item)
            self.listWidget.setItemWidget(list_item, widget)


        # try:
        # except Exception as e:
        #     print(f"Ошибка при установке данных: {e}")

    def get_data(self):
        """
        Метод-заглушка. Возвращает данные, если нужно.
        """
        pass