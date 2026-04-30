from PyQt5.QtCore import QEventLoop, QTimer, QThread
import traceback
import subprocess
import sys
import socket
import time
import serial
import serial.tools.list_ports
import logging
from Core.platforms import detect
from BarcodeScanner.dispense_command_gate import DispenseCommandGate
from DB.Data.sqlite_db import SessionLocal, engine
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.DeviceConfigCRUD import EngineDeviceConfig
from DB.Engine.HardwareConfigCRUD import EngineHardwareConfig
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
            'cmd_start': lambda *args, **kwargs: self.cmd_start(*args, **kwargs),
            'cmd_test_self': lambda *args, **kwargs: self.cmd_test_self(*args, **kwargs),
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
        self._hal_gate = None
        self._hal_lock_ms_pending = 0
        self._hal_sequence_in_progress = False
        self._db_session = SessionLocal(engine())
        self._e_cell = EngineCell(self._db_session)
        self._e_device_cfg = EngineDeviceConfig(self._db_session)
        self._e_hw_cfg = EngineHardwareConfig(self._db_session)

    def cmd_start(self, *args, **kwargs):
        """
        Точка входа стартового контракта железа.
        Всегда переводит FSM в cmd_test_self через триггер system_start.
        """
        logger.info("cmd_start: trigger system_start")
        return {"trigger": "system_start"}

    def _load_hal_motion_profile(self):
        defaults = {
            "led": 180,
            "lock_ms": 15000,
            "push_down": 900,
            "push_up": 0,
            "park_x": 0,
            "park_z": 0,
            "x_axis_motor": 1,
            "z_axis_motor": 3,
            "push_motor": 5,
        }
        try:
            device_cfg = self._e_device_cfg.get_active()
            if device_cfg:
                hw_cfg = self._e_hw_cfg.get_by_device(device_cfg.id)
                if hw_cfg:
                    defaults.update(
                        {
                            "led": hw_cfg.led_default,
                            "lock_ms": hw_cfg.lock_ms_default,
                            "push_down": hw_cfg.push_down_default,
                            "push_up": hw_cfg.push_up_default,
                            "park_x": hw_cfg.park_x_default,
                            "park_z": hw_cfg.park_z_default,
                            "x_axis_motor": hw_cfg.x_axis_motor,
                            "z_axis_motor": hw_cfg.z_axis_motor,
                            "push_motor": hw_cfg.push_motor,
                        }
                    )
        except Exception as e:
            logger.warning("HAL profile DB fallback to defaults: %s", e)
        return defaults

    def _build_hal_dispense_steps(self, number: int, cell_id=None):
        defaults = self._load_hal_motion_profile()
        try:
            cell_profile = self._e_cell.get_cell_hal_profile(cell_id) if cell_id else None
        except Exception as e:
            logger.warning("Cell HAL profile fallback for cell_id=%s: %s", cell_id, e)
            cell_profile = None
        x = int((cell_profile or {}).get("hal_x") if (cell_profile or {}).get("hal_x") is not None else number)
        z = int((cell_profile or {}).get("hal_z") if (cell_profile or {}).get("hal_z") is not None else 0)

        push_down = int(defaults["push_down"])
        push_up = int(defaults["push_up"])
        park_x = int(defaults["park_x"])
        park_z = int(defaults["park_z"])
        led = int(defaults["led"])
        lock_ms = int(defaults["lock_ms"])

        mot_x = int(defaults["x_axis_motor"])
        mot_z = int(defaults["z_axis_motor"])
        mot_push = int(defaults["push_motor"])

        # Свет -> X/Z -> толкатель вниз/вверх -> парковка -> LOCK,ms
        steps = [
            (f"LED,{led}", False),
            (f"MOT{mot_x},{x}", True),
            (f"MOT{mot_z},{z}", True),
            (f"MOT{mot_push},{push_down}", True),
            (f"MOT{mot_push},{push_up}", True),
            (f"MOT{mot_x},{park_x}", True),
            (f"MOT{mot_z},{park_z}", True),
            # В текущей прошивке LOCK,ms подтверждается OK без DONE:
            # оставляем short и списываем по QTimer lock_ms.
            (f"LOCK,{lock_ms}", False),
        ]
        return steps, lock_ms

    def _ensure_hal_gate(self):
        if self._hal_gate is not None:
            return self._hal_gate
        mgr = self.__executor.controller_serial_manager
        if not mgr or not hasattr(mgr, "command_finished"):
            return None

        gate = DispenseCommandGate(mgr)

        def _on_sequence_failed(idx: int, cmd: str, reason: str):
            self._hal_sequence_in_progress = False
            self.__executor.hardware_last_error = f"dispense_step_{idx}:{cmd}:{reason}"
            self.__executor.handle_controller_serial_response("err_devices")

        def _on_sequence_aborted():
            self._hal_sequence_in_progress = False
            self.__executor.hardware_last_error = "dispense_aborted"
            self.__executor.handle_controller_serial_response("err_devices")

        def _on_sequence_finished():
            self._hal_sequence_in_progress = False
            lock_ms = int(self._hal_lock_ms_pending or 0)
            if lock_ms < 0:
                lock_ms = 0
            QTimer.singleShot(lock_ms, lambda: self.__executor.handle_controller_serial_response("command_ok"))

        gate.sequence_failed.connect(_on_sequence_failed)
        gate.sequence_aborted.connect(_on_sequence_aborted)
        gate.sequence_finished.connect(_on_sequence_finished)

        self._hal_gate = gate
        return gate

    def _wait_hal_command_finished(self, command: str, is_long: bool, timeout_ms: int):
        """
        Отправляет команду в HAL и синхронно ждёт completion через signal command_finished.
        """
        mgr = self.__executor.controller_serial_manager
        if not mgr or not hasattr(mgr, "command_finished"):
            return False, "hal_manager_unavailable"

        result = {"done": False, "ok": False, "reason": "timeout"}
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)

        expected = (command or "").strip().lstrip("$")

        def _on_finished(cmd: str, outcome: str):
            if (cmd or "").strip().lstrip("$") != expected:
                return
            result["done"] = True
            result["reason"] = outcome
            result["ok"] = outcome in ("done", "ok_short")
            if loop.isRunning():
                loop.quit()

        def _on_timeout():
            result["done"] = True
            result["ok"] = False
            result["reason"] = "timeout_wait_completion"
            if loop.isRunning():
                loop.quit()

        mgr.command_finished.connect(_on_finished)
        timer.timeout.connect(_on_timeout)
        timer.start(timeout_ms)

        try:
            if not self.__executor.send_controller_command(expected, is_long=is_long):
                return False, "send_rejected"
            loop.exec_()
        finally:
            try:
                mgr.command_finished.disconnect(_on_finished)
            except Exception:
                pass
            try:
                timer.timeout.disconnect(_on_timeout)
            except Exception:
                pass
            timer.stop()

        return bool(result["ok"]), str(result["reason"])

    def cmd_test_self(self, *args, **kwargs):
        """
        Startup-контракт готовности железа:
        - для legacy: пропускаем без проверки;
        - для atmega_hal: проверка связи + ZERO + парковка в нули.
        """
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        self.__executor.hardware_last_error = ""
        self.__executor.hardware_ready = False

        if protocol != "atmega_hal":
            logger.info("cmd_test_self: legacy mode, skipping HAL startup contract")
            self.__executor.hardware_ready = True
            return {"trigger": "ok"}

        mgr = self.__executor.controller_serial_manager
        if not mgr:
            self.__executor.hardware_last_error = "controller_manager_missing"
            return {"trigger": "err_devices"}

        if hasattr(mgr, "initialize_mock"):
            try:
                mgr.initialize_mock()
            except Exception as e:
                logger.warning("cmd_test_self: mock init failed: %s", e)

        if hasattr(mgr, "check_connection"):
            try:
                if not bool(mgr.check_connection()):
                    self.__executor.hardware_last_error = "serial_port_not_ready"
                    return {"trigger": "err_devices"}
            except Exception as e:
                logger.warning("cmd_test_self: check_connection failed, fallback to serial_conn check: %s", e)

        # Ждём открытия порта (поток serial_manager запускается чуть раньше в main.py).
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            conn = getattr(mgr, "serial_conn", None)
            if conn is not None and getattr(conn, "is_open", False):
                break
            QThread.msleep(50)
        else:
            self.__executor.hardware_last_error = "serial_port_not_ready"
            return {"trigger": "err_devices"}

        defaults = self._load_hal_motion_profile()
        startup_sequence = [
            ("ZERO", True, 120_000),   # калибровка
            (f"MOT{int(defaults['x_axis_motor'])},0", True, 30_000),  # парковка осей
            (f"MOT{int(defaults['z_axis_motor'])},0", True, 30_000),
            (f"MOT{int(defaults['push_motor'])},0", True, 30_000),
            ("LOCK1", False, 5_000),   # держим люк/замок в закрытом состоянии
        ]

        for cmd, is_long, timeout_ms in startup_sequence:
            ok, reason = self._wait_hal_command_finished(cmd, is_long, timeout_ms)
            if not ok:
                self.__executor.hardware_last_error = f"{cmd}:{reason}"
                logger.error("cmd_test_self failed at %s: %s", cmd, reason)
                return {"trigger": "err_devices"}

        self.__executor.hardware_ready = True
        logger.info("cmd_test_self: hardware ready")
        return {"trigger": "ok"}


    def cmd_send(self, number, tool_name, cell_id=None, port='COM30', baudrate=9600, timeout=15, trigger=None, **kwargs):
        # print(f"Отправка команды: {number} | Инструмент: {tool_name} | Порт: {port}")
        if not number:
            logger.warning("cmd_send number: %s is None, tool_name: %s", number, tool_name)
            return {"trigger": "err_devices"}

        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            self.__executor.send_controller_command(str(number))
            return None

        if self._hal_sequence_in_progress:
            logger.warning("HAL dispense is already running")
            return {"trigger": "command_is_send"}

        gate = self._ensure_hal_gate()
        if gate is None:
            self.__executor.hardware_last_error = "dispense_gate_unavailable"
            return {"trigger": "err_devices"}

        try:
            steps, lock_ms = self._build_hal_dispense_steps(int(number), cell_id=cell_id)
        except Exception as e:
            logger.exception("Build HAL steps failed: %s", e)
            self.__executor.hardware_last_error = f"build_steps_failed:{e}"
            return {"trigger": "err_devices"}

        self._hal_lock_ms_pending = lock_ms
        started = gate.run_sequence(steps)
        if not started:
            self.__executor.hardware_last_error = "dispense_sequence_rejected"
            return {"trigger": "err_devices"}

        self._hal_sequence_in_progress = True
        # Сразу переводим FSM в wait-экран; завершение сценария придёт как command_ok после QTimer(lock_ms).
        return {"trigger": "command_is_send"}


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



