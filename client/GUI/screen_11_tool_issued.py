from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_11_tool_issued import Ui_screen_11_tool_issued

logger = get_logger(__name__)


class screen_11_tool_issued(BaseScreen, Ui_screen_11_tool_issued):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def showEvent(self, event):
        super().showEvent(event)

    def hideEvent(self, event):
        super().hideEvent(event)

    def set_data(self, *args, **kwargs):
        logger.debug("screen_11_tool_issued set_data. args: %s, kwargs: %s", args, kwargs)
        pass

    def get_data(self):
        logger.debug("screen_11_tool_issued get_data")
        pass
