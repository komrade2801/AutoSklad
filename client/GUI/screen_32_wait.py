from PyQt5.QtCore import QTimer
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget
# from BarcodeScanner.SerialWorker import SerialWorker  # Используем новый класс!
from GUI.BaseScreen import BaseScreen
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

        # 🔹 Таймер для отслеживания видимости экрана
        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)

        # 🔹 Таймер для возврата назад
        self.timeout_back = int(self.lbl_timeout_back.text())
        self.__timeout_back = self.timeout_back
        self.event_timeout_back = lambda *args, **kwargs: self.hide()

        # 🔹 Обработчик данных из COM-порта
        self.on_serial_data_received = lambda *args, **kwargs: print(*args, **kwargs)  # self.hide()


    def check_visibility(self):
        """Уменьшает счетчик таймера и скрывает экран, если время истекло"""
        if self.timeout_back > 1:
            self.timeout_back -= 1
            self.lbl_timeout_back.setText(str(self.timeout_back))
        else:
            self.timeout_back = self.__timeout_back
            self.lbl_timeout_back.setText(str(self.timeout_back))
            self.event_timeout_back("timeout_back")

    def showEvent(self, event):
        """Запускается при показе экрана"""
        super().showEvent(event)
        self.visibility_timer.start(1000)
        self.timeout_back = self.__timeout_back

        # 🔹 Запускаем поток чтения COM-порта

    def hideEvent(self, event):
        """Запускается при скрытии экрана"""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back

        # 🔹 Останавливаем поток, если экран скрывается

    def on_serial_error(self, error_msg):
        """Обрабатывает ошибки COM-порта"""
        print(f"Ошибка последовательного порта: {error_msg}")

    def closeEvent(self, event):
        """Закрытие окна — останавливаем поток"""
        event.accept()

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        return {'trigger': 'command_ok'}
