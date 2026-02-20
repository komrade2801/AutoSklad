from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from Core.app_logging import get_logger
from ..BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_widget_17_mass_drop import Ui_widget_17_mass_drop as Ui


class WidgetMassDropTool(BaseScreen, Ui):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tools_name.setWordWrap(True)
        self.tools_name.setMaximumHeight(40)

    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(440, 75)

    def set_data(self, cell_data):
        logger.debug("WidgetMassDropTool set_data cell_data=%s", cell_data)
        """Устанавливает текстовые данные для отображения."""
        for key, value in cell_data.items():
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
