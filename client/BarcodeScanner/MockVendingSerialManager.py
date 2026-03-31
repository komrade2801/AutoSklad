"""
Mock ATmega HAL serial device for development and tests.

Imitates line-based responses: OK, DONE, ERROR, LOCK ON/OFF, SENSx_y.
Compatible API with VendingSerialManager (enqueue_command, send_data, Thread+QObject, same signals).

Special command MOCKFAIL — emits ERROR (сценарий «механика сломалась»).
"""

from __future__ import annotations

import queue
import re
import threading
import time
from typing import Dict, Optional

from PyQt5.QtCore import QObject, pyqtSignal


class MockVendingSerialManager(threading.Thread, QObject):
    raw_line = pyqtSignal(str)
    unknown_line = pyqtSignal(str)
    debug_log = pyqtSignal(str)

    event_ok = pyqtSignal()
    event_done = pyqtSignal()
    event_error = pyqtSignal(str)
    event_timeout = pyqtSignal(str)

    event_sensor = pyqtSignal(int, int)
    event_lock_state = pyqtSignal(bool)

    fsm_trigger = pyqtSignal(str)
    command_finished = pyqtSignal(str, str)

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 9600,
        timeout: float = 0.05,
        long_op_delay_s: float = 1.2,
        sens_default: int = 1,
    ):
        threading.Thread.__init__(self, daemon=True)
        QObject.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._long_delay = long_op_delay_s
        self._sensor_values: Dict[int, int] = {}
        for i in range(1, 7):
            self._sensor_values[i] = sens_default

        self._tx_queue: "queue.Queue[str]" = queue.Queue()
        self.running = True

    # --- public API (aligned with VendingSerialManager) ---

    def enqueue_command(self, command: str, is_long: Optional[bool] = None) -> None:
        cmd = (command or "").strip()
        if not cmd:
            self.event_error.emit("empty_command")
            self.debug_log.emit("MockVending: rejected empty command")
            return

        if cmd.startswith("$"):
            cmd = cmd[1:].strip()

        if is_long is None:
            is_long = cmd.startswith("MOT") or cmd == "ZERO"

        self.debug_log.emit(f"MockVending queue {'LONG' if is_long else 'SHORT'}: {cmd}")
        self._tx_queue.put(f"{int(is_long)}|{cmd}")

    def send_data(self, data) -> None:
        """Совместимость с action_cmd.cmd_send (legacy вызов)."""
        self.enqueue_command(str(data))

    def open_port(self) -> None:
        self.debug_log.emit("[MockVending] виртуальный порт открыт")

    def close_port(self) -> None:
        self.debug_log.emit("[MockVending] виртуальный порт закрыт")

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        self.open_port()
        while self.running:
            try:
                packed = self._tx_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                flag_s, cmd = packed.split("|", 1)
                is_long = bool(int(flag_s))
            except ValueError:
                continue
            try:
                self._simulate(is_long, cmd)
            except Exception as exc:
                self.debug_log.emit(f"MockVending simulate error: {exc}")
                self._emit_error(cmd)

        self.close_port()

    # --- simulation ---

    def _simulate(self, is_long: bool, cmd: str) -> None:
        c = cmd.strip()
        u = c.upper()

        if u == "MOCKFAIL" or u.startswith("MOCKFAIL,"):
            self._emit_error(c)
            return

        if u == "LOCK0":
            self._emit_short_ok(c)
            time.sleep(0.02)
            self.raw_line.emit("LOCK OFF")
            self.event_lock_state.emit(False)
            self.debug_log.emit("MockVending: LOCK0 -> LOCK OFF")
            return

        if u == "LOCK1":
            self._emit_short_ok(c)
            time.sleep(0.02)
            self.raw_line.emit("LOCK ON")
            self.event_lock_state.emit(True)
            self.debug_log.emit("MockVending: LOCK1 -> LOCK ON")
            return

        m_sens = re.fullmatch(r"SENS([1-6])", u)
        if m_sens:
            idx = int(m_sens.group(1))
            self._emit_short_ok(c)
            time.sleep(0.02)
            val = self._sensor_values.get(idx, 1)
            line = f"SENS{idx}_{val}"
            self.raw_line.emit(line)
            self.event_sensor.emit(idx, val)
            return

        if u.startswith("LED,"):
            try:
                pwm = int(c.split(",", 1)[1])
            except (ValueError, IndexError):
                self._emit_error(c)
                return
            if 0 <= pwm <= 255:
                self._emit_short_ok(c)
            else:
                self._emit_error(c)
            return

        if re.match(r"^MOT[1-5]_(SPEED|BOOST),", u):
            self._emit_short_ok(c)
            return

        if is_long:
            self._emit_long_ack(c)
            time.sleep(self._long_delay)
            self._emit_long_done(c)
            return

        if u.startswith("LOCK,"):
            self._emit_short_ok(c)
            return

        self.unknown_line.emit(c)
        self.debug_log.emit(f"MockVending: unknown short command {c!r} -> ERROR")
        self._emit_error(c)

    def _emit_short_ok(self, cmd: str) -> None:
        self.raw_line.emit("OK")
        self.event_ok.emit()
        self.fsm_trigger.emit("command_is_send")
        self.command_finished.emit(cmd, "ok_short")

    def _emit_long_ack(self, cmd: str) -> None:
        self.raw_line.emit("OK")
        self.event_ok.emit()
        self.fsm_trigger.emit("command_is_send")

    def _emit_long_done(self, cmd: str) -> None:
        self.raw_line.emit("DONE")
        self.event_done.emit()
        self.fsm_trigger.emit("command_ok")
        self.command_finished.emit(cmd, "done")

    def _emit_error(self, cmd: str) -> None:
        self.raw_line.emit("ERROR")
        self.event_error.emit("device_error")
        self.fsm_trigger.emit("err_devices")
        self.command_finished.emit(cmd, "error")
