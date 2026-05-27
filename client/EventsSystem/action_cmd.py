from PyQt5.QtCore import QEventLoop, QTimer, QThread
from PyQt5.QtWidgets import QApplication
import json
import traceback
import subprocess
import sys
import socket
import time
import serial
import serial.tools.list_ports
import logging
from pathlib import Path
from Core.platforms import detect
from BarcodeScanner.dispense_command_gate import DispenseCommandGate
from EventsSystem.hal_coords import (
    HAL_DISPENSE_PUSH_DOWN,
    HAL_DISPENSE_PUSH_UP,
    HAL_JOG_X_INDICES,
    HAL_JOG_Z_INDICES,
    HAL_MOT_PUSH_INDEX,
    format_hal_coords_error,
    MOT_EXCEEDS_MAX_MESSAGE,
    apply_jog_to_motor_positions,
    clamp_mot_vector,
    clamp_motor_value,
    hal_dispense_target_mot5,
    parse_hal_jog_trigger,
    hal_project_hal_xz_from_motors,
    validate_hal_cell_coords,
)
from DB.Data.sqlite_db import SessionLocal, engine
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.DeviceConfigCRUD import EngineDeviceConfig
from DB.Engine.HardwareConfigCRUD import EngineHardwareConfig
# from BarcodeScanner.SerialWorker import SerialWorker  # Используем потоковый класс!

logger = logging.getLogger(__name__)

_CONFIG_JSON = Path(__file__).resolve().parent.parent / "config.json"

# Импульс соленоида после парковки (окно выдачи), мс — прошивка $SOL,ms
HAL_DISPENSE_SOL_MS = 20_000
# Импульс соленоида/замка на экране тестовой выдачи (инженер), мс
HAL_ENGINEER_TEST_PULSE_MS = 10_000

_HAL_JSON_MERGE_KEYS = frozenset(
    {
        "led",
        "lock_ms",
        "sol_ms",
        "push_down",
        "push_up",
        "x_axis_motor",
        "z_axis_motor",
        "push_motor",
        "park_m1",
        "park_m2",
        "park_m3",
        "park_m4",
        "park_m5",
        "rear_safe_m3",
        "rear_safe_m4",
        "rear_safe_first",
        "rgb_issue_r",
        "rgb_issue_g",
        "rgb_issue_b",
    }
)


def _clamp_mot_coord(value: int) -> int:
    v = int(value)
    if v < 0:
        return 0
    if v > 999999:
        return 999999
    return v


def _clamp_rgb_byte(value: int) -> int:
    v = int(value)
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v


def _fmt_mot5(pos):
    """Одна команда $MOT,p1..p5 для no_block_plata (без ведущего $)."""
    clamped = clamp_mot_vector(pos)
    return "MOT," + ",".join(str(p) for p in clamped)


def _motor_index(motor_1_to_5: int, label: str) -> int:
    idx = int(motor_1_to_5) - 1
    if idx < 0 or idx > 4:
        raise ValueError(f"Номер мотора {label} вне 1..5: {motor_1_to_5!r}")
    return idx


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
            'cmd_hal_zero': lambda *args, **kwargs: self.cmd_hal_zero(*args, **kwargs),
            'cmd_hal_park': lambda *args, **kwargs: self.cmd_hal_park(*args, **kwargs),
            'cmd_hal_jog': lambda *args, **kwargs: self.cmd_hal_jog(*args, **kwargs),
            'cmd_hal_mot_goto': lambda *args, **kwargs: self.cmd_hal_mot_goto(*args, **kwargs),
            'cmd_hal_led_toggle': lambda *args, **kwargs: self.cmd_hal_led_toggle(*args, **kwargs),
            'cmd_hal_solenoid': lambda *args, **kwargs: self.cmd_hal_solenoid(*args, **kwargs),
            'cmd_hal_lock': lambda *args, **kwargs: self.cmd_hal_lock(*args, **kwargs),
            'cmd_run_timer_event': lambda *args, **kwargs: self.cmd_run_timer_event(*args, **kwargs),
            'cmd_keyboard_toggle': lambda index: logger.debug("cmd_keyboard_toggle %s", index),
        }
        self._hal_motor_positions = [0, 0, 0, 0, 0]
        self._hal_gate = None
        self._hal_lock_ms_pending = 0
        self._hal_sequence_in_progress = False
        self._hal_led_on = False
        from DB.hardware_config_migrate import migrate_hardware_config_park_motors

        eng = engine()
        migrate_hardware_config_park_motors(eng)
        self._db_session = SessionLocal(eng)
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

    def cmd_run_timer_event(self, *args, **kwargs):
        """После фоновых таймеров/инициализации — допуск в основной UI."""
        logger.debug("cmd_run_timer_event: ready_to_use")
        return {"trigger": "ready_to_use"}

    def _merge_hal_motion_profile_from_json(self, defaults: dict) -> None:
        """Доп. поля из hardware.hal_motion_profile в client/config.json (необязательно)."""
        try:
            if not _CONFIG_JSON.is_file():
                return
            cfg = json.loads(_CONFIG_JSON.read_text(encoding="utf-8"))
            blob = (cfg.get("hardware") or {}).get("hal_motion_profile")
            if not isinstance(blob, dict):
                return
            for k, v in blob.items():
                if k in _HAL_JSON_MERGE_KEYS and v is not None:
                    defaults[k] = v
        except Exception as e:
            logger.warning("hal_motion_profile из config.json не применён: %s", e)

    def _park_motors_from_hw_cfg(self, hw_cfg) -> dict:
        """Парковка M1..M5 из HardwareConfig."""
        return {
            f"park_m{i}": int(getattr(hw_cfg, f"park_m{i}_default", 0))
            for i in range(1, 6)
        }

    def _load_hal_motion_profile(self):
        defaults = {
            "led": 1,
            "lock_ms": 15000,
            "sol_ms": HAL_DISPENSE_SOL_MS,
            "push_down": 900,
            "push_up": 0,
            "park_m1": 0,
            "park_m2": 0,
            "park_m3": 0,
            "park_m4": 0,
            "park_m5": 0,
            "x_axis_motor": 3,
            "z_axis_motor": 1,
            "push_motor": 5,
            "rear_safe_first": False,
            "rear_safe_m3": 0,
            "rear_safe_m4": 0,
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
                            "x_axis_motor": hw_cfg.x_axis_motor,
                            "z_axis_motor": hw_cfg.z_axis_motor,
                            "push_motor": hw_cfg.push_motor,
                            **self._park_motors_from_hw_cfg(hw_cfg),
                        }
                    )
        except Exception as e:
            logger.warning("HAL profile DB fallback to defaults: %s", e)
        self._merge_hal_motion_profile_from_json(defaults)
        if "jog_step" not in defaults:
            defaults["jog_step"] = 100
        return defaults

    def _hal_view_coords_payload(self) -> dict:
        return {
            "trigger": "view_hal_coords",
            "hal_motor_positions": list(self._hal_motor_positions),
        }

    def _hal_view_dispense_payload(self, **extra) -> dict:
        payload = {"trigger": "view_hal_dispense", "hal_led_on": self._hal_led_on}
        payload.update(extra)
        return payload

    def _sync_motor_positions_to_executor(self) -> None:
        self.__executor.hal_motor_positions = list(self._hal_motor_positions)
        try:
            profile = self._load_hal_motion_profile()
            hx, hz = self._project_hal_xz_from_motors(profile)
            self.__executor.hal_projected_x = hx
            self.__executor.hal_projected_z = hz
        except Exception as e:
            logger.warning("HAL projection failed: %s", e)

    def _parse_hal_jog_trigger(self, trigger: str):
        """hal_jog_x_plus -> ('x', +1)."""
        name = (trigger or "").strip().lower()
        if not name.startswith("hal_jog_"):
            return None, 0
        body = name[len("hal_jog_") :]
        if body.endswith("_plus"):
            axis = body[: -len("_plus")]
            sign = 1
        elif body.endswith("_minus"):
            axis = body[: -len("_minus")]
            sign = -1
        else:
            return None, 0
        if axis in ("x", "z", "y"):
            return axis, sign
        if axis in ("m1", "m2", "m3", "m4", "m5"):
            return axis, sign
        return None, 0

    def _jog_motor_indices(self, axis: str, profile: dict) -> list:
        if axis == "x":
            return list(HAL_JOG_X_INDICES)
        if axis == "z":
            return list(HAL_JOG_Z_INDICES)
        if axis == "y":
            return [HAL_MOT_PUSH_INDEX]
        if axis in ("m1", "m2", "m3", "m4", "m5"):
            return [int(axis[1]) - 1]
        return []

    def _project_hal_xz_from_motors(self, profile: dict) -> tuple:
        """Проекция M1..M5 в hal_x (M3) и hal_z (M1)."""
        return hal_project_hal_xz_from_motors(self._hal_motor_positions)

    def _park_vector_five(self, profile: dict) -> list:
        """Парковочный кадр MOT,p1..p5 из park_m1..park_m5 профиля."""
        return [
            clamp_motor_value(int(profile.get(f"park_m{i}", 0)), i - 1)
            for i in range(1, 6)
        ]

    def _illumination_step(self, profile: dict):
        """
        Прошивка: только $LED,0|1. Ненулевой led из БД трактуем как «вкл» (1).
        Если заданы rgb_issue_r/g/b — шаг $RGB,r,g,b.
        """
        if all(
            profile.get(k) is not None
            for k in ("rgb_issue_r", "rgb_issue_g", "rgb_issue_b")
        ):
            r = _clamp_rgb_byte(int(profile["rgb_issue_r"]))
            g = _clamp_rgb_byte(int(profile["rgb_issue_g"]))
            b = _clamp_rgb_byte(int(profile["rgb_issue_b"]))
            return f"RGB,{r},{g},{b}", False
        led_on = 1 if int(profile.get("led", 0)) != 0 else 0
        return f"LED,{led_on}", False

    def _illumination_off_step(self, profile: dict):
        """Гасит ту же подсветку, что включали в начале выдачи (RGB или LED,0)."""
        if all(
            profile.get(k) is not None
            for k in ("rgb_issue_r", "rgb_issue_g", "rgb_issue_b")
        ):
            return "RGB,0,0,0", False
        return "LED,0", False

    def _resolve_hal_target_coords(self, number: int, cell_id=None):
        """
        Целевые hal_x/hal_z только из БД; без fallback на Cell.number / 0.

        Контракт: (coords, coord_err).
        coords — кортеж (hal_x, hal_z) при успехе, иначе None.
        coord_err — строка ошибки или None.
        """
        try:
            cell_profile = self._e_cell.get_cell_hal_profile(cell_id) if cell_id else None
        except Exception as e:
            logger.warning("Cell HAL profile load failed for cell_id=%s: %s", cell_id, e)
            cell_profile = None

        hal_x = (cell_profile or {}).get("hal_x")
        hal_z = (cell_profile or {}).get("hal_z")
        ok, reason = validate_hal_cell_coords(hal_x, hal_z)
        if not ok:
            err = format_hal_coords_error(
                reason,
                cell_id=(cell_profile or {}).get("cell_id", cell_id),
                number=(cell_profile or {}).get("number", number),
            )
            return None, err
        return (int(hal_x), int(hal_z)), None

    def _build_hal_dispense_steps(self, number: int, cell_id=None):
        """
        Цепочка под no_block_plata: кадры MOT,p1..p5 (параллель осей в одном кадре),
        порядок — подсветка (LED/RGB) → ZERO → задняя «безопасная» (опц.) → к ячейке → штырь
        → парковка → $SOL,ms (окно выдачи) → выключение LED/RGB.

        Подъезд к ячейке: M1=M2=hal_z, M3=hal_x, M4=hal_x−25, M5=0; штырь M5: 60 → 0.
        """
        coords, coord_err = self._resolve_hal_target_coords(number, cell_id=cell_id)
        if coord_err:
            raise ValueError(coord_err)
        x, z = coords

        defaults = self._load_hal_motion_profile()

        park = self._park_vector_five(defaults)
        cell_target = list(hal_dispense_target_mot5(x, z))
        steps = [
            self._illumination_step(defaults),
            ("ZERO", True),
        ]

        pos = list(park)
        if bool(defaults.get("rear_safe_first")):
            pos[2] = int(defaults.get("rear_safe_m3", pos[2]))
            pos[3] = int(defaults.get("rear_safe_m4", pos[3]))
            steps.append((_fmt_mot5(pos), True))

        steps.append((_fmt_mot5(list(cell_target)), True))

        pos = list(cell_target)
        pos[HAL_MOT_PUSH_INDEX] = _clamp_mot_coord(HAL_DISPENSE_PUSH_DOWN)
        steps.append((_fmt_mot5(clamp_mot_vector(pos)), True))

        pos = list(cell_target)
        pos[HAL_MOT_PUSH_INDEX] = _clamp_mot_coord(HAL_DISPENSE_PUSH_UP)
        steps.append((_fmt_mot5(clamp_mot_vector(pos)), True))

        steps.append((_fmt_mot5(list(park)), True))

        sol_ms = int(defaults.get("sol_ms", HAL_DISPENSE_SOL_MS))
        if sol_ms < 0:
            sol_ms = 0
        if sol_ms > 65_535:
            sol_ms = 65_535
        steps.append((f"SOL,{sol_ms}", True))
        steps.append(self._illumination_off_step(defaults))

        return steps, 0

    def is_hal_operation_busy(self) -> bool:
        """Цикл выдачи через DispenseCommandGate или флаг активной HAL-последовательности."""
        if self._hal_sequence_in_progress:
            return True
        gate = self._hal_gate
        if gate is not None and gate.is_running():
            return True
        return False

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
            logger.warning(
                "HAL FSM sequence_failed step=%s cmd=%r reason=%s recent_rx=%s",
                idx,
                cmd,
                reason,
                self.__executor.format_hal_rx_snapshot(),
            )
            self.__executor.handle_controller_serial_response("err_devices")

        def _on_sequence_aborted():
            self._hal_sequence_in_progress = False
            self.__executor.hardware_last_error = "dispense_aborted"
            logger.warning(
                "HAL FSM sequence_aborted recent_rx=%s",
                self.__executor.format_hal_rx_snapshot(),
            )
            self.__executor.handle_controller_serial_response("err_devices")

        def _on_sequence_finished():
            self._hal_sequence_in_progress = False
            logger.info(
                "HAL FSM sequence_finished → command_ok recent_rx=%s",
                self.__executor.format_hal_rx_snapshot(),
            )
            ctx = getattr(self.__executor, "engineer_wait_context", None)
            if ctx in ("park", "dispense"):
                self.__executor.handle_controller_serial_response("command_ok_engineer")
            else:
                self.__executor.handle_controller_serial_response("command_ok")

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

        ui_tick = QTimer()
        ui_tick.timeout.connect(lambda: QApplication.processEvents())

        mgr.command_finished.connect(_on_finished)
        timer.timeout.connect(_on_timeout)
        timer.start(timeout_ms)
        ui_tick.start(50)

        try:
            if not self.__executor.send_controller_command(expected, is_long=is_long):
                return False, "send_rejected"
            loop.exec_()
        finally:
            ui_tick.stop()
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
            self.__executor.wait_screen_message = ""
            self.__executor.engineer_wait_context = None
            return {"trigger": "ok"}

        def _fail_startup(err_key: str):
            self.__executor.hardware_last_error = err_key
            self.__executor.wait_screen_message = ""
            self.__executor.engineer_wait_context = None
            return {"trigger": "err_devices"}

        mgr = self.__executor.controller_serial_manager
        if not mgr:
            return _fail_startup("controller_manager_missing")

        if hasattr(mgr, "initialize_mock"):
            try:
                mgr.initialize_mock()
            except Exception as e:
                logger.warning("cmd_test_self: mock init failed: %s", e)

        if hasattr(mgr, "check_connection"):
            try:
                if not bool(mgr.check_connection()):
                    return _fail_startup("serial_port_not_ready")
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
            return _fail_startup("serial_port_not_ready")

        # no_block_plata: только $ZERO и $MOT,p1..p5 (нет LOCK0/LOCK1 на прошивке).
        startup_sequence = [
            ("ZERO", True, 120_000),
            ("MOT,0,0,0,0,0", True, 90_000),
        ]

        for cmd, is_long, timeout_ms in startup_sequence:
            ok, reason = self._wait_hal_command_finished(cmd, is_long, timeout_ms)
            if not ok:
                logger.error(
                    "cmd_test_self failed at %s: %s recent_rx=%s",
                    cmd,
                    reason,
                    self.__executor.format_hal_rx_snapshot(),
                )
                return _fail_startup(f"{cmd}:{reason}")

        self.__executor.hardware_ready = True
        self._hal_motor_positions = [0, 0, 0, 0, 0]
        self._sync_motor_positions_to_executor()
        logger.info(
            "cmd_test_self: hardware ready recent_rx=%s",
            self.__executor.format_hal_rx_snapshot(),
        )
        self.__executor.wait_screen_message = ""
        self.__executor.engineer_wait_context = None
        return {"trigger": "ok"}

    def cmd_hal_zero(self, *args, **kwargs):
        """Homing: только $ZERO (инженер, экран координат)."""
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_coords_payload()

        ok, reason = self._wait_hal_command_finished("ZERO", True, 120_000)
        if not ok:
            self.__executor.hardware_last_error = f"ZERO:{reason}"
            return {"trigger": "err_devices"}

        self._hal_motor_positions = [0, 0, 0, 0, 0]
        self._sync_motor_positions_to_executor()
        payload = self._hal_view_coords_payload()
        payload["hal_zero_ok"] = True
        return payload

    def cmd_hal_park(self, *args, **kwargs):
        """Парковка: MOT,p1..p5 из park_m1..park_m5 профиля."""
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_coords_payload()

        profile = self._load_hal_motion_profile()
        park = self._park_vector_five(profile)
        cmd = _fmt_mot5(park)
        ok, reason = self._wait_hal_command_finished(cmd, True, 90_000)
        if not ok:
            self.__executor.hardware_last_error = f"{cmd}:{reason}"
            return {"trigger": "err_devices"}

        self._hal_motor_positions = list(park)
        self._sync_motor_positions_to_executor()
        payload = self._hal_view_coords_payload()
        payload["hal_park_ok"] = True
        return payload

    def cmd_hal_jog(self, *args, trigger=None, **kwargs):
        """Короткий кадр MOT со сдвигом одной логической оси."""
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_coords_payload()

        jog_trigger = (
            trigger
            or kwargs.get("trigger")
            or getattr(self.__executor, "last_hal_jog_trigger", "")
        )
        axis, sign = parse_hal_jog_trigger(str(jog_trigger))
        if not axis:
            self.__executor.hardware_last_error = f"unknown_jog_trigger:{jog_trigger}"
            return {"trigger": "err_devices"}

        profile = self._load_hal_motion_profile()
        ui_step = getattr(self.__executor, "hal_jog_step", None)
        if ui_step is not None:
            try:
                step = int(ui_step)
            except (TypeError, ValueError):
                step = int(profile.get("jog_step", 50))
        else:
            step = int(profile.get("jog_step", 50))
        if step <= 0:
            step = 50
        pos, limit_hit = apply_jog_to_motor_positions(
            self._hal_motor_positions,
            axis=axis,
            sign=sign,
            step=step,
        )
        if limit_hit:
            return {
                "trigger": "view_hal_coords",
                "hal_motor_positions": pos,
                "hal_input_error": MOT_EXCEEDS_MAX_MESSAGE,
            }

        cmd = _fmt_mot5(pos)
        ok, reason = self._wait_hal_command_finished(cmd, True, 90_000)
        if not ok:
            self.__executor.hardware_last_error = f"{cmd}:{reason}"
            return {"trigger": "err_devices"}

        self._hal_motor_positions = pos
        self._sync_motor_positions_to_executor()
        return self._hal_view_coords_payload()

    def cmd_hal_mot_goto(self, *args, **kwargs):
        """Абсолютный кадр MOT,p1..p5 из полей ввода на screen_38."""
        from EventsSystem.hal_coords import (
            MOT_STEP_MIN,
            message_for_reason,
            mot_axis_max,
            validate_motor_position_texts,
        )

        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_coords_payload()

        raw = kwargs.get("hal_motor_positions")
        if raw is None:
            raw = getattr(self.__executor, "hal_mot_goto_positions", None)
        texts = [str(int(v)) for v in (raw or [])[:5]]
        while len(texts) < 5:
            texts.append("0")
        pos_list, bad_index, reason = validate_motor_position_texts(texts)
        if bad_index is not None:
            label = f"M{bad_index + 1}"
            return {
                "trigger": "view_hal_coords",
                "hal_input_error": message_for_reason(
                    reason,
                    motor_label=label,
                    min_v=MOT_STEP_MIN,
                    max_v=mot_axis_max(bad_index),
                ),
                "hal_motor_positions": list(self._hal_motor_positions),
            }

        pos = clamp_mot_vector(pos_list[:5])
        cmd = _fmt_mot5(pos)
        ok, reason = self._wait_hal_command_finished(cmd, True, 90_000)
        if not ok:
            self.__executor.hardware_last_error = f"{cmd}:{reason}"
            return {"trigger": "err_devices"}

        self._hal_motor_positions = pos
        self._sync_motor_positions_to_executor()
        return self._hal_view_coords_payload()

    def cmd_hal_led_toggle(self, *args, **kwargs):
        """Переключение LED-подсветки ($LED,0|1)."""
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_dispense_payload()

        new_on = not self._hal_led_on
        cmd = f"LED,{1 if new_on else 0}"
        ok, reason = self._wait_hal_command_finished(cmd, False, 15_000)
        if not ok:
            self.__executor.hardware_last_error = f"{cmd}:{reason}"
            return {"trigger": "err_devices"}

        self._hal_led_on = new_on
        return self._hal_view_dispense_payload()

    def cmd_hal_solenoid(self, *args, **kwargs):
        """Импульс соленоида $SOL,ms (тестовая выдача)."""
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_dispense_payload(hal_pulse_cancel="solenoid")

        ms = HAL_ENGINEER_TEST_PULSE_MS
        cmd = f"SOL,{ms}"
        ok, reason = self._wait_hal_command_finished(cmd, True, ms + 5_000)
        if not ok:
            self.__executor.hardware_last_error = f"{cmd}:{reason}"
            return self._hal_view_dispense_payload(hal_pulse_cancel="solenoid")

        return self._hal_view_dispense_payload()

    def cmd_hal_lock(self, *args, **kwargs):
        """Импульс замка $LOCK,ms (тестовая выдача)."""
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return {"trigger": "err_devices"}

        if self._hal_sequence_in_progress:
            return self._hal_view_dispense_payload(hal_pulse_cancel="lock")

        ms = HAL_ENGINEER_TEST_PULSE_MS
        cmd = f"LOCK,{ms}"
        ok, reason = self._wait_hal_command_finished(cmd, True, ms + 5_000)
        if not ok:
            self.__executor.hardware_last_error = f"{cmd}:{reason}"
            return self._hal_view_dispense_payload(hal_pulse_cancel="lock")

        return self._hal_view_dispense_payload()

    def get_hal_motor_positions(self) -> list:
        return list(self._hal_motor_positions)

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

        coords, coord_err = self._resolve_hal_target_coords(int(number), cell_id=cell_id)
        if coord_err:
            self.__executor.hardware_last_error = coord_err
            logger.error("HAL dispense blocked: %s", coord_err)
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
        ctx = getattr(self.__executor, "engineer_wait_context", None)
        if ctx == "dispense":
            self.__executor.wait_screen_message = "Тестовая выдача…"
        # FSM: wait по command_is_send; command_ok после цепочки MOT/LED.
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



