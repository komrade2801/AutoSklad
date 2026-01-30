import traceback

from Core.app_logging import get_logger
from PyQt5 import QtCore
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_14_stockman import Ui_screen_14_stockman
try:
    import RPi.GPIO as GPIO
except Exception:
    from Compat import gpio_stub as GPIO
import time

GPIO.setmode(GPIO.BCM)

# Номер пина GPIO для реле двери (18)
relay_pin = 18

GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.LOW)


def control_rely(command):
    try:
        if command == "1":
            logger.info("Включаю реле на 15 секунд")
            GPIO.output(relay_pin, GPIO.HIGH)
            time.sleep(15)
            logger.info("Выключаю реле")
            GPIO.output(relay_pin, GPIO.LOW)
        elif command == "2":
            logger.info("Выключаю реле")
            GPIO.output(relay_pin, GPIO.LOW)
        else:
            logger.warning("Неверная команда. Используйте 1 - Включить, 2 - Выключить")
    except Exception as e:
        logger.exception("control_rely: %s", e)


class screen_14_stockman(BaseScreen, Ui_screen_14_stockman):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

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
        # :contentReference[oaicite:0]{index=0}
        self.btn_open_door.clicked.connect(self.on_open_door)
        # :contentReference[oaicite:0]{index=0}
        self.btn_back.clicked.connect(self.close_door)

    def on_open_door(self):
        """
        Это метод-обработчик (слот), который вызовется
        при каждом клике по btn_open_door.
        Здесь реализуйте логику открытия двери.
        """
        logger.debug("Кнопка «Открыть дверь» нажата!")
        # TODO Перенести в основную логику программы
        control_rely("1")

    def close_door(self):
        """
        Это метод-обработчик (слот), который вызовется
        при каждом клике по btn_open_door.
        Здесь реализуйте логику открытия двери.
        """
        logger.debug("Кнопка «Закрыть дверь» нажата")
        # TODO Перенести в основную логику программыц
        # Настройка режима нумерации пинов (BCM)

        control_rely("2")

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        logger.debug("set_data Input args: %s", args)
        for arg in args:
            try:
                logger.debug("set_data arg: %s", arg)
                if not arg:
                    continue
                if isinstance(arg, tuple):
                    user = arg[0]
                    logger.debug("user as tuple: %s", user)
                    self.lbl_name.setText(f"{user.first_name} {user.second_name}")
                    self.lbl_name_2.setText(f"{user.family}")
                elif isinstance(arg, str) and arg.strip():
                    print(f"user as str: {arg}")
                    full = arg.split(" ")
                    if len(full) >= 2:
                        self.lbl_name.setText(f"{full[0]} {full[1]}")
                        self.lbl_name_2.setText(f"{full[2]}")

            except Exception as e:
                logger.exception("Ошибка в set_data stockman: %s", e)

    def get_data(self):
        pass

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
        from PyQt5 import QtWidgets
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
            print(f"[QR] Добавлен символ: {repr(event.text())}, буфер: {repr(self._barcode_buffer)}")
            event.accept()  # Явно принимаем событие

    def _process_barcode(self):
        logger.debug("[QR] _process_barcode buffer: %s", repr(self._barcode_buffer))
        if self._barcode_buffer:
            # Очищаем буфер от завершающих символов (\n, \r)
            cleaned_buffer = self._barcode_buffer.strip()
            if cleaned_buffer:
                logger.debug("[QR] Отправка штрих-кода: %s", repr(cleaned_buffer))
                self.event_enter_barcode({'barcode': cleaned_buffer})
                self._barcode_buffer = ""
            else:
                logger.debug("[QR] Буфер пуст после очистки, пропуск")
                self._barcode_buffer = ""
