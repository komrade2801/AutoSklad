import traceback

from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_30_shutdown import Ui_screen_30_shutdown
from PyQt5.QtCore import QEvent, QTimer


class screen_30_shutdown(BaseScreen, Ui_screen_30_shutdown):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.confirmation_timer = QTimer(self)
        self.confirmation_timer.timeout.connect(self._on_confirmation_timeout)
        self.confirmation_countdown = 5  # Секунд до автоматического подтверждения
        self.is_confirmed = False
        
        self._setup_ui_connections()

    def _setup_ui_connections(self):
        """Подключение обработчиков событий"""
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        self.btn_back.clicked.connect(self._on_back_clicked)

    def _on_confirmation_timeout(self):
        """Обработка таймера обратного отсчета"""
        if self.confirmation_countdown > 0:
            self.confirmation_countdown -= 1
            # Обновляем текст с оставшимся временем
            self.lbl_info_3.setText(f"Выключить через {self.confirmation_countdown} сек?")
        else:
            # Автоматическое подтверждение
            self.confirmation_timer.stop()
            self.is_confirmed = True
            self._execute_shutdown()

    def _on_ok_clicked(self):
        """Подтверждение выключения"""
        if not self.is_confirmed:
            # Первое нажатие - запускаем таймер обратного отсчета
            self.is_confirmed = True
            self.confirmation_timer.start(1000)  # Каждую секунду
            self.btn_ok.setEnabled(False)  # Блокируем кнопку до завершения
            self._on_confirmation_timeout()  # Сразу обновляем текст
        else:
            # Второе нажатие - немедленное выключение
            self.confirmation_timer.stop()
            self._execute_shutdown()

    def _on_back_clicked(self):
        """Отмена выключения"""
        self.confirmation_timer.stop()
        self.is_confirmed = False
        self.confirmation_countdown = 5
        self.lbl_info_3.setText("Выключить?")
        return {'trigger': 'btn_back'}

    def _execute_shutdown(self):
        """Выполнение команды выключения"""
        try:
            # Команда будет выполнена через state machine -> cmd_stop
            logger.info("Выполняется выключение системы...")
            return {'trigger': 'btn_ok'}
        except Exception as e:
            logger.exception("Ошибка при выключении: %s", e)
            return {'trigger': 'error'}

    def showEvent(self, event):
        """Событие, которое срабатывает, когда виджет показывается"""
        super().showEvent(event)
        self.is_confirmed = False
        self.confirmation_countdown = 5
        self.lbl_info_3.setText("Выключить?")
        self.btn_ok.setEnabled(True)

    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается"""
        super().hideEvent(event)
        self.confirmation_timer.stop()
        self.is_confirmed = False
        self.confirmation_countdown = 5

    def set_data(self, *args, **kwargs):
        """Устанавливает данные при переходе на экран"""
        self.is_confirmed = False
        self.confirmation_countdown = 5
        self.lbl_info_3.setText("Выключить?")

    def get_data(self):
        """Возвращает данные с экрана"""
        pass
