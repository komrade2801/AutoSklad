"""
Sequential high-level command gate on top of VendingSerialManager.

Correlates each hardware completion with the exact command string using
VendingSerialManager.command_finished (not anonymous event_done alone).

Thread-safety:
    All mutable orchestration state is guarded by a threading.Lock.
    Qt slots may run on the GUI thread or be queued from the serial worker;
    the lock keeps _kick / _on_command_finished / abort mutually consistent.

Typical usage (from GUI thread after wiring):
    gate = DispenseCommandGate(mgr)
    gate.run_sequence([("MOT1,100", True), ("MOT2,200", True), ("LOCK,15000", False)])
"""

from __future__ import annotations

import logging
import threading
from typing import List, Optional, Tuple

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from BarcodeScanner.vending_serial_manager import VendingSerialManager

logger = logging.getLogger(__name__)

DispenseStep = Tuple[str, bool]

HAL_DELAY_STEP_PREFIX = "__HAL_DELAY_MS:"


def hal_delay_step(ms: int) -> DispenseStep:
    """Пауза между UART-шагами без отправки команды на плату."""
    delay_ms = max(0, int(ms))
    return (f"{HAL_DELAY_STEP_PREFIX}{delay_ms}", False)


def _parse_hal_delay_ms(command: str) -> Optional[int]:
    cmd = (command or "").strip()
    if not cmd.startswith(HAL_DELAY_STEP_PREFIX):
        return None
    try:
        return max(0, int(cmd[len(HAL_DELAY_STEP_PREFIX) :]))
    except ValueError:
        return 0


class DispenseCommandGate(QObject):
    """Executes a list of UART commands one after another; each step waits for driver completion."""

    step_started = pyqtSignal(int, str)  # index, command
    step_completed = pyqtSignal(int, str, str)  # index, command, outcome (done|ok_short)
    sequence_finished = pyqtSignal()
    sequence_failed = pyqtSignal(int, str, str)  # index, command_or_empty, reason
    sequence_aborted = pyqtSignal()

    def __init__(self, serial_manager: VendingSerialManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._serial = serial_manager
        self._lock = threading.Lock()
        self._steps: List[DispenseStep] = []
        self._index = 0
        self._running = False
        self._expected_cmd: Optional[str] = None
        self._expected_long = False
        self._delay_timer: Optional[QTimer] = None

        self._serial.command_finished.connect(self._on_command_finished)

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def run_sequence(self, steps: List[DispenseStep]) -> bool:
        """
        Start a new sequence. Returns False if a sequence is already running.
        """
        cleaned: List[DispenseStep] = []
        for item in steps:
            if not item:
                continue
            cmd, is_long = item[0], item[1]
            c = (cmd or "").strip()
            if c.startswith("$"):
                c = c[1:].strip()
            if not c:
                continue
            cleaned.append((c, bool(is_long)))

        with self._lock:
            if self._running:
                logger.warning("DispenseCommandGate: run_sequence rejected (already running)")
                return False
            if not cleaned:
                logger.warning("DispenseCommandGate: run_sequence rejected (empty)")
                return False
            self._steps = cleaned
            self._index = 0
            self._running = True
            self._expected_cmd = None
            self._expected_long = False

        self._kick()
        return True

    def abort(self) -> None:
        """Stop orchestration; does not flush the driver's low-level TX queue."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._expected_cmd = None
        if self._delay_timer is not None:
            self._delay_timer.stop()
            self._delay_timer = None
        self.sequence_aborted.emit()

    def _kick(self) -> None:
        cmd_to_send: Optional[str] = None
        is_long: bool = False
        idx: int = 0
        emit_finished_only = False

        with self._lock:
            if not self._running:
                return
            if self._expected_cmd is not None:
                # Waiting for UART completion for the current step.
                return
            if self._index >= len(self._steps):
                self._running = False
                emit_finished_only = True
            else:
                cmd_to_send, is_long = self._steps[self._index]
                self._expected_cmd = cmd_to_send
                self._expected_long = is_long
                idx = self._index

        if emit_finished_only:
            self.sequence_finished.emit()
            return

        assert cmd_to_send is not None
        self.step_started.emit(idx, cmd_to_send)

        delay_ms = _parse_hal_delay_ms(cmd_to_send)
        if delay_ms is not None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self._on_delay_finished)
            self._delay_timer = timer
            timer.start(delay_ms)
            return

        self._serial.enqueue_command(cmd_to_send, is_long)

    def _on_delay_finished(self) -> None:
        self._delay_timer = None
        with self._lock:
            if not self._running or self._expected_cmd is None:
                return
            cmd = self._expected_cmd
            idx = self._index
            self._index += 1
            self._expected_cmd = None
            emit_sequence_done = self._index >= len(self._steps)
            if emit_sequence_done:
                self._running = False
            need_kick = not emit_sequence_done

        self.step_completed.emit(idx, cmd, "delay")
        if emit_sequence_done:
            self.sequence_finished.emit()
            return
        if need_kick:
            self._kick()

    def _on_command_finished(self, cmd: str, outcome: str) -> None:
        """
        Driver emits one completion per in-flight command, with the exact command string.
        """
        emit_failed = False
        fail_idx = 0
        fail_cmd = ""
        fail_reason = ""

        emit_step_done = False
        done_idx = 0
        done_cmd = ""
        done_out = ""

        emit_sequence_done = False
        need_kick = False

        with self._lock:
            if not self._running:
                return
            if self._expected_cmd is None:
                logger.debug(
                    "DispenseCommandGate: stray command_finished %r (%s) — ignored",
                    cmd,
                    outcome,
                )
                return

            if cmd != self._expected_cmd:
                exp = self._expected_cmd
                idx = self._index
                self._running = False
                self._expected_cmd = None
                emit_failed = True
                fail_idx = idx
                fail_cmd = cmd
                fail_reason = f"correlation_mismatch: got {cmd!r} expected {exp!r} ({outcome})"
            else:
                want_done = self._expected_long
                if want_done:
                    success = outcome == "done"
                else:
                    # HAL LED/RGB завершаются одной строкой DONE без WAIT.
                    success = outcome in ("ok_short", "done")
                idx = self._index
                cur_cmd = cmd
                if not success:
                    self._running = False
                    self._expected_cmd = None
                    emit_failed = True
                    fail_idx = idx
                    fail_cmd = cur_cmd
                    fail_reason = outcome
                else:
                    emit_step_done = True
                    done_idx = idx
                    done_cmd = cur_cmd
                    done_out = outcome
                    self._index += 1
                    self._expected_cmd = None
                    if self._index >= len(self._steps):
                        self._running = False
                        emit_sequence_done = True
                    else:
                        need_kick = True

        if emit_failed:
            self.sequence_failed.emit(fail_idx, fail_cmd, fail_reason)
            return

        if emit_step_done:
            self.step_completed.emit(done_idx, done_cmd, done_out)

        if emit_sequence_done:
            self.sequence_finished.emit()
            return

        if need_kick:
            self._kick()
