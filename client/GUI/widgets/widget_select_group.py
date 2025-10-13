from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from ..BaseScreen import BaseScreen
from .ui_classes.Ui_widget_select_group import Ui_widget_select_group


class WidgetSelectGroup(BaseScreen, Ui_widget_select_group):
    key_pressed = pyqtSignal(str)
    widget_clicked = pyqtSignal()  # Сигнал для кликов по виджету

    def __init__(self, trigger):
        super().__init__()
        self.setupUi(self)
        self.name = ""
        self.id = -1
        self.event_select_group = lambda *args, **kwargs: print(*args, **kwargs)
        self.event_management_group = lambda *args, **kwargs: print(*args, **kwargs)
        self.trigger_name = trigger
        # self.setStyleSheet("border: 2px solid #0078D7; border-radius: 10px; background-color: #f0f0f0;")
    def emit_key(self, key):
        """Вызывается при нажатии на кнопку."""
        self.key_pressed.emit(key)

    def set_data(self, group):
        """Устанавливает текстовые данные для отображения."""
        try:
            self.lbl_name.setText(group.name)
            self.name = group.name
            self.id = group.id
            # Устанавливаем размер кнопки для автоматической подстройки
            self.lbl_name.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        except:
            self.lbl_name.setText(group['name'])
            self.name = group['name']
            self.id = group['id']
            # Устанавливаем размер кнопки для автоматической подстройки
            self.lbl_name.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        # Обработка клика
        # self.lbl_name.clicked.connect(lambda: self.emit_key(str(group['id'])))

    def get_data(self):
        pass

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        print(f"sizeHint: {self.width()}, {self.height()}")
        return QtCore.QSize(self.width(), self.height())

    def mousePressEvent(self, event):
        """Обработка нажатия мыши на виджет."""
        super().mousePressEvent(event)  # Сохраняем стандартное поведение
        self.widget_clicked.emit()  # Генерируем сигнал клика по виджету
        self.event_select_group((self.id, self.name), self.trigger_name)

