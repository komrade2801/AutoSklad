import traceback

from Core.app_logging import get_logger
from PyQt5 import QtGui, QtCore, QtWidgets
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_6_user import Ui_screen_6_user
from GUI.ico.ico_avatar import Avatar

class screen_6_user(BaseScreen, Ui_screen_6_user):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.update_icon()  # Вызов метода для обновления иконки

        # Устанавливаем политику фокуса для приема всех событий клавиатуры
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        # Таймер для проверки видимости
        self.visibility_timer = QtCore.QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.timeout_back = int(self.lbl_timeout_back.text())
        self.__timeout_back = self.timeout_back
        self.event_timeout_back = lambda *args, **kwargs: self.hide()

        # Атрибуты для обработки ввода штрих-кода
        self._barcode_buffer = ""
        self._barcode_timer = QtCore.QTimer(self)
        self._barcode_timer.setInterval(1500)  # 1500 мс - увеличенный таймаут как fallback
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.timeout.connect(self._process_barcode)
        self.event_enter_barcode = lambda barcode: logger.debug("Получен штрих-код: %s", barcode)

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
        # Устанавливаем фокус на виджет для приема всех событий клавиатуры
        self.setFocus()
        # Отключаем фокус у всех кнопок, чтобы пробел не активировал их
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setFocusPolicy(QtCore.Qt.NoFocus)
        # Запуск таймера для обработки ввода штрих-кода (fallback на случай, если Enter не придет)
        self._barcode_timer.start()

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back
        # Остановка таймера для обработки ввода штрих-кода
        self._barcode_timer.stop()

    def keyPressEvent(self, event):
        # Обработка Enter/Return - основной механизм завершения ввода QR-кода
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            if self._barcode_buffer:
                self._barcode_timer.stop()  # Останавливаем таймер
                logger.debug("[QR] Enter нажат, обработка буфера: %s", repr(self._barcode_buffer))
                self._process_barcode()  # Немедленно обрабатываем
            event.accept()  # Явно принимаем событие
            return

        # ВАЖНО: Обрабатываем Tab как обычный символ для QR-кода, а не как навигацию
        if event.key() == QtCore.Qt.Key_Tab:
            # Добавляем табуляцию в буфер
            self._barcode_buffer += '\t'
            logger.debug("[QR] Добавлен Tab, буфер: %s", repr(self._barcode_buffer))
            # Перезапускаем таймер как fallback
            self._barcode_timer.start()
            event.accept()  # Явно принимаем событие, чтобы предотвратить стандартную обработку Tab
            return  # Предотвращаем стандартную обработку Tab (переключение фокуса)

        # ВАЖНО: Обрабатываем пробел (Space) явно, чтобы он не активировал кнопки
        if event.key() == QtCore.Qt.Key_Space:
            # Добавляем пробел в буфер
            self._barcode_buffer += ' '
            logger.debug("[QR] Добавлен пробел, буфер: %s", repr(self._barcode_buffer))
            # Перезапускаем таймер как fallback
            self._barcode_timer.start()
            event.accept()  # Явно принимаем событие, чтобы предотвратить активацию кнопок
            return  # Предотвращаем стандартную обработку пробела (активация кнопки)

        # Принимаем ЛЮБОЙ символ (не только цифры) для поддержки QR-кодов с буквами, пробелами, табуляциями
        if event.text():
            self._barcode_buffer += event.text()
            # Перезапускаем таймер как fallback
            self._barcode_timer.start()
            logger.debug("[QR] Добавлен символ: %s, буфер: %s", repr(event.text()), repr(self._barcode_buffer))
            event.accept()  # Явно принимаем событие

    def _process_barcode(self):
        logger.debug("[QR] _process_barcode buffer: %s", repr(self._barcode_buffer))
        if self._barcode_buffer:
            # Очищаем буфер от завершающих символов (\n, \r)
            cleaned_buffer = self._barcode_buffer.strip()
            if cleaned_buffer:
                barcode = {'barcode': cleaned_buffer}
                logger.debug("[QR] Отправка штрих-кода: %s", repr(cleaned_buffer))
                self._barcode_buffer = ""
                self.event_enter_barcode(barcode)
            else:
                logger.debug("[QR] Буфер пуст после очистки, пропуск")
                self._barcode_buffer = ""

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
                    logger.debug("user: %s", user)
                    self.lbl_name.setText(f"{user.first_name} {user.second_name}")
                    self.lbl_name_2.setText(f"{user.family}")
                    continue

            except Exception:
                logger.exception("screen_6_user set_data")

    def get_data(self):
        logger.debug("get_data Before clear: %s", self._barcode_buffer)
        self._barcode_buffer = ""
        pass
