import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

import serial
from PyQt5.QtCore import QObject, pyqtSignal


@dataclass
class CommandContext:
    command: str
    is_long: bool
    sent_at: float
    ack_deadline: float
    done_deadline: Optional[float] = None
    acked: bool = False


class VendingSerialManager(threading.Thread, QObject):
    """
    v0 line-based serial manager for new ATmega firmware.

    It is intentionally standalone and not wired into the app yet.
    Expected line responses:
    - OK
    - DONE
    - ERROR
    - SENSx_0 / SENSx_1
    - LOCK ON / LOCK OFF
    """

    # Raw diagnostics
    raw_line = pyqtSignal(str)
    unknown_line = pyqtSignal(str)
    debug_log = pyqtSignal(str)

    # Generic events
    event_ok = pyqtSignal()
    event_done = pyqtSignal()
    event_error = pyqtSignal(str)
    event_timeout = pyqtSignal(str)  # timeout_ack / timeout_done

    # Typed events
    event_sensor = pyqtSignal(int, int)  # sensor_index, 0/1
    event_lock_state = pyqtSignal(bool)  # True=LOCK ON(closed), False=LOCK OFF(open)

    # Legacy/FSM bridge events for future easy integration
    fsm_trigger = pyqtSignal(str)  # command_is_send / command_ok / err_devices

    # Correlation: one emission per logical completion of the in-flight UART command.
    # outcome: ok_short | done | error | timeout_ack | timeout_done
    command_finished = pyqtSignal(str, str)

    def __init__(
        self,
        port: str = "COM30",
        baudrate: int = 9600,
        timeout: float = 0.05,
        ack_timeout_s: float = 2.0,
        done_timeout_s: float = 90.0,
    ):
        threading.Thread.__init__(self, daemon=True)
        QObject.__init__(self)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ack_timeout_s = ack_timeout_s
        self.done_timeout_s = done_timeout_s

        self.serial_conn: Optional[serial.Serial] = None
        self.running = False

        # Outbound queue and current command state
        self._tx_queue: "queue.Queue[str]" = queue.Queue()
        self._ctx: Optional[CommandContext] = None

    # -----------------------------
    # Public API (for future usage)
    # -----------------------------
    def enqueue_command(self, command: str, is_long: Optional[bool] = None) -> None:
        """
        Enqueue command WITHOUT leading '$' and WITHOUT line ending.
        Example: 'ZERO', 'MOT1,500', 'LOCK,15000'.
        """
        cmd = (command or "").strip()
        if not cmd:
            self.event_error.emit("empty_command")
            self.debug_log.emit("Rejected empty command")
            return

        if cmd.startswith("$"):
            cmd = cmd[1:].strip()

        # v0 heuristic: MOT*, ZERO, and LOCK,ms need OK then DONE (Sketch: OK, delay, DONE).
        if is_long is None:
            is_long = cmd.startswith("MOT") or cmd == "ZERO" or cmd.startswith("LOCK,")

        marker = "LONG" if is_long else "SHORT"
        self.debug_log.emit(f"Queue {marker}: {cmd}")
        self._tx_queue.put(f"{int(is_long)}|{cmd}")

    def send_data(self, data) -> None:
        """Совместимость с action_cmd.cmd_send и legacy SerialManager."""
        self.enqueue_command(str(data))

    def stop(self) -> None:
        self.running = False

    def open_port(self) -> None:
        self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.debug_log.emit(f"Port opened: {self.port} @ {self.baudrate}")

    def close_port(self) -> None:
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.debug_log.emit(f"Port closed: {self.port}")

    # -----------------------------
    # Thread loop
    # -----------------------------
    def run(self) -> None:
        self.running = True
        try:
            self.open_port()
        except Exception as exc:
            self.event_error.emit(f"port_open_error:{exc}")
            self.debug_log.emit(f"Failed to open port: {exc}")
            self.running = False
            return

        try:
            while self.running:
                self._pump_outbound()
                self._pump_inbound()
                self._check_timeouts()
                time.sleep(0.005)
        finally:
            self.close_port()

    # -----------------------------
    # Internal send/receive
    # -----------------------------
    def _pump_outbound(self) -> None:
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        # Strict serialization: only one in-flight command.
        if self._ctx is not None:
            return

        if self._tx_queue.empty():
            return

        packed = self._tx_queue.get()
        long_marker, cmd = packed.split("|", 1)
        is_long = bool(int(long_marker))

        payload = f"${cmd}\n".encode("ascii", errors="ignore")
        self.serial_conn.write(payload)

        now = time.monotonic()
        self._ctx = CommandContext(
            command=cmd,
            is_long=is_long,
            sent_at=now,
            ack_deadline=now + self.ack_timeout_s,
        )
        self.debug_log.emit(f"Sent: {payload!r}")

    def _pump_inbound(self) -> None:
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        try:
            raw = self.serial_conn.readline()
        except Exception as exc:
            self.event_error.emit(f"read_error:{exc}")
            self.debug_log.emit(f"Read error: {exc}")
            return

        if not raw:
            return

        line = raw.decode("utf-8", errors="ignore").strip()
        if not line:
            return

        self.raw_line.emit(line)
        self._handle_line(line)

    # -----------------------------
    # Protocol handling
    # -----------------------------
    def _handle_line(self, line: str) -> None:
        if line == "OK":
            self.event_ok.emit()
            self.fsm_trigger.emit("command_is_send")
            self._on_ok()
            return

        if line == "DONE":
            self.event_done.emit()
            self.fsm_trigger.emit("command_ok")
            self._on_done()
            return

        if line == "ERROR":
            self.event_error.emit("device_error")
            self.fsm_trigger.emit("err_devices")
            self._clear_inflight("error")
            return

        # LOCK0/LOCK1: прошивка шлёт только LOCK OFF / LOCK ON без OK — завершаем полёт команды здесь.
        if line == "LOCK OFF":
            self.event_lock_state.emit(False)
            self.debug_log.emit("Lock state: OFF")
            if self._ctx is not None and self._ctx.command.upper() == "LOCK0":
                self._clear_inflight("ok_short")
            return

        if line == "LOCK ON":
            self.event_lock_state.emit(True)
            self.debug_log.emit("Lock state: ON")
            if self._ctx is not None and self._ctx.command.upper() == "LOCK1":
                self._clear_inflight("ok_short")
            return

        if line.startswith("SENS") and "_" in line:
            parsed = self._parse_sensor(line)
            if parsed is not None:
                sensor_idx, sensor_val = parsed
                self.event_sensor.emit(sensor_idx, sensor_val)
                return

        self.unknown_line.emit(line)
        self.debug_log.emit(f"Unknown line: {line}")

    def _parse_sensor(self, line: str) -> Optional[tuple]:
        # Expected: SENS1_0 ... SENS6_1
        try:
            head, val = line.split("_", 1)
            if not head.startswith("SENS"):
                return None
            idx_str = head[4:]
            idx = int(idx_str)
            state = int(val)
            if idx < 1 or idx > 6:
                return None
            if state not in (0, 1):
                return None
            return idx, state
        except Exception:
            return None

    # -----------------------------
    # In-flight lifecycle
    # -----------------------------
    def _on_ok(self) -> None:
        if self._ctx is None:
            # OK can be emitted by commands initiated elsewhere; ignore safely.
            self.debug_log.emit("OK without active context")
            return

        self._ctx.acked = True
        if self._ctx.is_long:
            self._ctx.done_deadline = time.monotonic() + self.done_timeout_s
        else:
            self._clear_inflight("ok_short")

    def _on_done(self) -> None:
        if self._ctx is None:
            self.debug_log.emit("DONE without active context")
            return
        self._clear_inflight("done")

    def _clear_inflight(self, reason: str) -> None:
        old_cmd = self._ctx.command if self._ctx else ""
        if self._ctx is not None:
            self.debug_log.emit(f"Clear in-flight ({reason}): {self._ctx.command}")
        self._ctx = None
        if old_cmd:
            self.command_finished.emit(old_cmd, reason)

    def _check_timeouts(self) -> None:
        if self._ctx is None:
            return

        now = time.monotonic()

        if not self._ctx.acked and now > self._ctx.ack_deadline:
            self.event_timeout.emit("timeout_ack")
            self.event_error.emit("timeout_ack")
            self.fsm_trigger.emit("err_devices")
            self._clear_inflight("timeout_ack")
            return

        if self._ctx.is_long and self._ctx.acked and self._ctx.done_deadline is not None:
            if now > self._ctx.done_deadline:
                self.event_timeout.emit("timeout_done")
                self.event_error.emit("timeout_done")
                self.fsm_trigger.emit("err_devices")
                self._clear_inflight("timeout_done")
