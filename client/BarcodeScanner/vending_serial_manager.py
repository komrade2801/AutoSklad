import queue
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import serial
from PyQt5.QtCore import QObject, pyqtSignal


# SPEEDx2 / no_block_plata: ZERO / MOT,* → WAIT then DONE or DONE ZERO / DONE MOT;
# LED/RGB → DONE or DONE LED / DONE RGB; LOCK,SOL → WAIT then DONE LOCK / DONE SOL.


@dataclass
class CommandContext:
    command: str
    """two_phase | done_only | pulse_ack | ok_ack (legacy short OK)."""
    mode: str
    sent_at: float
    ack_deadline: float
    done_deadline: Optional[float] = None
    acked: bool = False


@dataclass
class PendingPulse:
    command: str
    channel: str
    ms: int
    accepted_at: float


class VendingSerialManager(threading.Thread, QObject):
    """
    Line-based UART HAL for ATmega firmware.

    Responses (text + \\n):
    - ZERO / MOT,* : WAIT (ack) then DONE / DONE ZERO / DONE MOT or ERROR
    - LED,* / RGB,* : DONE / DONE LED / DONE RGB (or ERROR), no WAIT/OK
    - LOCK,ms / SOL,ms : WAIT (ack), затем DONE LOCK / DONE SOL по таймеру на MCU
    - Optional legacy: OK as ack for long ops; LOCK0/LOCK1 → LOCK OFF/ON lines
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

    # pulse_ack: WAIT принят, TX свободен; финал — command_finished(..., "done")
    command_accepted = pyqtSignal(str)

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
        bridge_ok_to_fsm: bool = False,
        bridge_done_to_fsm: bool = False,
        bridge_error_to_fsm: bool = True,
    ):
        threading.Thread.__init__(self, daemon=True)
        QObject.__init__(self)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ack_timeout_s = ack_timeout_s
        self.done_timeout_s = done_timeout_s
        self.blocking_margin_s = 2.0
        self.bridge_ok_to_fsm = bridge_ok_to_fsm
        # command_ok в FMS для выдачи шлёт action_cmd после цепочки UART (не bridge DONE).
        self.bridge_done_to_fsm = bridge_done_to_fsm
        self.bridge_error_to_fsm = bridge_error_to_fsm

        self.serial_conn: Optional[serial.Serial] = None
        self.running = False

        # Outbound queue and current command state
        self._tx_queue: "queue.Queue[str]" = queue.Queue()
        self._ctx: Optional[CommandContext] = None
        self._pending_pulses: Dict[str, PendingPulse] = {}

    # -----------------------------
    # Public API (for future usage)
    # -----------------------------
    def is_hardware_busy(self) -> bool:
        """True, если в очереди или на проводе есть HAL-команда (ожидание WAIT/ответа)."""
        return self._ctx is not None or not self._tx_queue.empty()

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

        # Queue flag: long two-phase motion (ZERO, MOT,, legacy MOTn when caller marks long).
        if is_long is None:
            is_long = (
                cmd == "ZERO"
                or cmd.upper().startswith("MOT,")
                or (cmd.upper().startswith("MOT") and "," in cmd)
            )

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

        # Strict serialization: only one in-flight command awaiting first response.
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
        self._ctx = self._build_command_context(cmd, is_long, now)
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
    @staticmethod
    def _pulse_channel(cmd_upper: str) -> Optional[str]:
        if cmd_upper.startswith("LOCK,"):
            return "lock"
        if cmd_upper.startswith("SOL,"):
            return "sol"
        return None

    def _parse_blocking_ms(self, cmd_upper: str) -> int:
        if "," not in cmd_upper:
            return 0
        try:
            return max(0, int(cmd_upper.split(",", 1)[1]))
        except ValueError:
            return 0

    def _build_command_context(self, cmd: str, is_long_flag: bool, now: float) -> CommandContext:
        u = (cmd or "").strip().upper()
        if u.startswith("LED,") or u.startswith("RGB,"):
            ddl = now + self.done_timeout_s
            return CommandContext(
                command=cmd, mode="done_only", sent_at=now, ack_deadline=ddl, done_deadline=ddl
            )
        if u.startswith("LOCK,") or u.startswith("SOL,"):
            return CommandContext(
                command=cmd,
                mode="pulse_ack",
                sent_at=now,
                ack_deadline=now + self.ack_timeout_s,
            )
        if u in ("LOCK0", "LOCK1"):
            return CommandContext(
                command=cmd, mode="ok_ack", sent_at=now, ack_deadline=now + self.ack_timeout_s
            )
        if u == "ZERO" or u.startswith("MOT,") or (is_long_flag and u.startswith("MOT")):
            return CommandContext(
                command=cmd, mode="two_phase", sent_at=now, ack_deadline=now + self.ack_timeout_s
            )
        return CommandContext(
            command=cmd, mode="ok_ack", sent_at=now, ack_deadline=now + self.ack_timeout_s
        )

    def _handle_line(self, line: str) -> None:
        if line == "WAIT":
            self._on_wait_or_ok("WAIT")
            return

        if line == "OK":
            self._on_wait_or_ok("OK")
            return

        if line == "DONE LOCK":
            self._on_tagged_pulse_done("lock")
            return

        if line == "DONE SOL":
            self._on_tagged_pulse_done("sol")
            return

        if self._is_command_done_line(line):
            self.event_done.emit()
            self._on_done_line()
            return

        if line == "ERROR" or line.startswith("ERROR"):
            self.event_error.emit("device_error")
            if self.bridge_error_to_fsm:
                self.fsm_trigger.emit("err_devices")
            self._clear_inflight("error")
            return

        # LOCK0/LOCK1: mock / эталон может слать LOCK OFF / LOCK ON без предварительного OK.
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

    @staticmethod
    def _is_command_done_line(line: str) -> bool:
        """
        Завершение ZERO/MOT/LED/RGB: plain DONE или tagged (SPEEDx2 прошивка).
        DONE LOCK / DONE SOL обрабатываются отдельно (импульсы).
        """
        if line == "DONE":
            return True
        if not line.startswith("DONE "):
            return False
        tag = line[5:].strip().upper()
        return tag in ("ZERO", "MOT", "RGB", "LED")

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
    def _on_wait_or_ok(self, line: str) -> None:
        if self._ctx is None:
            self.debug_log.emit(f"{line} without active context")
            return
        mode = self._ctx.mode
        if mode == "two_phase":
            self._ctx.acked = True
            self._ctx.done_deadline = time.monotonic() + self.done_timeout_s
            self.event_ok.emit()
            if self.bridge_ok_to_fsm:
                self.fsm_trigger.emit("command_is_send")
            return
        if mode == "pulse_ack" and line == "WAIT":
            cmd = self._ctx.command
            u = cmd.upper()
            channel = self._pulse_channel(u)
            if channel is None:
                self.debug_log.emit(f"pulse_ack without channel: {cmd!r}")
                return
            ms = self._parse_blocking_ms(u)
            self._pending_pulses[channel] = PendingPulse(
                command=cmd,
                channel=channel,
                ms=ms,
                accepted_at=time.monotonic(),
            )
            self.event_ok.emit()
            if self.bridge_ok_to_fsm:
                self.fsm_trigger.emit("command_is_send")
            self.command_accepted.emit(cmd)
            self._release_tx_after_accept()
            return
        if mode == "ok_ack" and line == "OK":
            self.event_ok.emit()
            if self.bridge_ok_to_fsm:
                self.fsm_trigger.emit("command_is_send")
            self._clear_inflight("ok_short")
            return
        self.debug_log.emit(f"Ignored {line!r} for mode={mode} cmd={self._ctx.command!r}")

    def _on_tagged_pulse_done(self, channel: str) -> None:
        self.event_done.emit()
        pending = self._pending_pulses.pop(channel, None)
        if pending is None:
            self.debug_log.emit(f"DONE {channel.upper()} without pending pulse")
            return
        if self.bridge_done_to_fsm:
            self.fsm_trigger.emit("command_ok")
        self.command_finished.emit(pending.command, "done")

    def _on_done_line(self) -> None:
        if self._ctx is None:
            self.debug_log.emit("DONE without active context")
            return
        mode = self._ctx.mode
        if mode == "two_phase":
            if not self._ctx.acked:
                self.debug_log.emit("DONE before WAIT/OK — ignored")
                return
            if self.bridge_done_to_fsm:
                self.fsm_trigger.emit("command_ok")
            self._clear_inflight("done")
            return
        if mode == "done_only":
            if self.bridge_done_to_fsm:
                self.fsm_trigger.emit("command_ok")
            self._clear_inflight("done")
            return
        self.debug_log.emit(f"Unexpected DONE in mode={mode}")

    def _release_tx_after_accept(self) -> None:
        if self._ctx is not None:
            self.debug_log.emit(f"TX released after accept: {self._ctx.command}")
        self._ctx = None

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
        ctx = self._ctx

        if ctx.mode == "two_phase":
            if not ctx.acked and now > ctx.ack_deadline:
                self.event_timeout.emit("timeout_ack")
                self.event_error.emit("timeout_ack")
                if self.bridge_error_to_fsm:
                    self.fsm_trigger.emit("err_devices")
                self._clear_inflight("timeout_ack")
                return
            if ctx.acked and ctx.done_deadline is not None and now > ctx.done_deadline:
                self.event_timeout.emit("timeout_done")
                self.event_error.emit("timeout_done")
                if self.bridge_error_to_fsm:
                    self.fsm_trigger.emit("err_devices")
                self._clear_inflight("timeout_done")
            return

        if ctx.mode == "done_only":
            if ctx.done_deadline is not None and now > ctx.done_deadline:
                self.event_timeout.emit("timeout_done")
                self.event_error.emit("timeout_done")
                if self.bridge_error_to_fsm:
                    self.fsm_trigger.emit("err_devices")
                self._clear_inflight("timeout_done")
            return

        if ctx.mode in ("pulse_ack", "ok_ack"):
            if now > ctx.ack_deadline:
                self.event_timeout.emit("timeout_ack")
                self.event_error.emit("timeout_ack")
                if self.bridge_error_to_fsm:
                    self.fsm_trigger.emit("err_devices")
                self._clear_inflight("timeout_ack")
            return
