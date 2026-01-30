from PyQt5.QtCore import QEventLoop, QTimer, QThread
import traceback
import subprocess
import sys
import socket
import serial
import serial.tools.list_ports
import logging
from Core.platforms import detect
# from BarcodeScanner.SerialWorker import SerialWorker  # Используем потоковый класс!

logger = logging.getLogger(__name__)


class ActionMapper:
    def __init__(self, executor):
        self.__executor = executor
        self.serial_worker = None
        self.response_ok = False
        self.response_command_ok = False
        self.platform = detect()
        self.__actions = {
            'cmd_start': lambda *args, **kwargs: logger.debug("cmd_start %s %s", args, kwargs),
            'cmd_test_self': lambda *args, **kwargs: logger.debug("cmd_test_self %s %s", args, kwargs),
            'cmd_empty': lambda *args, **kwargs: lambda *args, **kwargs: self.cmd_empty(*args, **kwargs),
            'cmd_run_timeout_wait_back': lambda *args, **kwargs: self.cmd_run_timeout_wait_back(*args, **kwargs),
            'cmd_run_timeout_get_back': lambda *args, **kwargs: self.cmd_run_timeout_get_back(*args, **kwargs),
            'cmd_run_timeout_post_back': lambda *args, **kwargs: self.cmd_run_timeout_post_back(*args, **kwargs),
            'cmd_reboot': lambda *args, **kwargs: self.cmd_reboot(*args, **kwargs),
            'cmd_test_is_free': lambda *args, **kwargs: self.cmd_test_is_free(*args, **kwargs),
            'cmd_ping': lambda *args, **kwargs: self.cmd_ping(*args, **kwargs),
            'cmd_stop': lambda *args, **kwargs: self.cmd_stop(*args, **kwargs),
            'cmd_send': lambda *args, **kwargs: self.cmd_send(*args, **kwargs),
            'cmd_run_timer_event': lambda *args, **kwargs: logger.debug("cmd_run_timer_event %s %s", args, kwargs),
            'cmd_keyboard_toggle': lambda index: logger.debug("cmd_keyboard_toggle %s", index),
        }


    def cmd_send(self, number, tool_name, port='COM30', baudrate=9600, timeout=15, trigger=None):
        # print(f"Отправка команды: {number} | Инструмент: {tool_name} | Порт: {port}")
        if number:
            self.__executor.controller_serial_manager.send_data(number)
        else:
            logger.warning("cmd_send number: %s is None, tool_name: %s", number, tool_name)


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

    def cmd_reboot(self, *args, **kwargs):
        """
        Перезагрузка системы.
        Приложение должно запускаться от sudo для работы на Raspberry Pi.
        """
        try:
            logging.info("Инициирована перезагрузка системы")
            
            if self.platform == 'Raspberry Pi' or self.platform == 'Linux':
                # Используем systemctl для корректной перезагрузки
                subprocess.run(['systemctl', 'reboot'], check=True, timeout=5)
            elif self.platform == 'Windows':
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True, timeout=5)
            else:
                logging.warning(f"Перезагрузка не поддерживается на {self.platform}")
                return {'trigger': 'error', 'message': f'Перезагрузка не поддерживается на {self.platform}'}
            
            return {'trigger': 'ok'}
        except subprocess.TimeoutExpired:
            logging.error("Таймаут при выполнении команды перезагрузки")
            return {'trigger': 'error', 'message': 'Таймаут выполнения команды'}
        except subprocess.CalledProcessError as e:
            logging.error(f"Ошибка перезагрузки: {e}")
            return {'trigger': 'error', 'message': f'Ошибка перезагрузки: {e}'}
        except Exception as e:
            logging.error(f"Неожиданная ошибка при перезагрузке: {e}")
            traceback.print_exc()
            return {'trigger': 'error', 'message': f'Неожиданная ошибка: {e}'}

    def cmd_stop(self, *args, **kwargs):
        """
        Выключение системы.
        Приложение должно запускаться от sudo для работы на Raspberry Pi.
        """
        try:
            logging.info("Инициировано выключение системы")
            
            if self.platform == 'Raspberry Pi' or self.platform == 'Linux':
                # Используем systemctl для корректного выключения
                subprocess.run(['systemctl', 'poweroff'], check=True, timeout=5)
            elif self.platform == 'Windows':
                subprocess.run(['shutdown', '/s', '/t', '0'], check=True, timeout=5)
            else:
                logging.warning(f"Выключение не поддерживается на {self.platform}")
                return {'trigger': 'error', 'message': f'Выключение не поддерживается на {self.platform}'}
            
            return {'trigger': 'ok'}
        except subprocess.TimeoutExpired:
            logging.error("Таймаут при выполнении команды выключения")
            return {'trigger': 'error', 'message': 'Таймаут выполнения команды'}
        except subprocess.CalledProcessError as e:
            logging.error(f"Ошибка выключения: {e}")
            return {'trigger': 'error', 'message': f'Ошибка выключения: {e}'}
        except Exception as e:
            logging.error(f"Неожиданная ошибка при выключении: {e}")
            traceback.print_exc()
            return {'trigger': 'error', 'message': f'Неожиданная ошибка: {e}'}

    def cmd_ping(self, *args, **kwargs):
        """
        Проверка доступности сервера через TCP соединение.
        Возвращает статус 'ok' или 'error'.
        """
        try:
            from Cnf.Actions import CnfActions
            
            cnf = CnfActions()
            config = cnf.read_cnf(0)
            server_ip = str(config.get('server', {}).get('ip', '127.0.0.1'))
            server_port = int(config.get('server', {}).get('port', 8000))
            
            logging.info(f"Проверка доступности сервера {server_ip}:{server_port}")
            
            # Проверка доступности порта через TCP соединение
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_ip, server_port))
            sock.close()
            
            if result == 0:
                logging.info(f"Сервер {server_ip}:{server_port} доступен")
                return {'trigger': 'status', 'status': 'ok'}
            else:
                logging.warning(f"Сервер {server_ip}:{server_port} недоступен (код: {result})")
                return {'trigger': 'status', 'status': 'error'}
        except socket.gaierror as e:
            logging.error(f"Ошибка разрешения имени хоста: {e}")
            return {'trigger': 'status', 'status': 'error'}
        except socket.timeout:
            logging.warning("Таймаут при проверке доступности сервера")
            return {'trigger': 'status', 'status': 'error'}
        except Exception as e:
            logging.error(f"Ошибка при выполнении ping: {e}")
            traceback.print_exc()
            return {'trigger': 'status', 'status': 'error'}

    def cmd_test_is_free(self, *args, **kwargs):
        """
        Проверка доступности последовательного порта.
        Возвращает статус 'ok' если порт свободен, 'error' если занят или недоступен.
        """
        try:
            from Cnf.Actions import CnfActions
            
            cnf = CnfActions()
            serial_config = cnf.read_cnf_serial(0)
            port = serial_config.get('port', 'COM29')
            
            logging.info(f"Проверка доступности порта {port}")
            
            # Попытка открыть порт для проверки доступности
            try:
                ser = serial.Serial(port, timeout=1)
                ser.close()
                logging.info(f"Порт {port} доступен")
                return {'trigger': 'status', 'status': 'ok'}
            except serial.SerialException as e:
                logging.warning(f"Порт {port} недоступен или занят: {e}")
                return {'trigger': 'status', 'status': 'error'}
        except Exception as e:
            logging.error(f"Ошибка при проверке порта: {e}")
            traceback.print_exc()
            return {'trigger': 'status', 'status': 'error'}



