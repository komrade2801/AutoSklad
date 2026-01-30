from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_11_tool_issued import Ui_screen_11_tool_issued
from PyQt5.QtCore import QEvent, QTimer

logger = get_logger(__name__)


class screen_11_tool_issued(BaseScreen, Ui_screen_11_tool_issued):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.timeout_back = int(self.lbl_timeout_back.text())
        self.__timeout_back = self.timeout_back
        self.event_timeout_back = lambda *args, **kwargs: self.hide()

    def check_visibility(self):
        if self.timeout_back > 1:
            self.timeout_back = self.timeout_back - 1
            self.lbl_timeout_back.setText(str(self.timeout_back))
        else:
            self.timeout_back = self.__timeout_back
            self.lbl_timeout_back.setText(str(self.timeout_back))
            self.event_timeout_back("timeout_back")

    def showEvent(self, event):
        print(f"screen_11_tool_issued showEvent. event: {event}")
        """Событие, которое срабатывает, когда виджет показывается."""
        super().showEvent(event)
        self.visibility_timer.start(1000)
        self.timeout_back = self.__timeout_back

    def hideEvent(self, event):
        logger.debug("screen_11_tool_issued hideEvent. event: %s", event)
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back
    def set_data(self, *args, **kwargs):
        logger.debug("screen_11_tool_issued set_data. args: %s, kwargs: %s", args, kwargs)
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        logger.debug("screen_11_tool_issued get_data")
        pass