from PyQt5 import QtCore, QtGui
from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_32_wait import Ui_screen_32_wait


class screen_32_wait(BaseScreen, Ui_screen_32_wait):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 🔹 Создаем анимацию GIF
        self.gif_movie = QtGui.QMovie("GUI/img/VAyR.gif")
        self.lbl_gif.setMovie(self.gif_movie)
        self.gif_movie.setScaledSize(QtCore.QSize(250, 250))
        self.gif_movie.start()

        # 🔹 Обработчик данных из COM-порта
        self.on_serial_data_received = lambda *args, **kwargs: logger.debug("serial_data %s %s", args, kwargs)

    def showEvent(self, event):
        """Запускается при показе экрана"""
        super().showEvent(event)

    def hideEvent(self, event):
        """Запускается при скрытии экрана"""
        super().hideEvent(event)

    def on_serial_error(self, error_msg):
        """Обрабатывает ошибки COM-порта"""
        logger.error("Ошибка последовательного порта: %s", error_msg)

    def closeEvent(self, event):
        """Закрытие окна — останавливаем поток"""
        event.accept()

    def set_data(self, *args, **kwargs):
        """Подпись ожидания: «Парковка…», «Тестовая выдача…» или стандартная выдача."""
        message = kwargs.get("wait_screen_message")
        if not message and args:
            first = args[0]
            if isinstance(first, dict):
                message = first.get("wait_screen_message")
        if not message:
            parent = self.window()
            executor = getattr(parent, "executor", None)
            if executor is not None:
                message = getattr(executor, "wait_screen_message", "") or ""
        if message:
            self.lbl_info_1.setText(str(message))
        else:
            self.lbl_info_1.setText("Выдача инструмента")

    def get_data(self):
        return None
