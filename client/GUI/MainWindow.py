# -*- coding: utf-8 -*-
# from BarcodeScanner.serial_manager import SerialManager
# from EventsSystem.Executor import Executor
# from EventsSystem.action_selector import ActionSelector
# from EventsSystem.state_router import StateRouter
# from GUI.helper.MyLineEdit import MyLineEdit
# from PyQt5.QtWidgets import QApplication
import os
import sys
import traceback
from typing import Any

import psutil
from PyQt5 import QtWidgets, QtCore

from PyQt5.QtWidgets import QApplication

from Core import platforms
from Core.app_logging import get_logger

logger = get_logger(__name__)
from EventsSystem.events import Hendlers
from GUI.BaseScreen import BaseScreen
from GUI.SessionIdleManager import SessionIdleManager
from StateMachine.NavigationManager import NavigationManager
from StateMachine.state_map import transitions
from StateMachine.screens import screen
from StateMachine.FMS import Maps
from transitions import MachineError
from ui import *


# Класс для управления отображением виджетов
class MainWindowEvent(QtCore.QObject):
    show_widget = QtCore.pyqtSignal(str)


# Настройка перехвата исключений
def exception_hook(exctype, value, tb):
    logger.exception("Необработанное исключение: %s %s", exctype, value)
    sys.__excepthook__(exctype, value, tb)


sys.excepthook = exception_hook


# Главное окно приложения
class MainWindow(QtWidgets.QWidget):
    def __init__(self, maps=None, handler=None):
        super().__init__()

        self.handler = handler or Hendlers()
        self.lump = maps or Maps("screen_1_welcome")
        logger.debug("Initial state: %s", self.lump.state())
        self.current_screen = ""

        self.setWindowTitle("Main Window")
        self.resize(480, 800)
        current_platform = platforms.detect()
        if current_platform == platforms.Raspberry_Pi:
            self.showFullScreen()

        # Словари для хранения виджетов и сигналов кнопок
        self.widgets = {}
        self.button_signals = {}
        self.current_value = {}  # Состояние текущего экрана
        self.back_state = None
        self.value = {}
        # Контекст выдачи: 'by_group' (свободная) или 'by_plan' (по чертежу) — для выбора триггера «Назад»
        self.issue_context = None
        self.ISSUE_BACK_SCREENS = ('screen_10_confirmation', 'screen_11_tool_issued', 'screen_12_no_tool')
        # Экраны с возвратом по запомненной роли: «Назад» — в меню роли (user, admin или stockman)
        self.last_role_screen = None
        self.SUMMARY_BACK_SCREENS = ('screen_21_summary', 'screen_33_select_plan', 'screen_7_select_group', 'screen_9_select_tool_by_plan')
        # # Наш навигационный менеджер
        # self.nav_manager = NavigationManager()

        # Основной layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Создание экранов
        self.create_widgets()
        self.session_manager = SessionIdleManager(self)
        QApplication.instance().installEventFilter(self.session_manager)
        self.last_widget_value = {}
        self.open_widget(self.lump.state(), None, None)
        self.action_callback = None
        # self.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 rgba(47, 70, 105, 255), stop:1 rgba(131, 149, 174, 255));\n""")
        self.setStyleSheet("background-color: #2e4461;")

    def create_widgets(self):
        """Создает виджеты для всех экранов."""
        for screen_name, buttons in screen.items():
            widget = self.create_widget(screen_name)
            widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.widgets[screen_name] = widget
            self.layout.addWidget(widget)
            self.layout.setContentsMargins(0, 0, 0, 0)

        self.bind_transitions()

    def create_widget(self, screen_name):
        """Создаёт и настраивает виджет для конкретного экрана."""
        ui_class = getattr(sys.modules[__name__], screen_name, None)
        if ui_class and issubclass(ui_class, BaseScreen):
            widget = ui_class()
            return widget
        else:
            raise TypeError(f"Экран {screen_name} не наследуется от BaseScreen")

    def find_and_connect_buttons(self, widget):
        """Находит кнопки на виджете и подключает их к сигналам."""
        for button in widget.findChildren(QtWidgets.QPushButton):
            button_name = button.objectName()
            self.button_signals[button_name] = button.clicked

    def bind_transitions(self):
        """Привязывает кнопки к переходам между экранами."""
        for transition in transitions:
            trigger = transition['trigger']
            source = transition['source']
            dest = transition['dest']
            if source in self.widgets:
                self.bind_button_signal(source, trigger, dest)
        # На экранах выдачи одна кнопка «Назад» вызывает контекстный триггер (по группе или по чертежу)
        for source in self.ISSUE_BACK_SCREENS:
            if source not in self.widgets:
                continue
            btn = self.widgets[source].findChild(QtWidgets.QPushButton, "btn_back")
            if btn:
                btn.clicked.connect(self._on_issue_back_clicked)
                self.button_signals[btn.objectName()] = btn.clicked
        # «Назад» — в меню роли (user, admin или stockman) по last_role_screen
        for source in self.SUMMARY_BACK_SCREENS:
            if source not in self.widgets:
                continue
            btn = self.widgets[source].findChild(QtWidgets.QPushButton, "btn_back")
            if btn:
                btn.clicked.connect(self._on_summary_back_clicked)
                self.button_signals[btn.objectName()] = btn.clicked

    def bind_button_signal(self, source, trigger, dest):
        """Привязывает сигнал кнопки к обработчику."""
        # event_timeout_back отключён — используется глобальный SessionIdleManager

        if self.widgets[source].event_input_name_code:
            self.widgets[source].event_input_name_code = (lambda checked, btn_name="input_name_code": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_select_group:
            self.widgets[source].event_select_group = (lambda checked, btn_name="btn_select_group_names": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_select_management_group:
            self.widgets[source].event_select_management_group = (lambda checked, btn_name="btn_warehouse_select_tools": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_select_tool:
            self.widgets[source].event_select_tool = (lambda checked, btn_name="btn_tool_name": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_select_plan:
            self.widgets[source].event_select_plan = (lambda checked, btn_name="btn_plan_name": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_enter_barcode:
            self.widgets[source].event_enter_barcode = (lambda barcode=0, btn_name="barcode": self.button_clicked(btn_name, dest, value=barcode))

        # На экранах выдачи триггеры btn_back_to_* привязаны к одной кнопке btn_back в bind_transitions
        if source in self.ISSUE_BACK_SCREENS and trigger in ("btn_back_to_group", "btn_back_to_plan"):
            return
        # На экранах сводки и выбора плана триггеры btn_back_to_* привязаны к btn_back в bind_transitions
        if source in self.SUMMARY_BACK_SCREENS and trigger in ("btn_back_to_admin", "btn_back_to_stockman", "btn_back_to_user"):
            return
        # На screen_9 виртуальные триггеры btn_back_to_plan_list_* не ищут кнопку по имени
        if source == "screen_9_select_tool_by_plan" and trigger in ("btn_back_to_plan_list_user", "btn_back_to_plan_list_stockman"):
            return
        button = self.widgets[source].findChild(QtWidgets.QPushButton, trigger)
        if button:
            self.button_signals[button.objectName()] = button.clicked
            button_name = button.objectName()
            # if button_name == "btn_back":
            #     button.clicked.connect(lambda checked: self.open_back_widget())
            # else:
            button.clicked.connect(lambda checked, btn_name=button_name: self.button_clicked(btn_name, dest))
            #
            # self.button_signals[button.objectName()] = button.clicked
            # button_name = button.objectName()
            #
            # button.clicked.connect(lambda checked, btn_name=button_name: self.button_clicked(btn_name, dest))

    def handle_controller_serial_response(self, response):
        """Обрабатываем полученный ответ"""
        self.session_manager.reset_timer()
        logger.debug("MainWindow controller_serial получен: %s value=%s", response, self.last_widget_value)
        self.button_clicked(response, None)

    def handle_barcode_manager_response(self, response):
        """Обрабатываем полученный ответ"""
        self.session_manager.reset_timer()
        logger.debug("MainWindow barcode_manager получен: %s value=%s", response, self.last_widget_value)
        self.value['barcode'] = response
        self.button_clicked('barcode', None)


    # def handle_timer_event(self):
    #     """Обрабатываем полученный ответ"""
    #     self.button_clicked('timer_event', None)


    # line_edit = self.widgets[source].findChild(MyLineEdit, "edit_psw")
    # if line_edit:
    #     try:
    #         line_edit.focus_in.disconnect()
    #     except TypeError:
    #         pass  # Если сигнал не подключён, ничего не делаем
    #     line_edit.focus_in.connect(lambda btn_name=trigger: self.button_clicked(btn_name, dest))
    #
    # line_edit = self.widgets[source].findChild(MyLineEdit, "edit_login")
    # if line_edit:
    #     try:
    #         line_edit.focus_in.disconnect()
    #     except TypeError:
    #         pass  # Если сигнал не подключён, ничего не делаем
    #     line_edit.focus_in.connect(lambda btn_name=trigger: self.button_clicked(btn_name, dest))

    def button_clicked(self, button_name: str, dest: str = None, value=0):
        """
        Обрабатывает нажатие кнопки.

        :param button_name: Имя нажатой кнопки.
        :param dest: Целевое состояние (опционально).
        """
        # try:
        if 'timer' in button_name and self.lump.state() != self.lump.machine.initial:
            return

        self.back_state = self.lump.state()
        self.lump.trigger(button_name)
        state = self.lump.state()
        logger.debug("button_clicked button_name=%s state=%s value=%s", button_name, state, self.last_widget_value)
        if state != self.back_state:
            # if 'btn_back' in button_name and self.lump.state() != self.lump.machine.initial:
            #     self.open_back_widget()
            # else:
            self.open_widget(state, button_name, value)
        # except (MachineError, TypeError, AttributeError) as e:
        #     self._handle_button_click_error(e)

    def open_back_widget(self, value: Any = None):
        logger.debug("open_back_widget value=%s last_widget_value=%s", value, self.last_widget_value)
        """
        Возвращает к предыдущему экрану, используя навигационный стек.
        :param value: (Опционально) данные для передачи при возврате.
        """
        prev_state = self.nav_manager.pop()
        if prev_state:
            self.open_widget(prev_state['screen'], None, prev_state['value'])
        else:
            logger.warning("История пуста. Нельзя вернуться назад.")

    def _on_issue_back_clicked(self):
        """Обработчик «Назад» на экранах выдачи: выбор триггера по контексту (по группе или по чертежу)."""
        if self.issue_context == "by_plan":
            value = self.value.get("plan_context")
            self.button_clicked("btn_back_to_plan", None, value=value)
        else:
            self.button_clicked("btn_back_to_group", None)

    def _on_summary_back_clicked(self):
        """Обработчик «Назад» на экране сводки и выбора плана: возврат в меню роли (user, admin или stockman)."""
        if self.last_role_screen == "screen_14_stockman":
            self.button_clicked("btn_back_to_stockman", None)
        elif self.last_role_screen == "screen_6_user":
            self.button_clicked("btn_back_to_user", None)
        elif self.last_role_screen == "screen_26_admin":
            self.button_clicked("btn_back_to_admin", None)

    def open_widget(self, widget_name: str, source: str = None, value: Any = None):
        logger.debug("open_widget widget_name=%s source=%s", widget_name, source)
        self.last_widget_value = value
        """
        Открывает виджет с указанным именем, скрывая остальные.

        :param widget_name: Имя виджета для отображения.
        :param value: Данные для передачи виджету.
        :param source: Имя источника перехода на виджет (кнопка).
        """

        # Если текущий экран уже установлен и он отличается от нового – сохраняем его в историю.
        # if self.current_screen and self.current_screen != widget_name and 'screen' in widget_name:
        #     self.nav_manager.push(self.current_screen, self.current_value)

        widget_found = False
        if 'screen' in widget_name:
            # Обработка виджетов
            for name, widget in self.widgets.items():
                visible = name == widget_name
                widget.setVisible(visible)
                widget.setFocus()
                if visible:
                    widget_found = True
                    if not value and hasattr(self, "value") and self.value:
                        key = (lambda name: name.split("_")[-1])(widget_name)

                        if key in self.value:
                            value = {key: self.value[key]}
                    # value = self._handle_widget_data(widget, source, value)
                    # Передаем данные в виджет и сохраняем текущее состояние
                    self.current_value = self._handle_widget_data(widget, source, value)
                    # Контекст выдачи для кнопки «Назад» на экранах подтверждения/успеха/ошибки
                    if widget_name == "screen_7_select_group":
                        self.issue_context = "by_group"
                    elif widget_name == "screen_9_select_tool_by_plan" and self.last_widget_value:
                        v = self.last_widget_value
                        if isinstance(v, (tuple, list)) and len(v) >= 4:
                            self.issue_context = "by_plan"
                            self.value["plan_context"] = {
                                "plan_id": v[3],
                                "plan_designation": v[1],
                                "plan_name": v[2],
                            }
                    # Запоминаем меню роли для возврата со сводки и выбора плана
                    if widget_name in ("screen_6_user", "screen_26_admin", "screen_14_stockman"):
                        self.last_role_screen = widget_name
                    # Список планов для возврата с screen_9 в screen_33 (user)
                    if widget_name == "screen_33_select_plan" and value:
                        self.value["plan_list_context"] = value

        self.current_screen = widget_name

        # Управление глобальным таймером сессии
        if widget_name == "screen_1_welcome":
            self.session_manager.stop()
        else:
            self.session_manager.start()

        # Если виджет не найден, возвращаемся к предыдущему состоянию
        if not widget_found and "cmd" not in widget_name:
            self._handle_widget_not_found(widget_name, source, value)
        elif "cmd" in widget_name:
            self._handle_cmd(widget_name, source, value)

    def _handle_widget_data(self, widget, source: str = None, *value: Any):
        """
        Обрабатывает передачу данных виджету.

        :param widget: Виджет для обработки.
        :param value: Данные для передачи.
        :param source: Имя источника перехода на виджет (кнопка).
        """
        logger.debug("_handle_widget_data widget=%s source=%s value=%s", widget, source, self.last_widget_value)

        # write = widget.is_write()
        # read  = widget.is_read()
        # if write and not read:
        widget.set_data(*value, source)
        # elif read and not write:
        data = widget.get_data()
        self.widget_back = widget
        return data

    def _handle_cmd(self, widget_name: str, source: str = None, value: Any = None):
        logger.debug("_handle_cmd widget_name=%s value=%s", widget_name, self.last_widget_value)
        """
        Обрабатывает случай, когда виджет не найден.

        :param widget_name: Имя несуществующего виджета.
        :param value: Данные для передачи следующему виджету.
        """
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            value, transition = self.action_callback(self.back_state, widget_name, self.lump, value, None)
            if transition:
                self.open_widget(transition, source, value=value)

    def _handle_widget_not_found(self, widget_name: str, source: str = None, value: Any = None):
        logger.debug("_handle_widget_not_found widget_name=%s source=%s value=%s", widget_name, source, self.last_widget_value)
        """
        Обрабатывает случай, когда виджет не найден.

        :param widget_name: Имя несуществующего виджета.
        :param value: Данные для передачи следующему виджету.
        """
        if widget_name == "read_db_get_plan_tools" and self.value.get("plan_context"):
            value = self.value["plan_context"]
        # При возврате с screen_9 на экран планов (user) read_db_plan нужен index для загрузки списка чертежей
        if widget_name == "read_db_plan" and self.back_state == "screen_9_select_tool_by_plan":
            if not isinstance(value, dict) or "index" not in value:
                value = {"index": 1} if not isinstance(value, dict) else {**value, "index": 1}
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            widget = self.widgets.get(self.back_state)
            if widget:
                if not value:
                    value = widget.get_data()
                if not value:
                    # key = widget_name.split("_")
                    # key = key[len(key)-1]
                    key = (lambda name: name.split("_")[-1])(widget_name)
                    if key in self.value:
                        value = {key: self.value[key]}
                value, transition = self.action_callback(
                    self.back_state, widget_name, self.lump, value, widget.handle_callback_executor
                )
                if transition:
                    self.open_widget(transition, source, value=value)
        else:
            logger.warning("Виджет '%s' не найден.", widget_name)

    def _handle_button_click_error(self, error: Exception):
        """
        Обрабатывает ошибки, возникающие при нажатии кнопки.

        :param error: Исключение, вызвавшее ошибку.
        """
        logger.exception("Ошибка при обработке кнопки: %s", error)

    def kill_proc_tree(self, pid, including_parent=True):
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        if including_parent:
            parent.kill()

    def closeEvent(self, event):
        logger.debug("closeEvent: %s", event)
        event.accept()
        self.kill_proc_tree(os.getpid())