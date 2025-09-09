from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_15_mass_load import Ui_screen_15_mass_load


class screen_15_mass_load(BaseScreen, Ui_screen_15_mass_load):
    # btn_load_ok = pyqtSignal(str)
    # btn_ico_back = pyqtSignal(str)  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.event_select_tool = lambda *args, **kwargs: print("screen_8_select_tool", *args, **kwargs)


    def set_data(self, *args, **kwargs):
        pass


    def get_data(self):
        pass