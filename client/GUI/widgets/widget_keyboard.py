from PyQt5.QtCore import pyqtSignal

from ..BaseScreen import BaseScreen
from .ui_classes.Ui_widget_3_29_keyboard import Ui_widget_3_29_keyboard


class WidgetKeyboard(BaseScreen, Ui_widget_3_29_keyboard):
    key_pressed = pyqtSignal(str)  # Сигнал, передающий символ нажатой клавиши

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # Настройка кнопок клавиатуры (пример)
        # Например, self.button_a.clicked.connect(lambda: self.key_pressed.emit('a'))
        # Настройка кнопок клавиатуры
        # self.btn_number_0.clicked.connect(lambda: self.key_pressed.emit('0'))
        # self.btn_number_1.clicked.connect(lambda: self.key_pressed.emit('1'))
        # self.btn_number_2.clicked.connect(lambda: self.key_pressed.emit('2'))
        # self.btn_number_3.clicked.connect(lambda: self.key_pressed.emit('3'))
        # self.btn_number_4.clicked.connect(lambda: self.key_pressed.emit('4'))
        # self.btn_number_5.clicked.connect(lambda: self.key_pressed.emit('5'))
        # self.btn_number_6.clicked.connect(lambda: self.key_pressed.emit('6'))
        # self.btn_number_7.clicked.connect(lambda: self.key_pressed.emit('7'))
        # self.btn_number_8.clicked.connect(lambda: self.key_pressed.emit('8'))
        # self.btn_number_9.clicked.connect(lambda: self.key_pressed.emit('9'))
        # self.btn_close.clicked.connect(lambda: self.key_pressed.emit('9'))

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass