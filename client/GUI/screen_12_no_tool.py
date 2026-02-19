from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_12_no_tool import Ui_screen_12_no_tool


class screen_12_no_tool(BaseScreen, Ui_screen_12_no_tool):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
