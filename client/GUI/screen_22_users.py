from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_22_users import Ui_screen_22_users
from PyQt5.QtCore import QEvent


class screen_22_users(BaseScreen, Ui_screen_22_users):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass