from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
import traceback
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_15_mass_load import Ui_screen_15_mass_load

from .widgets.widget_mass_load_tool import WidgetMassLoadTool


class screen_15_mass_load(BaseScreen, Ui_screen_15_mass_load):
    # btn_load_ok = pyqtSignal(str)
    # btn_ico_back = pyqtSignal(str)  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.event_select_tool = lambda *args, **kwargs: print("screen_8_select_tool", *args, **kwargs)


    def set_data(self, *args, **kwargs):
        print("screen_15_mass_load set_data")
        print(args)
        print(kwargs)
        try:
            if not args[0]:
                return
            cell_list = args[0]
            self.lbl_group_count.setText(f"Ячеек: {len(cell_list)}")

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
                print(e)
                print(traceback.format_exc())
            pass
        except:
            print(traceback.format_exc())


    def get_data(self):
        print("screen_15_mass_load get_data")
        pass