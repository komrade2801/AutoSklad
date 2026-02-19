import traceback
from Core.app_logging import get_logger

from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_26_admin import Ui_screen_26_admin


class screen_26_admin(BaseScreen, Ui_screen_26_admin):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.__is_read = False
        self.__is_write = True

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        logger.debug("set_data. Input args: %s", args)
        for arg in args:
            try:
                logger.debug("set_data. arg: %s", arg)
                if not arg:
                    continue
                if isinstance(arg, tuple):
                    user = arg[0]
                    logger.debug("user: %s", user)
                    self.lbl_name.setText(f"{user.second_name}")
                    self.lbl_name_2.setText(f"{user.first_name[0]}.{user.family[0]}.")
                    continue

            except Exception:
                logger.exception("screen_26_admin set_data")


    def get_data(self):
        pass
