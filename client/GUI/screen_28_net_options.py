from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_28_net_options import Ui_screen_28_net_options
from PyQt5.QtCore import QEvent


class screen_28_net_options(BaseScreen, Ui_screen_28_net_options):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
