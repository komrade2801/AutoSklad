from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_13_no_right import Ui_screen_13_no_right


class screen_13_no_right(BaseScreen, Ui_screen_13_no_right):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
