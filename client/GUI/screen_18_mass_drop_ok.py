from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_18_mass_drop_ok import Ui_screen_18_mass_drop_ok


class screen_18_mass_drop_ok(BaseScreen, Ui_screen_18_mass_drop_ok):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
