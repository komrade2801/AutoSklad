# -*- coding: utf-8 -*-
"""
Глобальный таймер неактивности сессии.
- 300 секунд до сброса авторизации и возврата на screen_1_welcome
- Всплывающее окно показывается только в последние 15 секунд
- Таймер сбрасывается при любом действии пользователя (клик, касание, клавиша)
"""

from PyQt5.QtCore import QTimer, QObject, QEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import Qt

from Core.app_logging import get_logger

logger = get_logger(__name__)

TOTAL_SECONDS = 60
WARNING_THRESHOLD = 15


class SessionIdleManager(QObject):
    """Менеджер глобального таймера неактивности сессии."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self._main_window = main_window
        self._remaining_seconds = TOTAL_SECONDS
        self._is_active = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._popup = None
        self._popup_label = None
        self._create_popup()

    def _create_popup(self):
        """Создаёт всплывающее окно предупреждения."""
        self._popup = QDialog(self._main_window)
        self._popup.setWindowFlags(
            Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self._popup.setMinimumSize(350, 120)
        self._popup.setStyleSheet(
            "background-color: #2e4461; color: #FFFFFF; "
            "border: 2px solid #CAE2FF; border-radius: 8px; "
            "padding: 20px; font-size: 18px;"
        )
        layout = QVBoxLayout(self._popup)
        self._popup_label = QLabel(self._popup)
        self._popup_label.setAlignment(Qt.AlignCenter)
        self._popup_label.setWordWrap(True)
        layout.addWidget(self._popup_label)

    def _update_popup_text(self):
        """Обновляет текст в диалоге."""
        self._popup_label.setText(
            f"Сессия истечёт через {self._remaining_seconds} сек.\n"
            "Нажмите экран для продления."
        )

    def _show_popup(self):
        """Показывает диалог по центру главного окна."""
        if not self._popup or not self._main_window:
            return
        self._update_popup_text()
        # Центрирование относительно MainWindow
        mw = self._main_window
        pw = self._popup
        x = mw.x() + (mw.width() - pw.width()) // 2
        y = mw.y() + (mw.height() - pw.height()) // 2
        pw.move(x, y)
        pw.show()

    def _hide_popup(self):
        """Скрывает диалог."""
        if self._popup:
            self._popup.hide()

    def start(self):
        """Запускает таймер сессии."""
        self._remaining_seconds = TOTAL_SECONDS
        self._is_active = True
        self._hide_popup()
        self._timer.start()
        logger.debug("SessionIdleManager: started")

    def stop(self):
        """Останавливает таймер сессии."""
        self._is_active = False
        self._timer.stop()
        self._hide_popup()
        logger.debug("SessionIdleManager: stopped")

    def reset_timer(self):
        """Сбрасывает таймер при активности пользователя."""
        if not self._is_active:
            return
        self._remaining_seconds = TOTAL_SECONDS
        if self._remaining_seconds > WARNING_THRESHOLD:
            self._hide_popup()
        else:
            self._hide_popup()

    def _tick(self):
        """Вызывается каждую секунду."""
        if not self._is_active:
            return
        self._remaining_seconds -= 1

        if self._remaining_seconds <= 0:
            self.stop()
            logger.info("SessionIdleManager: session expired, returning to welcome")
            self._main_window.button_clicked("timeout_back", None)
            return

        if self._remaining_seconds <= WARNING_THRESHOLD:
            self._update_popup_text()
            if not self._popup.isVisible():
                self._show_popup()
        else:
            self._hide_popup()

    def eventFilter(self, obj, event):
        """Перехватывает события для сброса таймера при активности."""
        if not self._is_active:
            return False

        event_type = event.type()
        activity_events = (
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseButtonDblClick,
            QEvent.KeyPress,
            QEvent.TouchBegin,
            QEvent.TouchUpdate,
            QEvent.TouchEnd,
        )
        if event_type in activity_events:
            self.reset_timer()
        return False
