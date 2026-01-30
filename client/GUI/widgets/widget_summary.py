import datetime
from Core.app_logging import get_logger
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_widget_27_summary import Ui_widget_27_summary as Ui


class WidgetSummary(BaseScreen, Ui):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)


    def set_data(self, *args, **kwargs):
        """
        Универсальная функция для установки значений атрибутов интерфейса.
        Обрабатывает именованные параметры (**kwargs) и автоматически находит
        соответствующие атрибуты класса, устанавливая значения через `setText`.

        :param args: Позиционные аргументы (резерв для будущего использования).
        :param kwargs: Именованные параметры, где ключи — имена атрибутов, а значения — данные для установки.
        """
        # Игнорируем *args, если они не нужны
        for key, value in kwargs.items():
            if key == 'datetime' and isinstance(value, datetime.datetime):
                value = value.strftime("%H:%M %d.%m.%Y")
            # Проверяем, существует ли атрибут с таким именем
            if hasattr(self, key):

                widget = getattr(self, key)  # Получаем атрибут
                # Проверяем, имеет ли атрибут метод `setText`
                if hasattr(widget, 'setText') and callable(widget.setText):
                    widget.setText(str(value))  # Устанавливаем текстовое значение
                else:
                    logger.warning("Предупреждение: атрибут '%s' не поддерживает setText", key)
            else:
                logger.warning("Предупреждение: атрибут '%s' не найден в %s", key, self.__class__.__name__)

    def get_data(self):
        pass

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(440, 154)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши на виджет."""
        super().mousePressEvent(event)  # Сохраняем стандартное поведение
        self.widget_clicked.emit()  # Генерируем сигнал клика по виджету
