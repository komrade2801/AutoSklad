# -*- coding: utf-8 -*-
import sys
import traceback
from typing import Any, Dict

from Core.app_logging import get_logger
from PyQt5 import QtWidgets, QtCore
from EventsSystem.events import Hendlers

logger = get_logger(__name__)
from GUI.BaseScreen import BaseScreen
from StateMachine.NavigationManager import NavigationManager
from StateMachine.screens import screen
from StateMachine.state_map import transitions
from StateMachine.FMS import Maps
from transitions import MachineError
from ui import *

# Настройка перехвата исключений
def exception_hook(exctype, value, tb):
    logger.exception("Необработанное исключение: %s %s", exctype, value)
    sys.__excepthook__(exctype, value, tb)


sys.excepthook = exception_hook


class MainWindow(QtWidgets.QWidget):
    def __init__(self, maps=None, handler=None):
        super().__init__()
        self.handler = handler or Hendlers()
        self.lump = maps or Maps("screen_1_welcome")
        logger.debug("Initial state: %s", self.lump.state())
        self.current_screen = ""
        self.current_value = {}
        self.value = {}  # Дополнительное хранилище данных для передачи в экраны
        self.back_state = None
        self.action_callback = None

        self.setWindowTitle("Main Window")
        self.resize(480, 800)
        self.setStyleSheet("background-color: #1A4789;")

        # Словари для хранения виджетов и сигналов кнопок
        self.widgets: Dict[str, BaseScreen] = {}
        self.button_signals: Dict[str, Any] = {}

        # Инициализация навигационного менеджера
        self.nav_manager = NavigationManager()

        # Основной layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Создаем экраны и привязываем переходы
        self.create_widgets()
        self.open_widget(self.lump.state(), None)

    def create_widgets(self):
        """Создает виджеты для всех экранов, добавляет их в основной layout и привязывает события."""
        for screen_name in screen.keys():
            widget = self.create_widget(screen_name)
            widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.widgets[screen_name] = widget
            self.layout.addWidget(widget)
            # Универсальное подключение сигналов для этого виджета
            self.bind_event_signals(widget)
        self.bind_transitions()

    def create_widget(self, screen_name: str) -> BaseScreen:
        """Создаёт и настраивает виджет для конкретного экрана."""
        ui_class = getattr(sys.modules[__name__], screen_name, None)
        if ui_class and issubclass(ui_class, BaseScreen):
            return ui_class()
        else:
            raise TypeError(f"Экран {screen_name} не наследуется от BaseScreen")

    def bind_event_signals(self, widget: BaseScreen):
        """
        Универсальное подключение событий (свойств виджета) к обработчику button_clicked.
        Для каждого известного события (атрибут, содержащий событие) задаем lambda-обработчик,
        который вызывает self.button_clicked с соответствующим именем кнопки.
        """
        # Словарь: имя атрибута события -> имя кнопки по умолчанию
        event_mapping = {
            "event_timeout_back": "timeout_back",
            "event_input_name_code": "input_name_code",
            "event_select_group": "btn_select_group_names",
            "event_select_management_group": "btn_warehouse_select_tools",
            "event_select_tool": "btn_tool_name",
            "event_enter_barcode": "barcode",
        }
        for event_attr, default_btn in event_mapping.items():
            if hasattr(widget, event_attr):
                # Переназначаем событие на универсальный обработчик.
                setattr(
                    widget,
                    event_attr,
                    lambda checked=False, btn_name=default_btn: self.button_clicked(btn_name, dest=None)
                )

        # Если в виджете есть QLineEdit, можно также подключить события focus_in/focus_out,
        # если они реализованы (пример – MyLineEdit). Здесь можно расширить логику по необходимости.

    def bind_transitions(self):
        """Привязывает кнопки к переходам между экранами на основе карты transitions."""
        for transition in transitions:
            trigger = transition['trigger']
            source = transition['source']
            dest = transition['dest']
            if source in self.widgets:
                self.bind_button_signal(source, trigger, dest)

    def bind_button_signal(self, source: str, trigger: str, dest: str):
        """
        Привязывает сигнал кнопки с именем trigger, найденной на виджете source, к переходу на экран dest.
        Если кнопка найдена, ее clicked сигнал связывается с обработчиком, который вызывает button_clicked.
        """
        widget = self.widgets[source]
        button = widget.findChild(QtWidgets.QPushButton, trigger)
        if button:
            self.button_signals[button.objectName()] = button.clicked
            button.clicked.connect(lambda checked, btn_name=button.objectName(): self.button_clicked(btn_name, dest))
        else:
            # Если кнопка не найдена, можно логировать информацию или игнорировать
            logger.warning("Кнопка с именем '%s' не найдена на экране '%s'.", trigger, source)

    def button_clicked(self, button_name: str, dest: str = None, value: Any = 0):
        """
        Обрабатывает нажатие кнопки.
        Если получено событие таймера – игнорируем, если мы не на начальном экране.
        Вызывает trigger конечного автомата и открывает новый виджет.
        """
        if 'timer' in button_name and self.lump.state() != self.lump.machine.initial:
            return

        self.back_state = self.lump.state()
        logger.debug("button_clicked: %s, state: %s, value: %s", button_name, self.lump.state(), value)
        try:
            self.lump.trigger(button_name)
        except (MachineError, TypeError, AttributeError) as e:
            self._handle_button_click_error(e)
            logger.exception("button_clicked error")
            return

        new_state = self.lump.state()
        if new_state != self.back_state:
            if 'btn_back' in button_name and new_state != self.lump.machine.initial:
                self.open_back_widget()
            else:
                self.open_widget(new_state, value)

    def open_back_widget(self, value: Any = None):
        logger.debug("open_back_widget value: %s", value)
        """
        Возвращает к предыдущему экрану, используя навигационный стек.
        """
        prev = self.nav_manager.pop()
        if prev:
            self.open_widget(prev['screen'], prev['value'])
        else:
            logger.warning("История пуста. Нельзя вернуться назад.")

    def open_widget(self, widget_name: str, value: Any = None):
        logger.debug("open_widget: %s, value: %s", widget_name, value)
        """
        Открывает виджет с указанным именем, скрывая остальные.
        При смене экрана сохраняет текущее состояние в навигационном стеке.
        """
        if self.current_screen and self.current_screen != widget_name and 'screen' in widget_name:
            self.nav_manager.push(self.current_screen, self.current_value)

        widget_found = False
        if 'screen' in widget_name:
            for name, widget in self.widgets.items():
                is_visible = (name == widget_name)
                widget.setVisible(is_visible)
                if is_visible:
                    widget_found = True
                    # Если значение не передано, пытаемся взять из self.value по ключу, основанному на последней части имени экрана
                    if value is None and self.value:
                        key = widget_name.split("_")[-1]
                        if key in self.value:
                            value = {key: self.value[key]}
                    # Передаем данные в виджет и сохраняем его состояние
                    widget.set_data(value)  # Передаем данные
                    self.current_value = widget.get_data()
        self.current_screen = widget_name

        if not widget_found and "cmd" not in widget_name:
            self._handle_widget_not_found(widget_name, value)
        elif "cmd" in widget_name:
            self._handle_cmd(widget_name, value)

    def _handle_widget_not_found(self, widget_name: str, value: Any):
        logger.debug("_handle_widget_not_found widget_name=%s value=%s", widget_name, value)
        """
        Обрабатывает случай, когда запрошенный виджет не найден.
        Вызывает action_callback, если он определен.
        """
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            widget = self.widgets.get(self.back_state)
            if widget:
                if not value:
                    value = widget.get_data()
                key = widget_name.split("_")[-1]
                if key in self.value:
                    value = {key: self.value[key]}
                value, transition = self.action_callback(
                    self.back_state, widget_name, self.lump, value, widget.handle_callback_executor
                )
                if transition:
                    self.open_widget(transition, value=value)
        else:
            logger.warning("Виджет '%s' не найден.", widget_name)

    def _handle_cmd(self, widget_name: str, value: Any):
        logger.debug("_handle_cmd widget_name=%s value=%s", widget_name, value)
        """
        Обрабатывает команды (виджеты с "cmd" в имени) через action_callback.
        """
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            value, transition = self.action_callback(self.back_state, widget_name, self.lump, value, None)
            if transition:
                self.open_widget(transition, value=value)

    def _handle_button_click_error(self, error: Exception):
        """Обрабатывает ошибки, возникающие при нажатии кнопки."""
        logger.exception("Ошибка при обработке кнопки: %s", error)
