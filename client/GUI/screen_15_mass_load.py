from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import traceback
from PyQt5.QtWidgets import QListWidgetItem

from Core.app_logging import get_logger
from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_15_mass_load import Ui_screen_15_mass_load

from .widgets.widget_mass_load_tool import WidgetMassLoadTool


class screen_15_mass_load(BaseScreen, Ui_screen_15_mass_load):
    # btn_load_ok = pyqtSignal(str)
    # btn_ico_back = pyqtSignal(str)  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.enable_touch_scroll = True
        self.setupUi(self)
        # self.event_select_tool = lambda *args, **kwargs: print("screen_8_select_tool", *args, **kwargs)


    def set_data(self, *args, **kwargs):
        logger.debug("screen_15_mass_load set_data args=%s kwargs=%s", args, kwargs)
        try:
            payload, source = self.split_set_data_args(args, kwargs)
            cell_list = payload if isinstance(payload, list) else []
            self.lbl_group_count.setText(f"Ячеек: {len(cell_list)}")

            if source == 'btn_down':
                cell_list.sort(reverse=False, key=self.mass_load_sort_by_cell_func)
            else:
                cell_list.sort(reverse=False, key=self.mass_load_sort_by_tool_func)

            self.listWidget.clear()  # Очищаем список перед добавлением новых данных
            try:
                for cell_data in cell_list:
                    if not isinstance(cell_data, dict):
                        continue

                    # Создаём кастомный виджет
                    widget = WidgetMassLoadTool()
                    widget.set_data(cell_data)  # Передаём данные в кастомный виджет
                    list_item = QListWidgetItem(self.listWidget)
                    list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                    self.listWidget.addItem(list_item)
                    self.listWidget.setItemWidget(list_item, widget)
            except Exception as e:
                logger.exception("screen_15_mass_load set_data: %s", e)
            pass
        except Exception:
            logger.exception("screen_15_mass_load set_data")


    def get_data(self):
        logger.debug("screen_15_mass_load get_data")
        pass

    def mass_load_sort_by_cell_func(self, e):
        return e['cell_number']

    def mass_load_sort_by_tool_func(self, e):
        return e['tools_name']
