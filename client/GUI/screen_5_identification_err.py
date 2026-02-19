from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_5_Identification_err import Ui_screen_5_identification_err


class screen_5_identification_err(BaseScreen, Ui_screen_5_identification_err):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
