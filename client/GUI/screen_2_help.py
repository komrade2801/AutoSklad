from Core.app_logging import get_logger
from DB.Models.Help import Help
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_2_help import Ui_screen_2_help
from PyQt5.QtCore import QEvent


class screen_2_help(BaseScreen, Ui_screen_2_help):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.__is_read = False
        self.__is_write = True
        self.index = 0

    def get_data(self):
        return self.index

    def set_data(self, data, source):
        logger.debug("set_data Input data: %s, source: %s", data, source)
        if isinstance(data, Help):
            self.text_window.setText(data.text)

    def is_read(self):
        return self.__is_read

    def is_write(self):
        return self.__is_write
