from PyQt5.QtCore import QEventLoop, QTimer, QThread
import traceback
# from BarcodeScanner.SerialWorker import SerialWorker  # Используем потоковый класс!

class ActionMapper:
    def __init__(self, executor):
        self.__executor = executor
        self.serial_worker = None
        self.response_ok = False
        self.response_command_ok = False
        self.__actions = {
            'cmd_start': lambda *args, **kwargs: print("cmd_start", *args, **kwargs),
            'cmd_test_self': lambda *args, **kwargs: print("cmd_test_self", *args, **kwargs),
            'cmd_empty': lambda *args, **kwargs: lambda *args, **kwargs: self.cmd_empty(*args, **kwargs),
            'cmd_run_timeout_wait_back': lambda *args, **kwargs: self.cmd_run_timeout_wait_back(*args, **kwargs),
            'cmd_run_timeout_get_back': lambda *args, **kwargs: self.cmd_run_timeout_get_back(*args, **kwargs),
            'cmd_run_timeout_post_back': lambda *args, **kwargs: self.cmd_run_timeout_post_back(*args, **kwargs),
            'cmd_reboot': lambda *args, **kwargs: print("cmd_reboot", *args, **kwargs),
            'cmd_test_is_free': lambda *args, **kwargs: print("cmd_test_is_free", *args, **kwargs),
            'cmd_ping': lambda *args, **kwargs: print("cmd_ping", *args, **kwargs),
            'cmd_stop': lambda *args, **kwargs: print("cmd_stop", *args, **kwargs),
            'cmd_send': lambda *args, **kwargs: self.cmd_send(*args, **kwargs),
            'cmd_run_timer_event': lambda *args, **kwargs: print("cmd_run_timer_event", *args, **kwargs),
            'cmd_keyboard_toggle': lambda index: print("cmd_keyboard_toggle",index),
        }


    def cmd_send(self, number, tool_name, port='COM30', baudrate=9600, timeout=15, trigger=None):
        # print(f"Отправка команды: {number} | Инструмент: {tool_name} | Порт: {port}")
        if number:
            self.__executor.controller_serial_manager.send_data(number)
        else:
            print(f"cmd_send number: {number} is None, tool_name: {tool_name}")


    def execute(self, action, *args, **kwargs):
        """
        Выполняет заданное действие, если оно есть в списке.
        """
        if action in self.__actions:
            return self.__actions[action](*args, **kwargs)
            # try:  except Exception as e:
            # print(f"Ошибка при выполнении {action}: {e}")
        else:
            raise ValueError(f"Команда '{action}' не найдена.")

    def cmd_run_timeout_wait_back(self, *args, **kwargs):
        return {'trigger': 'view_wait'}

    def cmd_empty(self, *args, **kwargs):
        return {'trigger': 'ok'}

    def cmd_run_timeout_get_back(self, *args, **kwargs):
        return {'trigger': 'wait_run'}

    def cmd_run_timeout_post_back(self, *args, **kwargs):
        return {'trigger': 'wait_run'}



