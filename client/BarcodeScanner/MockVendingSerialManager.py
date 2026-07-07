"""
Mock ATmega HAL serial device for development and tests.

С `emulate_no_block_plata=True` повторяет прошивку SPEEDx2:
WAIT+DONE / DONE ZERO / DONE MOT для ZERO/MOT; DONE / DONE LED / DONE RGB для LED/RGB;
LOCK,/SOL, → WAIT, затем DONE LOCK / DONE SOL после ms (не блокирует очередь TX).

Special command MOCKFAIL — emits ERROR (сценарий «механика сломалась»).
"""

from __future__ import annotations

import queue
import re
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

from PyQt5.QtCore import QObject, pyqtSignal


@dataclass
class _PendingPulse:
    command: str
    channel: str


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
    command_accepted = pyqtSignal(str)
    command_finished = pyqtSignal(str, str)

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 9600,
        timeout: float = 0.05,
        long_op_delay_s: float = 1.2,
        sens_default: int = 1,
        bridge_ok_to_fsm: bool = False,
        bridge_done_to_fsm: bool = False,
        bridge_error_to_fsm: bool = True,
        emulate_no_block_plata: bool = False,
        blocking_reply_cap_s: float = 5.0,
    ):
        threading.Thread.__init__(self, daemon=True)
        QObject.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._long_delay = long_op_delay_s
        self.bridge_ok_to_fsm = bridge_ok_to_fsm
        self.bridge_done_to_fsm = bridge_done_to_fsm
        self.bridge_error_to_fsm = bridge_error_to_fsm
        self._emulate_firmware = emulate_no_block_plata
        self._blocking_cap = blocking_reply_cap_s
        self._sensor_values: Dict[int, int] = {}
        for i in range(1, 7):
            self._sensor_values[i] = sens_default

        self._tx_queue: "queue.Queue[str]" = queue.Queue()
        self.running = True
        self._simulating = False
        self._lock_is_on = False
        self._pending_pulses: Dict[str, _PendingPulse] = {}
        self.serial_conn = None

    class _MockSerialConnection:
        def __init__(self) -> None:
            self.is_open = True

    def is_hardware_busy(self) -> bool:
        """True, если mock обрабатывает команду или в очереди TX есть шаги."""
        return self._simulating or not self._tx_queue.empty()

    def enqueue_command(self, command: str, is_long: Optional[bool] = None) -> None:
        cmd = (command or "").strip()
        if not cmd:
            self.event_error.emit("empty_command")
            self.debug_log.emit("MockVending: rejected empty command")
            return

        if cmd.startswith("$"):
            cmd = cmd[1:].strip()

        if is_long is None:
            cu = cmd.upper()
            is_long = (
                cu == "ZERO"
                or cu.startswith("MOT,")
                or (cu.startswith("MOT") and "," in cmd)
            )

        self.debug_log.emit(f"MockVending queue {'LONG' if is_long else 'SHORT'}: {cmd}")
        self._tx_queue.put(f"{int(is_long)}|{cmd}")

    def send_data(self, data) -> None:
        """Совместимость с action_cmd.cmd_send (legacy вызов)."""
        self.enqueue_command(str(data))

    def open_port(self) -> None:
        self.serial_conn = self._MockSerialConnection()
        self.debug_log.emit("[MockVending] виртуальный порт открыт")

    def close_port(self) -> None:
        if self.serial_conn is not None:
            self.serial_conn.is_open = False
        self.debug_log.emit("[MockVending] виртуальный порт закрыт")

    def check_connection(self) -> bool:
        conn = self.serial_conn
        return conn is not None and bool(getattr(conn, "is_open", False))

    def initialize_mock(self) -> None:
        for i in range(1, 7):
            if i not in self._sensor_values:
                self._sensor_values[i] = 1
        self._lock_is_on = True
        self.debug_log.emit("[MockVending] mock инициализирован")

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
            self._simulating = True
            try:
                self._simulate(is_long, cmd)
            except Exception as exc:
                self.debug_log.emit(f"MockVending simulate error: {exc}")
                self._emit_error(cmd)
            finally:
                self._simulating = False

        self.close_port()

    @staticmethod
    def _parse_blocking_ms(u: str) -> int:
        if "," not in u:
            return 0
        try:
            return max(0, int(u.split(",", 1)[1]))
        except ValueError:
            return 0

    @staticmethod
    def _pulse_channel(u: str) -> Optional[str]:
        if u.startswith("LOCK,"):
            return "lock"
        if u.startswith("SOL,"):
            return "sol"
        return None

    def _mot_csv_five_valid(self, c: str) -> bool:
        if "," not in c:
            return False
        rest = c.split(",", 1)[1]
        vals = [x.strip() for x in rest.split(",")]
        if len(vals) != 5:
            return False
        try:
            for x in vals:
                v = int(x)
                if v > 999999:
                    return False
        except ValueError:
            return False
        return True

    def _schedule_pulse_done(self, cmd: str, channel: str, delay_s: float) -> None:
        done_line = "DONE LOCK" if channel == "lock" else "DONE SOL"

        def _worker() -> None:
            time.sleep(delay_s)
            pending = self._pending_pulses.pop(channel, None)
            if pending is None or pending.command != cmd:
                self.debug_log.emit(
                    f"MockVending: stale pulse done ignored channel={channel} cmd={cmd!r}"
                )
                return
            self.raw_line.emit(done_line)
            self.event_done.emit()
            if self.bridge_done_to_fsm:
                self.fsm_trigger.emit("command_ok")
            self.command_finished.emit(cmd, "done")
            self.debug_log.emit(f"MockVending: {done_line} for {cmd!r}")

        threading.Thread(target=_worker, daemon=True).start()

    def _emit_pulse_ack(self, cmd: str, u: str) -> None:
        channel = self._pulse_channel(u)
        if channel is None:
            self._emit_error(cmd)
            return
        ms = self._parse_blocking_ms(u)
        delay = min(ms / 1000.0 + 0.05, self._blocking_cap)
        self._pending_pulses[channel] = _PendingPulse(command=cmd, channel=channel)
        self.raw_line.emit("WAIT")
        self.event_ok.emit()
        if self.bridge_ok_to_fsm:
            self.fsm_trigger.emit("command_is_send")
        self.command_accepted.emit(cmd)
        self.debug_log.emit(f"MockVending: WAIT pulse_ack {cmd!r}")
        self._schedule_pulse_done(cmd, channel, delay)

    def _simulate_firmware(self, is_long: bool, c: str, u: str) -> bool:
        if u.startswith("LED,"):
            try:
                pwm = int(c.split(",", 1)[1])
            except (ValueError, IndexError):
                self._emit_error(c)
                return True
            if 0 <= pwm <= 255:
                self._emit_done_only(c)
            else:
                self._emit_error(c)
            return True

        if u.startswith("RGB,"):
            parts = c.split(",", 3)
            if len(parts) < 4:
                self._emit_error(c)
                return True
            try:
                for p in parts[1:4]:
                    v = int(p.strip())
                    if not 0 <= v <= 255:
                        raise ValueError
            except ValueError:
                self._emit_error(c)
                return True
            self._emit_done_only(c)
            return True

        if u.startswith("LOCK,") or u.startswith("SOL,"):
            self._emit_pulse_ack(c, u)
            return True

        if u == "ZERO":
            self._emit_firmware_two_phase(c)
            return True

        if u.startswith("MOT,"):
            if not self._mot_csv_five_valid(c):
                self._emit_error(c)
                return True
            self._emit_firmware_two_phase(c)
            return True

        if is_long and u.startswith("MOT") and "," in c:
            self._emit_firmware_two_phase(c)
            return True

        return False

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
            self._lock_is_on = False
            self.debug_log.emit("MockVending: LOCK0 -> LOCK OFF")
            return

        if u == "LOCK1":
            self._emit_short_ok(c)
            time.sleep(0.02)
            self.raw_line.emit("LOCK ON")
            self.event_lock_state.emit(True)
            self._lock_is_on = True
            self.debug_log.emit("MockVending: LOCK1 -> LOCK ON")
            return

        if self._emulate_firmware and self._simulate_firmware(is_long, c, u):
            return

        if u in ("PING", "HELLO"):
            self._emit_short_ok(c)
            return

        if u == "INIT":
            self.initialize_mock()
            self._emit_short_ok(c)
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
        if self.bridge_ok_to_fsm:
            self.fsm_trigger.emit("command_is_send")
        self.command_finished.emit(cmd, "ok_short")

    def _emit_done_only(self, cmd: str) -> None:
        self.raw_line.emit("DONE")
        self.event_done.emit()
        if self.bridge_done_to_fsm:
            self.fsm_trigger.emit("command_ok")
        self.command_finished.emit(cmd, "done")

    def _emit_firmware_two_phase(self, cmd: str) -> None:
        self.raw_line.emit("WAIT")
        self.event_ok.emit()
        if self.bridge_ok_to_fsm:
            self.fsm_trigger.emit("command_is_send")
        time.sleep(self._long_delay)
        self.raw_line.emit("DONE")
        self.event_done.emit()
        if self.bridge_done_to_fsm:
            self.fsm_trigger.emit("command_ok")
        self.command_finished.emit(cmd, "done")

    def _emit_long_ack(self, cmd: str) -> None:
        self.raw_line.emit("OK")
        self.event_ok.emit()
        if self.bridge_ok_to_fsm:
            self.fsm_trigger.emit("command_is_send")

    def _emit_long_done(self, cmd: str) -> None:
        self.raw_line.emit("DONE")
        self.event_done.emit()
        if self.bridge_done_to_fsm:
            self.fsm_trigger.emit("command_ok")
        self.command_finished.emit(cmd, "done")

    def _emit_error(self, cmd: str) -> None:
        self.raw_line.emit("ERROR")
        self.event_error.emit("device_error")
        if self.bridge_error_to_fsm:
            self.fsm_trigger.emit("err_devices")
        self.command_finished.emit(cmd, "error")
