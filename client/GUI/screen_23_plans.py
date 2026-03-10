from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_23_plans import Ui_screen_23_plans
from PyQt5.QtCore import QEvent


class screen_23_plans(BaseScreen, Ui_screen_23_plans):
    def __init__(self):
        super().__init__()
        self.enable_touch_scroll = True
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
