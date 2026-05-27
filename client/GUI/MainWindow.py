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


# Триггеры FMS с HAL-драйвера (fsm_signal → MainWindow), не сырые строки UART
_HAL_FSM_TO_UI = frozenset(
    (
        "command_is_send",
        "command_ok",
        "command_ok_engineer",
        "err_devices",
    )
)

# Состояния FSM без Qt-экрана: выполняются через Executor (как cmd_*).
_FSM_ACTION_PREFIXES = (
    "read_db",
    "write_db",
    "read_cnf",
    "write_cnf",
    "http_",
    "write_log_",
)


# Главное окно приложения
class MainWindow(QtWidgets.QWidget):
    def __init__(self, maps=None, handler=None, controller_protocol: str = "legacy"):
        super().__init__()

        self.controller_protocol = (controller_protocol or "legacy").strip().lower()
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
        self.SUMMARY_BACK_SCREENS = ('screen_21_summary', 'screen_33_select_plan', 'screen_7_select_group')
        # screen_9: «Назад» — на экран выбора чертежа (read_db_plan → screen_33), с сохранением роли
        self.SCREEN_9_BACK_TO_PLAN = ('screen_9_select_tool_by_plan',)
        # # Наш навигационный менеджер
        # self.nav_manager = NavigationManager()

        # Основной layout; экраны — в QStackedWidget (не в общий VBox: на Windows
        # скрытые Expanding-виджеты раздувают высоту и сдвигают активный экран вверх).
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self._screen_stack = QtWidgets.QStackedWidget(self)
        self._screen_stack.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.layout.addWidget(self._screen_stack)
        self._screen_size = QtCore.QSize(480, 800)

        # Создание экранов
        self.create_widgets()
        self.session_manager = SessionIdleManager(self)
        QApplication.instance().installEventFilter(self.session_manager)
        self.last_widget_value = {}
        self.action_callback = None
        self.executor = None
        self._startup_hardware_done = False
        if self.lump.state() == "screen_32_wait":
            self.open_widget(
                "screen_32_wait",
                None,
                {"wait_screen_message": "Загрузка"},
            )
        else:
            self.open_widget(self.lump.state(), None, None)
        # self.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 rgba(47, 70, 105, 255), stop:1 rgba(131, 149, 174, 255));\n""")
        self.setStyleSheet("background-color: #2e4461;")

    def create_widgets(self):
        """Создает виджеты для всех экранов."""
        for screen_name, buttons in screen.items():
            widget = self.create_widget(screen_name)
            widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding,
            )
            widget.resize(self._screen_size)
            self.widgets[screen_name] = widget
            self._screen_stack.addWidget(widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.bind_transitions()
        welcome = self.widgets.get("screen_1_welcome")
        if welcome is not None:
            self._screen_stack.setCurrentWidget(welcome)

    def _is_fsm_action_state(self, widget_name: str) -> bool:
        if "cmd" in widget_name:
            return True
        return widget_name.startswith(_FSM_ACTION_PREFIXES)

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
        # screen_9: «Назад» — на экран выбора чертежа (по last_role_screen вызывается read_db_plan → screen_33)
        for source in self.SCREEN_9_BACK_TO_PLAN:
            if source not in self.widgets:
                continue
            btn = self.widgets[source].findChild(QtWidgets.QPushButton, "btn_back")
            if btn:
                btn.clicked.connect(self._on_screen_9_back_to_plan_clicked)
                self.button_signals[btn.objectName()] = btn.clicked
        self._bind_engineer_screen_events()

    def _bind_engineer_screen_events(self):
        s38 = self.widgets.get("screen_38_hal_coords")
        if s38 is not None:
            s38.event_hal_jog = self._on_hal_jog_clicked
            s38.event_hal_mot_send = self._on_hal_mot_send_clicked
            s38.event_hal_save_coords = self._on_hal_save_coords_clicked
            s38.event_hal_park = self._on_hal_park_clicked
            s38.event_hal_zero = self._on_hal_zero_clicked
            for btn_name, handler in (
                ("btn_hal_save_coords", s38.forward_save_coords),
                ("btn_hal_park", s38._forward_hal_park),
                ("btn_hal_zero", s38._forward_hal_zero),
            ):
                btn = s38.findChild(QtWidgets.QPushButton, btn_name)
                if btn is not None:
                    btn.clicked.connect(lambda checked=False, h=handler: h())
        s40 = self.widgets.get("screen_40_hal_dispense")
        if s40 is not None:
            s40.event_hal_park_save = self._on_hal_park_save_clicked
            s40.event_hal_led_toggle = self._on_hal_led_toggle_clicked
            s40.event_hal_solenoid = self._on_hal_solenoid_clicked
            s40.event_hal_lock = self._on_hal_lock_clicked
            for btn_name, handler in (
                ("btn_hal_park_save", s40.forward_park_save),
                ("btn_hal_led", s40.forward_hal_led_toggle),
                ("btn_hal_solenoid", s40.forward_hal_solenoid),
                ("btn_hal_lock", s40.forward_hal_lock),
            ):
                btn = s40.findChild(QtWidgets.QPushButton, btn_name)
                if btn is not None:
                    btn.clicked.connect(lambda checked=False, h=handler: h())

    def _on_hal_park_save_clicked(self):
        self.button_clicked("btn_hal_park_save", "write_db_hal_park_defaults")

    def _on_hal_led_toggle_clicked(self):
        self.button_clicked("btn_hal_led", "cmd_hal_led_toggle")

    def _on_hal_solenoid_clicked(self):
        self.button_clicked("btn_hal_solenoid", "cmd_hal_solenoid")

    def _on_hal_lock_clicked(self):
        self.button_clicked("btn_hal_lock", "cmd_hal_lock")

    def _on_hal_jog_clicked(self, trigger_name: str):
        if self.executor is not None:
            self.executor.last_hal_jog_trigger = trigger_name
        self.button_clicked(trigger_name, "cmd_hal_jog")

    def _on_hal_mot_send_clicked(self):
        self.button_clicked("btn_hal_mot_send", "cmd_hal_mot_goto")

    def _on_hal_save_coords_clicked(self):
        self.button_clicked("btn_hal_save_coords", "write_db_cell_hal_coords")

    def _on_hal_park_clicked(self):
        self.button_clicked("btn_hal_park", "cmd_hal_park")

    def _on_hal_zero_clicked(self):
        self.button_clicked("btn_hal_zero", "cmd_hal_zero")

    def _capture_engineer_cell_number_from_widget(self):
        widget = self.widgets.get(self.lump.state())
        if widget is None or not hasattr(widget, "get_data"):
            return
        try:
            data = widget.get_data()
        except Exception:
            return
        if isinstance(data, dict) and self.executor is not None:
            if data.get("engineer_cell_number") is not None:
                self.executor.engineer_cell_number = data["engineer_cell_number"]
            if data.get("hal_x") is not None:
                self.executor.hal_save_hal_x = int(data["hal_x"])
            if data.get("hal_z") is not None:
                self.executor.hal_save_hal_z = int(data["hal_z"])

    def bind_button_signal(self, source, trigger, dest):
        """Привязывает сигнал кнопки к обработчику."""
        # event_timeout_back отключён — используется глобальный SessionIdleManager

        # JOG / «Отправка» / «Сохранить» на screen_38 — через event_hal_* (иначе двойной cmd).
        if source == "screen_38_hal_coords" and (
            trigger.startswith("hal_jog_")
            or trigger in (
                "btn_hal_mot_send",
                "btn_hal_save_coords",
                "btn_hal_park",
                "btn_hal_zero",
            )
        ):
            return

        if source == "screen_40_hal_dispense" and trigger in (
            "btn_hal_park_save",
            "btn_hal_led",
            "btn_hal_solenoid",
            "btn_hal_lock",
        ):
            return

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
        if source in self.ISSUE_BACK_SCREENS and trigger in ("btn_back_to_group", "btn_back_to_plan", "btn_back_to_plan_selection"):
            return
        # На экранах сводки и выбора плана триггеры btn_back_to_* привязаны к btn_back в bind_transitions
        if source in self.SUMMARY_BACK_SCREENS and trigger in ("btn_back_to_admin", "btn_back_to_stockman", "btn_back_to_user"):
            return
        # На screen_9 «Назад» привязан к _on_screen_9_back_to_plan_clicked; виртуальные триггеры не ищут кнопку
        if source == "screen_9_select_tool_by_plan" and trigger in ("btn_back_to_plan_list_user", "btn_back_to_plan_list_stockman", "btn_back_to_user", "btn_back_to_stockman"):
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

    def attach_session_idle_hardware_monitoring(self) -> None:
        """
        Пока VendingSerialManager или DispenseCommandGate выполняют операции,
        SessionIdleManager не отсчитывает время простоя.
        """
        if self.executor is None:
            return
        mgr = self.executor.controller_serial_manager
        if mgr is not None and hasattr(mgr, "is_hardware_busy"):
            self.session_manager.register_busy_checker(mgr.is_hardware_busy)
        cmd_mapper = self.executor.selector.mappers.get("cmd")
        if cmd_mapper is not None and hasattr(cmd_mapper, "is_hal_operation_busy"):
            self.session_manager.register_busy_checker(cmd_mapper.is_hal_operation_busy)

    def handle_controller_serial_response(self, response):
        """Обрабатываем полученный ответ"""
        self.session_manager.reset_timer()
        logger.debug("MainWindow controller_serial получен: %s value=%s", response, self.last_widget_value)
        if self.controller_protocol == "atmega_hal" and response not in _HAL_FSM_TO_UI:
            logger.debug("HAL: ответ вне моста FSM, в автомат не передаём: %r", response)
            return
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
        if 'timer' in button_name and self.lump.state() != self.lump.machine.initial:
            return

        if (
            self.executor is not None
            and getattr(self.executor, "engineer_wait_context", None) == "startup"
            and self.lump.state() in ("screen_32_wait", "cmd_test_self")
        ):
            logger.debug(
                "button_clicked ignored during startup HAL check: %s",
                button_name,
            )
            return

        try:
            self._capture_engineer_cell_number_from_widget()
            self.back_state = self.lump.state()
            self.lump.trigger(button_name)
            state = self.lump.state()
            logger.debug("button_clicked button_name=%s state=%s value=%s", button_name, state, self.last_widget_value)
            if state != self.back_state:
                self.open_widget(state, button_name, value)
        except (MachineError, TypeError, AttributeError) as e:
            self._handle_button_click_error(e)

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
        """Обработчик «Назад» на экранах выдачи: по группе — к списку групп, по чертежу — на экран выбора чертежа."""
        if self.issue_context == "by_plan":
            # Возврат на экран выбора чертежа (read_db_plan → screen_33), список обновится при повторном входе в план
            value = self.value.get("plan_list_context") or {"index": 1}
            if not isinstance(value, dict) or "index" not in value:
                value = {"index": 1} if not isinstance(value, dict) else {**value, "index": 1}
            self.button_clicked("btn_back_to_plan_selection", None, value=value)
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

    def _on_screen_9_back_to_plan_clicked(self):
        """Обработчик «Назад» на screen_9: переход на экран выбора чертежа (screen_33) с сохранением роли."""
        value = self.value.get("plan_list_context") or {"index": 1}
        if not isinstance(value, dict) or "index" not in value:
            value = {"index": 1} if not isinstance(value, dict) else {**value, "index": 1}
        if self.last_role_screen == "screen_6_user":
            self.button_clicked("btn_back_to_plan_list_user", None, value=value)
        else:
            self.button_clicked("btn_back_to_plan_list_stockman", None, value=value)

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
            widget = self.widgets.get(widget_name)
            if widget is not None:
                self._screen_stack.setCurrentWidget(widget)
                widget.setFocus()
                widget_found = True
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
                if widget_name in (
                    "screen_6_user",
                    "screen_26_admin",
                    "screen_14_stockman",
                    "screen_37_engineer_hub",
                ):
                    self.last_role_screen = widget_name
                # Список планов для возврата с screen_9 в screen_33 (user)
                if widget_name == "screen_33_select_plan" and value:
                    self.value["plan_list_context"] = value
                widget.updateGeometry()
                self._screen_stack.update()

        self.current_screen = widget_name

        # Управление глобальным таймером сессии
        if widget_name == "screen_1_welcome":
            self.session_manager.stop()
        else:
            self.session_manager.start()

        if not widget_found and self._is_fsm_action_state(widget_name):
            self._run_fsm_action(widget_name, source, value)
        elif not widget_found:
            self._handle_widget_not_found(widget_name, source, value)

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
        if isinstance(value, dict):
            widget.set_data(value, source=source)
        elif isinstance(value, (list, tuple)):
            widget.set_data(*value, source=source)
        elif value is not None:
            widget.set_data(value, source=source)
        else:
            widget.set_data(source=source)
        data = widget.get_data()
        self.widget_back = widget
        return data

    def _run_fsm_action(self, widget_name: str, source: str = None, value: Any = None):
        """Выполняет служебное состояние FSM (cmd/read_db/write_db/…) и открывает следующий экран."""
        logger.debug("_run_fsm_action widget_name=%s value=%s", widget_name, value)
        if not callable(self.action_callback):
            return
        start_state = self.back_state if self.back_state is not None else widget_name
        widget = self.widgets.get(self.back_state) if self.back_state else None
        callback = widget.handle_callback_executor if widget else None
        if widget and not value:
            value = widget.get_data()
        result, transition = self.action_callback(
            start_state, widget_name, self.lump, value, callback
        )
        if transition:
            # В open_widget — результат action (ФИО, кортеж плана и т.д.), не входной value с экрана.
            self.open_widget(transition, source, value=result)

    def run_startup_hardware_check(self):
        """
        Стартовая проверка HAL: экран screen_32_wait («Загрузка») → cmd_test_self.
        Успех (ok) → screen_1_welcome; ошибка → screen_36_hardware_err.
        """
        if self._startup_hardware_done:
            return
        self._startup_hardware_done = True
        if not callable(self.action_callback):
            logger.warning("run_startup_hardware_check: action_callback не задан")
            return
        if self.lump.state() != "screen_32_wait":
            logger.debug(
                "run_startup_hardware_check: пропуск, FSM=%s",
                self.lump.state(),
            )
            return
        if self.executor is not None:
            self.executor.wait_screen_message = "Загрузка"
            self.executor.engineer_wait_context = "startup"
        self.session_manager.stop()
        self.open_widget(
            "screen_32_wait",
            None,
            {"wait_screen_message": "Загрузка"},
        )
        self.back_state = "screen_32_wait"
        try:
            self.lump.trigger("hardware_check")
        except MachineError as e:
            logger.warning("run_startup_hardware_check: %s", e)
            return
        state = self.lump.state()
        if state != "screen_32_wait":
            logger.info("run_startup_hardware_check: FSM=%s, запуск cmd_test_self", state)
            self._run_fsm_action(state, None, value={"trigger": "hardware_check"})

    def _handle_widget_not_found(self, widget_name: str, source: str = None, value: Any = None):
        logger.debug("_handle_widget_not_found widget_name=%s source=%s value=%s", widget_name, source, self.last_widget_value)
        if self._is_fsm_action_state(widget_name):
            self._run_fsm_action(widget_name, source, value)
            return
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            self._run_fsm_action(widget_name, source, value)
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