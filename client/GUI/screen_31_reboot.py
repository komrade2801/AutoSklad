import traceback
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_31_reboot import Ui_screen_31_reboot
from PyQt5.QtCore import QEvent, QTimer


class screen_31_reboot(BaseScreen, Ui_screen_31_reboot):
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
            self.lbl_info_3.setText(f"Перезагрузить через {self.confirmation_countdown} сек?")
        else:
            # Автоматическое подтверждение
            self.confirmation_timer.stop()
            self.is_confirmed = True
            self._execute_reboot()

    def _on_ok_clicked(self):
        """Подтверждение перезагрузки"""
        if not self.is_confirmed:
            # Первое нажатие - запускаем таймер обратного отсчета
            self.is_confirmed = True
            self.confirmation_timer.start(1000)  # Каждую секунду
            self.btn_ok.setEnabled(False)  # Блокируем кнопку до завершения
            self._on_confirmation_timeout()  # Сразу обновляем текст
        else:
            # Второе нажатие - немедленная перезагрузка
            self.confirmation_timer.stop()
            self._execute_reboot()

    def _on_back_clicked(self):
        """Отмена перезагрузки"""
        self.confirmation_timer.stop()
        self.is_confirmed = False
        self.confirmation_countdown = 5
        self.lbl_info_3.setText("Перезагрузить?")
        return {'trigger': 'btn_back'}

    def _execute_reboot(self):
        """Выполнение команды перезагрузки"""
        try:
            # Команда будет выполнена через state machine -> cmd_reboot
            print("Выполняется перезагрузка системы...")
            return {'trigger': 'btn_ok'}
        except Exception as e:
            print(f"Ошибка при перезагрузке: {e}")
            traceback.print_exc()
            return {'trigger': 'error'}

    def showEvent(self, event):
        """Событие, которое срабатывает, когда виджет показывается"""
        super().showEvent(event)
        self.is_confirmed = False
        self.confirmation_countdown = 5
        self.lbl_info_3.setText("Перезагрузить?")
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
        self.lbl_info_3.setText("Перезагрузить?")

    def get_data(self):
        """Возвращает данные с экрана"""
        pass
