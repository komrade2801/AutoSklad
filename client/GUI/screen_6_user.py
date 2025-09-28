import traceback

from PyQt5 import QtGui, QtCore
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_6_user import Ui_screen_6_user
from GUI.ico.ico_avatar import Avatar

class screen_6_user(BaseScreen, Ui_screen_6_user):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.update_icon()  # Вызов метода для обновления иконки

        # Таймер для проверки видимости
        self.visibility_timer = QtCore.QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.timeout_back = int(self.lbl_timeout_back.text())
        self.__timeout_back = self.timeout_back
        self.event_timeout_back = lambda *args, **kwargs: self.hide()

        # Атрибуты для обработки ввода штрих-кода
        self._barcode_buffer = ""
        self._barcode_timer = QtCore.QTimer(self)
        self._barcode_timer.setInterval(400)  # 400 мс
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.timeout.connect(self._process_barcode)
        self.event_enter_barcode = lambda barcode: print("Получен штрих-код:", barcode)

    def check_visibility(self):
        if self.timeout_back > 1:
            self.timeout_back -= 1
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
        # Запуск таймера для обработки ввода штрих-кода
        self._barcode_timer.start()

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back
        # Остановка таймера для обработки ввода штрих-кода
        self._barcode_timer.stop()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            return  # Игнорируем нажатия Enter

        if event.text().isdigit():  # Проверяем, что введена цифра
            self._barcode_buffer += event.text()
            self._barcode_timer.start()  # Перезапускаем таймер при каждом нажатии

    def _process_barcode(self):
        print(f"_process_barcode. buffer: {self._barcode_buffer}")
        if self._barcode_buffer:
            barcode={'barcode':self._barcode_buffer}
            self._barcode_buffer = ""
            self.event_enter_barcode(barcode)

    def update_icon(self):
        # Установка нового pixmap
        pixmap = QtGui.QPixmap(Avatar().get_pixmap())  # Укажите правильный путь к изображению
        self.lbl_info_ico.setPixmap(pixmap)

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
        print(f"get_data. Before clear: {self._barcode_buffer}")
        self._barcode_buffer = ""
        pass
