from PyQt5 import QtCore, QtGui

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_36_hardware_err import Ui_screen_36_hardware_err


class screen_36_hardware_err(BaseScreen, Ui_screen_36_hardware_err):
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
        detail = (kwargs.get("hardware_last_error") or "").strip()
        if not detail and args:
            first = args[0]
            if isinstance(first, dict):
                detail = (first.get("hardware_last_error") or "").strip()
        if not detail:
            parent = self.window()
            executor = getattr(parent, "executor", None)
            if executor is not None:
                detail = (getattr(executor, "hardware_last_error", "") or "").strip()
        if detail:
            self.lbl_body.setText(
                "Контроллер не прошел проверку связи или не завершил калибровку/парковку.\n\n"
                f"{detail}"
            )

    def get_data(self):
        return None
