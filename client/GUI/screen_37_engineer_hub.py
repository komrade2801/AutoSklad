from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_37_engineer_hub import Ui_screen_37_engineer_hub

logger = get_logger(__name__)


class screen_37_engineer_hub(BaseScreen, Ui_screen_37_engineer_hub):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.normalize_screen_geometry()

    def set_data(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, tuple) and arg:
                user = arg[0]
                self.lbl_name.setText(self.format_fio_short(user))

    def get_data(self):
        return None
