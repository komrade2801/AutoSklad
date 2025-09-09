from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_17_mass_drop import Ui_screen_17_mass_drop
from PyQt5.QtCore import QEvent


class screen_17_mass_drop(BaseScreen, Ui_screen_17_mass_drop):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass