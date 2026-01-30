from PyQt5 import QtGui, QtCore, QtWidgets
from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_1_welcome import Ui_screen_1_welcome
from GUI.ico.ico_logo import Logo

logger = get_logger(__name__)


class screen_1_welcome(BaseScreen, Ui_screen_1_welcome):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.lbl_info_ico.setPixmap(QtGui.QPixmap(Logo().get_pixmap()))  # Установка пиксмапа
        self.event_enter_barcode = lambda barcode=0: logger.debug("Получен штрих-код: %s", barcode)

        self._barcode_buffer = ""
        self._barcode_timer = QtCore.QTimer()
        self._barcode_timer.setInterval(300)  # 300 мс
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.timeout.connect(self._process_barcode)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            return  # Игнорируем нажатия Enter

        if event.text().isdigit():  # Проверяем, что введена цифра
            self._barcode_buffer += event.text()
            self._barcode_timer.start()  # Перезапускаем таймер при каждом нажатии

    def _process_barcode(self):
        if self._barcode_buffer:
            barcode={'barcode':self._barcode_buffer}
            self.event_enter_barcode(barcode)
            self._barcode_buffer = ""

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        pass

    def get_data(self):
        pass

    def handle_select_group(self, *args, **kwargs):
        self.event_enter_barcode(self.trigger)
