import traceback
from PyQt5.QtWidgets import QListWidgetItem

from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_17_mass_drop import Ui_screen_17_mass_drop
from PyQt5.QtCore import QEvent

from .widgets.widget_mass_drop_tool import WidgetMassDropTool


class screen_17_mass_drop(BaseScreen, Ui_screen_17_mass_drop):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.event_select_tool = lambda *args, **kwargs: print("screen_8_select_tool", *args, **kwargs)

    def set_data(self, *args, **kwargs):
        logger.debug("screen_17_mass_drop set_data args=%s kwargs=%s", args, kwargs)
        try:
            cell_list = args[0] if len(args) > 0 and args[0] is not None else []
            self.lbl_group_count.setText(f"Ячеек: {len(cell_list)}")

            if args[1] and args[1] == 'btn_down':
                cell_list.sort(reverse=False, key=self.mass_load_sort_by_cell_func)
            else:
                cell_list.sort(reverse=False, key=self.mass_load_sort_by_tool_func)

            self.listWidget.clear()  # Очищаем список перед добавлением новых данных
            try:
                for cell_data in cell_list:
                    if not isinstance(cell_data, dict):
                        continue

                    # Создаём кастомный виджет
                    widget = WidgetMassDropTool()
                    widget.set_data(cell_data)  # Передаём данные в кастомный виджет
                    list_item = QListWidgetItem(self.listWidget)
                    list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                    self.listWidget.addItem(list_item)
                    self.listWidget.setItemWidget(list_item, widget)
            except Exception as e:
                logger.exception("Ошибка при добавлении ячейки: %s", e)
            pass
        except Exception:
            logger.exception("screen_17_mass_drop set_data")

    def get_data(self):
        logger.debug("screen_17_mass_drop get_data")
        pass

    def mass_load_sort_by_cell_func(self, e):
        return e['cell_number']

    def mass_load_sort_by_tool_func(self, e):
        return e['tools_name']