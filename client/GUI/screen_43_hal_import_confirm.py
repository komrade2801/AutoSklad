from PyQt5 import QtCore

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_43_hal_import_confirm import Ui_screen_43_hal_import_confirm


def _message_from_set_data(args, kwargs) -> str:
    detail = (kwargs.get("message") or "").strip()
    if detail:
        return detail
    if args:
        first = args[0]
        if isinstance(first, dict):
            return (first.get("message") or "").strip()
        if isinstance(first, str):
            return first.strip()
    return ""


class screen_43_hal_import_confirm(BaseScreen, Ui_screen_43_hal_import_confirm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        pixmap = self.lbl_icon.pixmap()
        if pixmap is not None and not pixmap.isNull():
            self.lbl_icon.setPixmap(
                pixmap.scaled(
                    96,
                    96,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
            )
        self.normalize_screen_geometry()

    def set_data(self, *args, **kwargs):
        detail = _message_from_set_data(args, kwargs)
        if not detail:
            parent = self.window()
            executor = getattr(parent, "executor", None)
            if executor is not None:
                detail = (getattr(executor, "hal_import_message", "") or "").strip()
        if detail:
            self.lbl_body.setText(detail)

    def get_data(self):
        return None
