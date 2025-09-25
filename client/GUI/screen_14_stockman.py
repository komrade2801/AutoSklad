import traceback

from PyQt5 import QtCore
from GUI.BaseScreen import BaseScreen
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
            print("Включаю реле на 15 секунд")
            GPIO.output(relay_pin, GPIO.HIGH)
            time.sleep(15)
            print("Выключаю реле")
            GPIO.output(relay_pin, GPIO.LOW)
        elif command == "2":
            print("Выключаю реле")
            GPIO.output(relay_pin, GPIO.LOW)
        else:
            print("Неверная команда. Используйте 1 - Включить, 2 - Выключить")
    except Exception as e:
        print(e)


class screen_14_stockman(BaseScreen, Ui_screen_14_stockman):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

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
        self.event_enter_barcode = lambda barcode: print(
            "Получен штрих-код:", barcode)
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
        print(
            # :contentReference[oaicite:1]{index=1}
            "Кнопка «Открыть дверь» нажата!")
        # TODO Перенести в основную логику программы
        # Настройка режима нумерации пинов (BCM)

        control_rely("1")

    def close_door(self):
        """
        Это метод-обработчик (слот), который вызовется
        при каждом клике по btn_open_door.
        Здесь реализуйте логику открытия двери.
        """
        print(
            # :contentReference[oaicite:1]{index=1}
            "Кнопка «Открыть дверь» нажата!")
        # TODO Перенести в основную логику программыц
        # Настройка режима нумерации пинов (BCM)

        control_rely("2")

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        try:
            for arg in args:
                if isinstance(arg, dict):
                    if "user_name" in arg:
                        full = arg["user_name"].split(" ", 2)
                        if len(full) >= 2:
                            self.lbl_name.setText(f"{full[0]} {full[1]}")
                            self.lbl_name_2.setText(
                                f"{full[2]}" if len(full) > 2 else "")
                elif isinstance(arg, str) and arg.strip():
                    full = arg.split(" ")
                    if len(full) >= 2:
                        self.lbl_name.setText(f"{full[0]} {full[1]}")
                        self.lbl_name_2.setText(f"{full[2]}")
        except Exception as e:
            print(f"Ошибка в set_data stockman: {e}")
            print(traceback.format_exc())

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
        if self._barcode_buffer:
            self.event_enter_barcode({'barcode': self._barcode_buffer})
            self._barcode_buffer = ""
