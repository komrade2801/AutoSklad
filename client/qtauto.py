# -*- coding: utf-8 -*-
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication

from EventsSystem.Executor import Executor
from EventsSystem.action_selector import ActionSelector
from EventsSystem.events import Hendlers

from EventsSystem.state_router import StateRouter
from GUI.BaseScreen import BaseScreen
from GUI.helper.MyLineEdit import MyLineEdit
from StateMachine.state_map import transitions, states
from StateMachine.screens import screen
from StateMachine.FMS import Maps
from transitions import MachineError
from ui import *


# Класс для управления отображением виджетов
class MainWindowEvent(QtCore.QObject):
    show_widget = QtCore.pyqtSignal(str)


# Настройка перехвата исключений
def exception_hook(exctype, value, traceback):
    print(f"Тип исключения: {exctype}")
    print(f"Значение исключения: {value}")
    print(f"Трассировка: {traceback}")
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = exception_hook


# Главное окно приложения
class MainWindow(QtWidgets.QWidget):
    def __init__(self, maps=None, handler=None):
        super().__init__()

        self.handler = handler or Hendlers()
        self.lump = maps or Maps()
        self.current_screen = ""

        self.setWindowTitle("Main Window")
        self.showFullScreen()
        self.resize(480, 800)

        # Словари для хранения виджетов и сигналов кнопок
        self.widgets = {}
        self.button_signals = {}

        # Основной layout
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Создание экранов
        self.create_widgets()
        self.open_widget(self.lump.state(), None)
        self.action_callback = None
        # self.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0.5, y1:0, x2:0.5, y2:1, stop:0 rgba(47, 70, 105, 255), stop:1 rgba(131, 149, 174, 255));\n""")
        self.setStyleSheet("background-color: #1A4789;")
        self.back_state = None

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

    def bind_button_signal(self, source, trigger, dest):
        """Привязывает сигнал кнопки к обработчику."""

        if self.widgets[source].event_timeout_back:
            self.widgets[source].event_timeout_back = (lambda checked, btn_name="timeout_back": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_input_name_code:
            self.widgets[source].event_input_name_code = (lambda checked, btn_name="input_name_code": self.button_clicked(btn_name, dest))

        if self.widgets[source].event_select_group:
            self.widgets[source].event_select_group = (lambda checked, btn_name="btn_select_group_names": self.button_clicked(btn_name, dest))
        if self.widgets[source].event_select_tool:
            self.widgets[source].event_select_tool = (lambda checked, btn_name="btn_tool_name": self.button_clicked(btn_name, dest))
        if self.widgets[source].event_select_plan:
            self.widgets[source].event_select_plan = (lambda checked, btn_name="btn_plan_name": self.button_clicked(btn_name, dest))

        button = self.widgets[source].findChild(QtWidgets.QPushButton, trigger)
        if button:
            self.button_signals[button.objectName()] = button.clicked
            button_name = button.objectName()
            button.clicked.connect(lambda checked, btn_name=button_name: self.button_clicked(btn_name, dest))

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

    def button_clicked(self, button_name: str, dest: str = None):
        """
        Обрабатывает нажатие кнопки.

        :param button_name: Имя нажатой кнопки.
        :param dest: Целевое состояние (опционально).
        """
        try:
            self.back_state = self.lump.state()
            print("button_clicked", button_name, "state", self.lump.state())
            self.lump.trigger(button_name)
            state = self.lump.state()
            self.open_widget(state, None)
        except (MachineError, TypeError, AttributeError) as e:
            self._handle_button_click_error(e)

    def open_widget(self, widget_name: str, value: Any = None):
        """
        Открывает виджет с указанным именем, скрывая остальные.

        :param widget_name: Имя виджета для отображения.
        :param value: Данные для передачи виджету.
        """
        widget_found = False

        # Обработка виджетов
        for name, widget in self.widgets.items():
            visible = name == widget_name
            widget.setVisible(visible)

            if visible:
                widget_found = True
                value = self._handle_widget_data(widget, value)

        self.current_screen = widget_name

        # Если виджет не найден, возвращаемся к предыдущему состоянию
        if not widget_found and "cmd" not in widget_name:
            self._handle_widget_not_found(widget_name, value)
        elif "cmd" in widget_name:
            self._handle_cmd(widget_name, value)

    def _handle_widget_data(self, widget, *value: Any):
        """
        Обрабатывает передачу данных виджету.

        :param widget: Виджет для обработки.
        :param value: Данные для передачи.
        """
        # write = widget.is_write()
        # read  = widget.is_read()
        # if write and not read:
        widget.set_data(*value)
        # elif read and not write:
        return widget.get_data()

    def _handle_cmd(self, widget_name: str, value: Any):
        """
        Обрабатывает случай, когда виджет не найден.

        :param widget_name: Имя несуществующего виджета.
        :param value: Данные для передачи следующему виджету.
        """
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            value, transition = self.action_callback(self.back_state, widget_name, self.lump, value, None)
            if transition:
                self.open_widget(transition, value=value)



    def _handle_widget_not_found(self, widget_name: str, value: Any):
        """
        Обрабатывает случай, когда виджет не найден.

        :param widget_name: Имя несуществующего виджета.
        :param value: Данные для передачи следующему виджету.
        """
        if self.lump.machine.initial != widget_name and callable(self.action_callback):
            widget = self.widgets.get(self.back_state)
            if widget:
                value = widget.get_data()
                value, transition = self.action_callback(
                    self.back_state, widget_name, self.lump, value, widget.handle_callback_executor
                )
                if transition:
                    self.open_widget(transition, value=value)
        else:
            print(f"Виджет '{widget_name}' не найден.")



    def _handle_button_click_error(self, error: Exception):
        """
        Обрабатывает ошибки, возникающие при нажатии кнопки.

        :param error: Исключение, вызвавшее ошибку.
        """
        print(f"Ошибка при обработке кнопки: {error}")
        self.lump.trigger("err_authorization")
        self.lump.trigger("view_err_login")
        self.open_widget(self.lump.state(), None)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    maps = Maps()
    window = MainWindow(maps)
    executor = Executor()
    window.action_callback = executor.handle_widget_executor
    window.show()
    sys.exit(app.exec_())

