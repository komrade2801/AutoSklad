import traceback

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_10_confirmation import Ui_screen_10_confirmation
from PyQt5.QtCore import QEvent

class screen_10_confirmation(BaseScreen, Ui_screen_10_confirmation):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.name = None
        self.tool_id = None

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        try:
            value = args[0]

            self.name = value[1]
            self.tool_id = value[0]
            self.lbl_tool_number.setText(self.name)
        except Exception as e:...
            # print(e)
            # print(args)
            # print(traceback.format_exc())

    def get_data(self):
        value = {"tool_name": self.name, "tool_id": self.tool_id}
        return value