from PyQt5 import QtCore, QtWidgets

from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_42_hal_terminal import Ui_screen_42_hal_terminal

logger = get_logger(__name__)

_HELP_TEXT = """\
Команды (без $, Enter — отправить):
  ZERO          — все моторы в ноль
  ZERO,n        — мотор n (1..5) в ноль
  MOT,p1..p5    — позиции моторов 1..5
  LED,0|1       — лента выкл/вкл
  RGB,r,g,b     — адресная лента
  LOCK,ms       — импульс замка, мс
  SOL,ms        — импульс соленоида, мс
  c,n / f / g   — наследие монолита (осторожно)
Локально: clear — очистить лог; help — эта справка
"""


class screen_42_hal_terminal(BaseScreen, Ui_screen_42_hal_terminal):
    _LOG_LINE_LIMIT = 400

    def __init__(self):
        super().__init__()
        self._executor = None
        self._serial_manager = None
        self._log_line_count = 0
        self.setupUi(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.edit_cmd.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.btn_back.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_clear.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_help.setFocusPolicy(QtCore.Qt.NoFocus)
        self.te_log.setFocusPolicy(QtCore.Qt.NoFocus)
        log_idx = self.verticalLayout.indexOf(self.te_log)
        if log_idx >= 0:
            self.verticalLayout.setStretch(log_idx, 1)
        self.normalize_screen_geometry()

    def attach_executor(self, executor) -> None:
        self._executor = executor

    def showEvent(self, event):
        super().showEvent(event)
        if self._executor is not None:
            self._executor.hal_terminal_active = True
        self._connect_serial()
        self._refresh_status()
        self.edit_cmd.clear()
        self.edit_cmd.setFocus(QtCore.Qt.OtherFocusReason)

    def hideEvent(self, event):
        self._disconnect_serial()
        if self._executor is not None:
            self._executor.hal_terminal_active = False
        super().hideEvent(event)

    def _serial_mgr(self):
        if self._executor is None:
            return None
        return getattr(self._executor, "controller_serial_manager", None)

    def _connect_serial(self) -> None:
        mgr = self._serial_mgr()
        if mgr is None or mgr is self._serial_manager:
            return
        self._disconnect_serial()
        self._serial_manager = mgr
        if hasattr(mgr, "raw_line"):
            mgr.raw_line.connect(self._on_raw_line)

    def _disconnect_serial(self) -> None:
        mgr = self._serial_manager
        if mgr is None:
            return
        try:
            mgr.raw_line.disconnect(self._on_raw_line)
        except (TypeError, RuntimeError):
            pass
        self._serial_manager = None

    def _refresh_status(self) -> None:
        if self._executor is None:
            self.lbl_status.setText("Нет подключения к Executor")
            return
        protocol = (getattr(self._executor, "controller_protocol", "") or "").strip().lower()
        if protocol != "atmega_hal":
            self.lbl_status.setText("Только для протокола atmega_hal")
            return
        mgr = self._serial_mgr()
        if mgr is None:
            self.lbl_status.setText("Serial manager не инициализирован")
            return
        conn = getattr(mgr, "serial_conn", None)
        if conn is not None and getattr(conn, "is_open", False):
            busy = ""
            if hasattr(mgr, "is_hardware_busy") and mgr.is_hardware_busy():
                busy = " · очередь UART занята"
            self.lbl_status.setText(f"Подключено{busy}")
        else:
            self.lbl_status.setText("Порт UART не открыт")

    def _trim_log_if_needed(self) -> None:
        if self._log_line_count <= self._LOG_LINE_LIMIT:
            return
        lines = self.te_log.toPlainText().splitlines()
        if len(lines) <= self._LOG_LINE_LIMIT:
            self._log_line_count = len(lines)
            return
        kept = lines[-self._LOG_LINE_LIMIT :]
        self.te_log.setPlainText("\n".join(kept))
        self._log_line_count = len(kept)
        bar = self.te_log.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _append_log(self, text: str) -> None:
        line = (text or "").rstrip("\r\n")
        if not line:
            return
        self.te_log.appendPlainText(line)
        self._log_line_count += 1
        self._trim_log_if_needed()
        bar = self.te_log.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_raw_line(self, line: str) -> None:
        self._append_log(line)
        self._refresh_status()

    def clear_log(self) -> None:
        self.te_log.clear()
        self._log_line_count = 0

    def show_help(self) -> None:
        self._append_log(_HELP_TEXT.strip())

    def on_command_entered(self) -> None:
        raw = self.edit_cmd.text().strip()
        self.edit_cmd.clear()
        if not raw:
            return

        lower = raw.lower()
        if lower == "clear":
            self.clear_log()
            return
        if lower == "help":
            self.show_help()
            return

        cmd = raw.lstrip("$").strip()
        if not cmd:
            return

        self._append_log(f"> {cmd}")

        if self._executor is None:
            self._append_log("[ERR] Executor не подключён")
            return

        protocol = (getattr(self._executor, "controller_protocol", "") or "").strip().lower()
        if protocol != "atmega_hal":
            self._append_log("[ERR] Терминал доступен только при atmega_hal")
            return

        selector = getattr(self._executor, "selector", None)
        mapper = selector.mappers.get("cmd") if selector is not None else None
        if mapper is not None and hasattr(mapper, "is_hal_operation_busy"):
            if mapper.is_hal_operation_busy():
                self._append_log(
                    "[ERR] Идёт HAL-операция (выдача/JOG). Дождитесь завершения."
                )
                return

        if not self._executor.send_controller_command(cmd):
            self._append_log("[ERR] Не удалось поставить команду в очередь UART")
            return

        self._refresh_status()
        QtCore.QTimer.singleShot(100, self.edit_cmd.setFocus)

    def set_data(self, *args, **kwargs):
        pass

    def get_data(self):
        return None
