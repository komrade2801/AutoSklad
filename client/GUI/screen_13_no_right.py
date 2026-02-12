from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_13_no_right import Ui_screen_13_no_right
from PyQt5.QtCore import QEvent, QTimer


class screen_13_no_right(BaseScreen, Ui_screen_13_no_right):
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
        """Событие, которое срабатывает, когда виджет показывается."""
        super().showEvent(event)
        self.timeout_back = self.__timeout_back
        self.lbl_timeout_back.setText(str(self.timeout_back))
        self.visibility_timer.start(1000)

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back
    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass
