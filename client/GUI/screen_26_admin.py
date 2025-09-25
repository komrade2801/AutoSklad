import traceback

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QEvent

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_26_admin import Ui_screen_26_admin


class screen_26_admin(BaseScreen, Ui_screen_26_admin):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.__is_read = False
        self.__is_write = True
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
        self.visibility_timer.start(1000)
        self.timeout_back = self.__timeout_back

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        print(f"set_data. Input args: {args}")
        for arg in args:
            try:
                print(f"set_data. arg: {arg}")
                if not arg:
                    continue
                if isinstance(arg, tuple):
                    user = arg[0]
                    print(f"user: {user}")
                    self.lbl_name.setText(f"{user.first_name} {user.second_name}")
                    self.lbl_name_2.setText(f"{user.family}")
                    continue

            except:
                print(traceback.format_exc())


    def get_data(self):
        pass
