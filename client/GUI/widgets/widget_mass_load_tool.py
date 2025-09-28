from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen
from ..widgets.ui_classes.widget_15_mass_load import Ui_widget_15_mass_load as Ui


class WidgetMassLoadTool(BaseScreen, Ui):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(440, 75)

    def set_data(self, cell_data):
        print("WidgetMassLoadTool set_data")
        print(cell_data)
        """Устанавливает текстовые данные для отображения."""
        for key, value in cell_data.items():
            print(f"trying to set {key} to {value}")
            # Проверяем, существует ли атрибут с таким именем
            if hasattr(self, key):
                print(f"set {key} to {value}")

                widget = getattr(self, key)  # Получаем атрибут
                # Проверяем, имеет ли атрибут метод `setText`
                if hasattr(widget, 'setText') and callable(widget.setText):
                    widget.setText(str(value))  # Устанавливаем текстовое значение
                else:
                    print(f"Предупреждение: атрибут '{key}' не поддерживает setText")
            else:
                print(f"Предупреждение: атрибут '{key}' не найден в {self.__class__.__name__}")

    def get_data(self):
        pass