import traceback

from Core.app_logging import get_logger
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
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

# Длительность активации реле в секундах
RELAY_DURATION = 15


class RelayWorker(QThread):
    """Рабочий поток для управления реле без блокировки GUI."""
    finished = pyqtSignal()

    def __init__(self, duration=RELAY_DURATION):
        super().__init__()
        self.duration = duration

    def run(self):
        try:
            logger.info("Включаю реле на %d секунд", self.duration)
            GPIO.output(relay_pin, GPIO.HIGH)
            time.sleep(self.duration)
            logger.info("Выключаю реле")
            GPIO.output(relay_pin, GPIO.LOW)
        except Exception as e:
            logger.exception("RelayWorker: %s", e)
        finally:
            self.finished.emit()


def control_relay_off():
    """Немедленно выключить реле."""
    try:
        logger.info("Выключаю реле")
        GPIO.output(relay_pin, GPIO.LOW)
    except Exception as e:
        logger.exception("control_relay_off: %s", e)


class screen_14_stockman(BaseScreen, Ui_screen_14_stockman):
    # Стиль кнопки в активном состоянии (зелёный фон)
    BUTTON_STYLE_ACTIVE = """
        QPushButton {
            background-color: #4CAF50;
            border: 2px solid #388E3C;
            border-radius: 5px;
        }
        QPushButton:disabled {
            background-color: #4CAF50;
            border: 2px solid #388E3C;
        }
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Устанавливаем политику фокуса для приема всех событий клавиатуры
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Атрибуты для обработки ввода штрих-кода
        self._barcode_buffer = ""
        self._barcode_timer = QtCore.QTimer(self)
        self._barcode_timer.setInterval(1500)  # 1500 мс - увеличенный таймаут как fallback
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.timeout.connect(self._process_barcode)
        self.event_enter_barcode = lambda barcode: logger.debug("Получен штрих-код: %s", barcode)

        # Рабочий поток для реле
        self._relay_worker = None
        # Сохраняем оригинальный стиль кнопки
        self._btn_open_door_original_style = self.btn_open_door.styleSheet()

        self.btn_open_door.clicked.connect(self.on_open_door)
        self.btn_back.clicked.connect(self.close_door)

    def on_open_door(self):
        """
        Обработчик нажатия кнопки открытия двери.
        Запускает реле в отдельном потоке, не блокируя GUI.
        """
        # Игнорируем повторные нажатия, пока реле активно
        if self._relay_worker and self._relay_worker.isRunning():
            logger.debug("Реле уже активно, игнорируем повторное нажатие")
            return

        logger.debug("Кнопка «Открыть дверь» нажата!")

        # Деактивируем кнопку и меняем её стиль на зелёный
        self.btn_open_door.setEnabled(False)
        self.btn_open_door.setStyleSheet(self.BUTTON_STYLE_ACTIVE)

        # Запускаем рабочий поток для управления реле
        self._relay_worker = RelayWorker(RELAY_DURATION)
        self._relay_worker.finished.connect(self._on_relay_finished)
        self._relay_worker.start()

    def _on_relay_finished(self):
        """Вызывается когда реле выключается (поток завершён)."""
        logger.debug("Реле выключено, восстанавливаем кнопку")
        # Восстанавливаем оригинальный стиль и активируем кнопку
        self.btn_open_door.setStyleSheet(self._btn_open_door_original_style)
        self.btn_open_door.setEnabled(True)

    def close_door(self):
        """
        Обработчик нажатия кнопки закрытия/выхода.
        Немедленно выключает реле.
        """
        logger.debug("Кнопка «Закрыть дверь» нажата")
        control_relay_off()

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
                    self.lbl_name.setText(f"{user.family} {user.first_name[0]}. {user.second_name[0]}.")
                elif isinstance(arg, str) and arg.strip():
                    print(f"user as str: {arg}")
                    full = arg.split(" ")
                    if len(full) >= 3:
                        self.lbl_name.setText(f"{full[1]} {full[0][0]}. {full[2][0]}.")

            except Exception as e:
                logger.exception("Ошибка в set_data stockman: %s", e)

    def get_data(self):
        pass

    def showEvent(self, event):
        """Событие, которое срабатывает, когда виджет показывается."""
        super().showEvent(event)
        # Устанавливаем фокус на виджет для приема всех событий клавиатуры
        self.setFocus()
        # Отключаем фокус у всех кнопок, чтобы пробел не активировал их
        from PyQt5 import QtWidgets
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setFocusPolicy(QtCore.Qt.NoFocus)
        # Запуск таймера для обработки ввода штрих-кода (fallback на случай, если Enter не придет)
        self._barcode_timer.start()
        # Проверяем состояние реле при показе экрана
        if self._relay_worker and self._relay_worker.isRunning():
            # Реле ещё активно - показываем зелёную кнопку
            self.btn_open_door.setEnabled(False)
            self.btn_open_door.setStyleSheet(self.BUTTON_STYLE_ACTIVE)
        else:
            # Реле не активно - нормальное состояние
            self.btn_open_door.setStyleSheet(self._btn_open_door_original_style)
            self.btn_open_door.setEnabled(True)

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self._barcode_timer.stop()
        # Восстанавливаем состояние кнопки при скрытии экрана
        if self._relay_worker and self._relay_worker.isRunning():
            # Поток продолжит работу в фоне, но кнопку восстановим
            pass
        self.btn_open_door.setStyleSheet(self._btn_open_door_original_style)
        self.btn_open_door.setEnabled(True)

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
