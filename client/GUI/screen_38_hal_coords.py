from PyQt5 import QtCore, QtGui, QtWidgets

from Core.app_logging import get_logger
from EventsSystem.hal_coords import (
    CELL_NUMBER_MAX,
    CELL_NUMBER_MIN,
    MOT_EXCEEDS_MAX_MESSAGE,
    MOT_STEP_MIN,
    apply_jog_to_motor_positions,
    clamp_motor_text,
    hal_mot4_from_hal_x,
    message_for_reason,
    mot_axis_max,
    parse_hal_jog_trigger,
    validate_cell_number_text,
    validate_hal_cell_coords,
)
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_38_hal_coords import Ui_screen_38_hal_coords
from GUI.widgets.widget_hal_jog_panel import WidgetHalJogPanel
from GUI.widgets.widget_keyboard import WidgetKeyboard

logger = get_logger(__name__)


def _motor_index_from_jog_trigger(trigger_name: str):
    name = (trigger_name or "").strip().lower()
    if name.startswith("hal_jog_z"):
        return 0
    if not name.startswith("hal_jog_m"):
        return None
    body = name[len("hal_jog_m") :]
    if body[:1].isdigit():
        idx = int(body[0]) - 1
        if 0 <= idx <= 4:
            return idx
    return None


class screen_38_hal_coords(BaseScreen, Ui_screen_38_hal_coords):
    _CELL_LABEL_MIN_WIDTH = 111
    _CELL_NUMBER_SHIFT_LEFT_PX = 30
    _KEYBOARD_CLOSE_MS = 350
    JOG_STEP_OPTIONS = (1, 5, 10, 50, 100)
    DEFAULT_JOG_STEP = 50
    _EDIT_CELL_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 18px; }"
    )
    _EDIT_CELL_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 18px; }"
    )
    _LBL_CELL_MOT_DEFAULT = "(0, 0, 0)"
    _BTN_SAVE_OK = (
        "QPushButton { color: #FFFFFF; background-color: #2d7a3e;"
        "border-radius: 8px; font-size: 20px; font-weight: 600; min-height: 48px; }"
    )
    _SAVE_OK_MS = 3000

    def __init__(self):
        super().__init__()
        self.event_hal_jog = None
        self.event_hal_mot_send = None
        self.event_hal_save_coords = None
        self.event_hal_park = None
        self.event_hal_zero = None
        self._keyboard_target = None
        self._keyboard_closing = False
        self._motion_busy = False
        self._save_ok_timer = None
        self._park_ok_timer = None
        self._zero_ok_timer = None
        self.hal_jog_step = self.DEFAULT_JOG_STEP
        self.setupUi(self)
        self._btn_park_style_normal = self.btn_hal_park.styleSheet()
        self._btn_zero_style_normal = self.btn_hal_zero.styleSheet()
        self.lbl_cell.setMinimumWidth(self._CELL_LABEL_MIN_WIDTH)
        self.lbl_cell.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.layout_cell_row.setSpacing(8)
        if hasattr(self, "layout_cell_number"):
            m = self.layout_cell_number.contentsMargins()
            shift = -self._CELL_NUMBER_SHIFT_LEFT_PX
            self.layout_cell_number.setContentsMargins(shift, m.top(), m.right(), m.bottom())
        mot_lbl_idx = self.layout_cell_row.indexOf(self.lbl_cell_mot_coords)
        self.layout_cell_row.setStretch(mot_lbl_idx, 1)
        self.lbl_cell_mot_coords.setText(self._LBL_CELL_MOT_DEFAULT)
        self.lbl_input_error.setText("")
        self.lbl_input_error.hide()
        self.edit_cell_number.setValidator(
            QtGui.QIntValidator(CELL_NUMBER_MIN, CELL_NUMBER_MAX, self)
        )
        self.edit_cell_number.setStyleSheet(self._EDIT_CELL_OK)
        self._setup_jog_step_selector()
        self._setup_jog_panel()
        self.btn_hal_save_coords = self.jog_panel.btn_hal_save_coords
        self._btn_save_style_normal = self.btn_hal_save_coords.styleSheet()
        self._setup_keyboard()
        self.edit_cell_number.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.edit_cell_number.installEventFilter(self)
        self._bind_error_dismiss_handlers()
        self.normalize_screen_geometry()

    @staticmethod
    def _format_cell_mot_coords_label(
        hal_x, hal_z
    ) -> str:
        """M1–M2=hal_z, M3=hal_x, M4=hal_x−25 для подписи рядом с номером ячейки."""
        z_txt = "NULL" if hal_z is None else str(int(hal_z))
        x_txt = "NULL" if hal_x is None else str(int(hal_x))
        if hal_x is None:
            m4_txt = "NULL"
        else:
            m4_txt = str(hal_mot4_from_hal_x(int(hal_x)))
        return f"({z_txt}, {x_txt}, {m4_txt})"

    def _refresh_cell_mot_coords_label(self) -> None:
        """Подставить MOT-координаты ячейки из БД по введённому номеру."""
        number, reason = validate_cell_number_text(self.edit_cell_number.text())
        if reason:
            self.lbl_cell_mot_coords.setText(self._LBL_CELL_MOT_DEFAULT)
            return
        try:
            from DB.Data.sqlite_db import SessionLocal, engine
            from DB.Engine.CellCRUD import EngineCell

            session = SessionLocal(engine())
            cell = EngineCell(session).get_cell_by_number(int(number))
        except Exception as e:
            logger.warning("cell mot coords lookup: %s", e)
            cell = None
        if not cell:
            self.lbl_cell_mot_coords.setText(self._LBL_CELL_MOT_DEFAULT)
            return
        self.lbl_cell_mot_coords.setText(
            self._format_cell_mot_coords_label(cell.hal_x, cell.hal_z)
        )

    def _bind_error_dismiss_handlers(self) -> None:
        """Сброс сообщения об ошибке при действиях на экране."""
        for name in ("btn_hal_park", "btn_hal_zero", "btn_hal_save_coords", "btn_back"):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.clicked.connect(self._clear_input_error)
        self.edit_cell_number.textChanged.connect(self._try_clear_error_on_valid_input)

    def _show_input_error(self, message: str) -> None:
        text = (message or "").strip()
        if not text:
            self._clear_input_error()
            return
        self.lbl_input_error.setText(text)
        self.lbl_input_error.show()

    def _clear_input_error(self) -> None:
        self.lbl_input_error.clear()
        self.lbl_input_error.hide()
        self.edit_cell_number.setStyleSheet(self._EDIT_CELL_OK)
        self.jog_panel.clear_field_errors()

    def _try_clear_error_on_valid_input(self) -> None:
        """Скрыть ошибку, когда исправлены поля ввода (и условия save, если были)."""
        if not self.lbl_input_error.isVisible():
            return

        number, cell_reason = validate_cell_number_text(self.edit_cell_number.text())
        _positions, bad_index, _mot_reason = self.jog_panel.parse_motor_positions()

        if cell_reason is None:
            self._set_cell_field_error(False)
        if bad_index is None:
            self.jog_panel.clear_field_errors()
        if cell_reason is not None or bad_index is not None:
            return

        err_lower = self.lbl_input_error.text().lower()
        if "не найдена" in err_lower and number is not None:
            try:
                from DB.Data.sqlite_db import SessionLocal, engine
                from DB.Engine.CellCRUD import EngineCell

                session = SessionLocal(engine())
                if not EngineCell(session).get_cell_by_number(int(number)):
                    return
            except Exception:
                return

        if any(
            x in err_lower
            for x in (
                "(0, 0)",
                "координаты ячейки",
                "подведите каретку",
                "превышено",
                "максимальное",
            )
        ):
            hal_x, hal_z, bad_idx, _reason = self.jog_panel.get_mot13_hal_xz()
            if bad_idx is not None:
                return
            ok, _reason = validate_hal_cell_coords(hal_x, hal_z)
            if not ok:
                return

        self._clear_input_error()

    def _set_cell_field_error(self, active: bool) -> None:
        self.edit_cell_number.setStyleSheet(
            self._EDIT_CELL_ERR if active else self._EDIT_CELL_OK
        )

    def _validate_cell_number_ui(self):
        number, reason = validate_cell_number_text(self.edit_cell_number.text())
        if reason:
            msg = message_for_reason(
                reason,
                min_v=CELL_NUMBER_MIN,
                max_v=CELL_NUMBER_MAX,
            )
            self._set_cell_field_error(True)
            return None, f"Ячейка №: {msg}"
        self._set_cell_field_error(False)
        return number, None

    def _validate_motors_ui(self):
        self.jog_panel.clamp_coord_inputs()
        positions, bad_index, reason = self.jog_panel.parse_motor_positions()
        if bad_index is not None:
            self.jog_panel.set_field_error(bad_index, True)
            msg = self.jog_panel.validation_error_message() or message_for_reason(
                reason,
                motor_label=f"M{bad_index + 1}",
                min_v=MOT_STEP_MIN,
                max_v=mot_axis_max(bad_index),
            )
            return None, msg
        self.jog_panel.clear_field_errors()
        return positions, None

    def _validate_save_ui(self):
        if self.jog_panel.clamp_coord_inputs():
            self._show_input_error(MOT_EXCEEDS_MAX_MESSAGE)
            return False
        self._clear_input_error()
        number, err = self._validate_cell_number_ui()
        if err:
            self._show_input_error(err)
            return False

        parent = self.window()
        executor = getattr(parent, "executor", None)
        if executor is None:
            self._show_input_error("Система не готова")
            return False

        from DB.Data.sqlite_db import SessionLocal, engine
        from DB.Engine.CellCRUD import EngineCell

        try:
            session = SessionLocal(engine())
            cell = EngineCell(session).get_cell_by_number(int(number))
        except Exception as e:
            logger.warning("validate save cell lookup: %s", e)
            cell = None

        if not cell:
            self._set_cell_field_error(True)
            self._show_input_error("Ячейка с таким номером не найдена")
            return False

        hal_x, hal_z, bad_index, mot_reason = self.jog_panel.get_mot13_hal_xz()
        if bad_index is not None:
            self.jog_panel.set_field_error(bad_index, True)
            msg = self.jog_panel.validation_error_message() or message_for_reason(
                mot_reason,
                motor_label=f"M{bad_index + 1}",
                min_v=MOT_STEP_MIN,
                max_v=mot_axis_max(bad_index),
            )
            self._show_input_error(msg)
            return False

        ok, reason = validate_hal_cell_coords(hal_x, hal_z)
        if not ok:
            self._show_input_error(message_for_reason(reason))
            return False

        executor.engineer_cell_number = int(number)
        executor.hal_save_hal_x = int(hal_x)
        executor.hal_save_hal_z = int(hal_z)
        return True

    def _validate_mot_send_ui(self):
        clamped = self.jog_panel.clamp_coord_inputs()
        if not clamped:
            self._clear_input_error()
        positions, err = self._validate_motors_ui()
        if err:
            self._show_input_error(err)
            return None
        if clamped:
            self._show_input_error(MOT_EXCEEDS_MAX_MESSAGE)
        return positions

    def _setup_jog_step_selector(self):
        self._jog_step_group = QtWidgets.QButtonGroup(self)
        self._jog_step_group.setExclusive(True)
        self._jog_step_buttons = {}
        for step in self.JOG_STEP_OPTIONS:
            btn = getattr(self, f"btn_jog_step_{step}", None)
            if btn is None:
                continue
            self._jog_step_group.addButton(btn)
            self._jog_step_buttons[step] = btn
        default_btn = self._jog_step_buttons.get(self.DEFAULT_JOG_STEP)
        if default_btn is not None:
            default_btn.setChecked(True)
        self._jog_step_group.buttonClicked.connect(self._on_jog_step_selected)
        self._sync_jog_step_to_executor()

    def _on_jog_step_selected(self, button: QtWidgets.QAbstractButton):
        self._clear_input_error()
        try:
            self.hal_jog_step = int(button.text())
        except ValueError:
            self.hal_jog_step = self.DEFAULT_JOG_STEP
        self._sync_jog_step_to_executor()

    def _sync_jog_step_to_executor(self):
        parent = self.window()
        executor = getattr(parent, "executor", None)
        if executor is not None:
            executor.hal_jog_step = int(self.hal_jog_step)

    def _setup_jog_panel(self):
        idx = self.verticalLayout.indexOf(self.widget_jog_placeholder)
        self.verticalLayout.removeWidget(self.widget_jog_placeholder)
        self.widget_jog_placeholder.deleteLater()
        self.jog_panel = WidgetHalJogPanel(self)
        self.jog_panel.event_hal_jog = lambda t: self._forward_jog(t)
        self.jog_panel.event_hal_mot_send = lambda: self._forward_mot_send()
        self.verticalLayout.insertWidget(idx, self.jog_panel)
        for edit in self.jog_panel.coord_edits():
            edit.installEventFilter(self)
            edit.textChanged.connect(self._try_clear_error_on_valid_input)

    def _setup_keyboard(self):
        self.keyboard = WidgetKeyboard()
        self.keyboard.setParent(self)
        self.keyboard.setFixedSize(450, 225)
        self.keyboard.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed,
        )
        self.keyboard.setVisible(False)
        self.keyboard.hide()
        self.keyboard.btn_close.clicked.connect(self._hide_keyboard)
        self.keyboard.btn_close.clicked.connect(self._clear_input_error)
        for digit, key in enumerate("0123456789"):
            btn = getattr(self.keyboard, f"btn_number_{digit}", None)
            if btn:
                btn.clicked.connect(lambda checked=False, k=key: self._add_digit(k))
        if hasattr(self.keyboard, "btn_backspace"):
            self.keyboard.btn_backspace.clicked.connect(self._backspace)

    def _is_coord_input(self, obj) -> bool:
        return obj in self.jog_panel.coord_edits()

    def _motor_index_for_coord_edit(self, edit) -> int:
        edits = self.jog_panel.coord_edits()
        row_indices = self.jog_panel.row_motor_indices()
        try:
            row_i = edits.index(edit)
            return row_indices[row_i]
        except ValueError:
            return 0

    def _clamp_coord_edit(self, edit) -> bool:
        """Усечь одно поле координаты по оси; True, если значение было выше лимита."""
        if edit is None or not self._is_coord_input(edit):
            return False
        mot_idx = self._motor_index_for_coord_edit(edit)
        new_text, clamped = clamp_motor_text(edit.text(), mot_idx)
        if not clamped:
            return False
        edit.blockSignals(True)
        edit.setText(new_text)
        edit.blockSignals(False)
        return True

    def _normalize_coord_edit_if_empty(self, edit) -> None:
        """При уходе с поля: пустое → «0»; при превышении лимита — усечь и предупредить."""
        if edit is None or not self._is_coord_input(edit):
            return
        if not (edit.text() or "").strip():
            edit.blockSignals(True)
            edit.setText("0")
            edit.blockSignals(False)
        if self._clamp_coord_edit(edit):
            self._show_input_error(MOT_EXCEEDS_MAX_MESSAGE)

    def eventFilter(self, obj, event):
        if obj is self.edit_cell_number or self._is_coord_input(obj):
            if self._keyboard_closing and event.type() in (
                QtCore.QEvent.FocusIn,
                QtCore.QEvent.MouseButtonPress,
            ):
                return True
            if (
                obj is self.edit_cell_number
                and event.type() == QtCore.QEvent.FocusOut
                and not self._keyboard_closing
            ):
                self._refresh_cell_mot_coords_label()
            if (
                event.type() == QtCore.QEvent.MouseButtonPress
                and event.button() == QtCore.Qt.LeftButton
                and not self._motion_busy
            ):
                self._show_keyboard(obj)
        return super().eventFilter(obj, event)

    def _begin_motion(self, motor_index=None, all_motors: bool = False) -> None:
        self._motion_busy = True
        self.jog_panel.set_motion_highlight(motor_index=motor_index, all_motors=all_motors)
        self._set_screen_blocked(True)
        QtWidgets.QApplication.processEvents()

    def _end_motion(self) -> None:
        self._refresh_positions_from_executor()
        self.jog_panel.clear_motion_highlight()
        self._set_screen_blocked(False)
        self._motion_busy = False

    def _set_screen_blocked(self, blocked: bool) -> None:
        self.jog_panel.set_blocked(blocked)
        for name in (
            "btn_hal_park",
            "btn_hal_zero",
            "btn_back",
            "edit_cell_number",
            "btn_jog_step_1",
            "btn_jog_step_5",
            "btn_jog_step_10",
            "btn_jog_step_50",
            "btn_jog_step_100",
        ):
            w = getattr(self, name, None)
            if w is not None:
                w.setEnabled(not blocked)

    def _refresh_positions_from_executor(self) -> None:
        parent = self.window()
        executor = getattr(parent, "executor", None)
        if executor is not None:
            self.jog_panel.set_motor_positions(list(executor.hal_motor_positions))

    def _jog_blocked_by_axis_limit(self, trigger_name: str) -> bool:
        """JOG у упора: усечь координаты в полях, предупредить, без UART."""
        axis, sign = parse_hal_jog_trigger(trigger_name)
        if not axis:
            return False
        parent = self.window()
        executor = getattr(parent, "executor", None)
        if executor is None:
            return False
        self._sync_jog_step_to_executor()
        try:
            step = int(getattr(executor, "hal_jog_step", self.hal_jog_step))
        except (TypeError, ValueError):
            step = self.DEFAULT_JOG_STEP
        if step <= 0:
            step = self.DEFAULT_JOG_STEP
        current = list(getattr(executor, "hal_motor_positions", None) or [0] * 5)
        new_pos, limit_hit = apply_jog_to_motor_positions(
            current,
            axis=axis,
            sign=sign,
            step=step,
        )
        if not limit_hit:
            return False
        self.jog_panel.set_motor_positions(new_pos)
        self._show_input_error(MOT_EXCEEDS_MAX_MESSAGE)
        return True

    def _forward_jog(self, trigger_name: str):
        if self._motion_busy:
            return
        if self._jog_blocked_by_axis_limit(trigger_name):
            return
        self._clear_input_error()
        self._sync_jog_step_to_executor()
        motor_idx = _motor_index_from_jog_trigger(trigger_name)
        self._begin_motion(motor_index=motor_idx)
        try:
            if callable(self.event_hal_jog):
                self.event_hal_jog(trigger_name)
        finally:
            self._end_motion()

    def _forward_mot_send(self):
        if self._motion_busy:
            return
        positions = self._validate_mot_send_ui()
        if positions is None:
            return
        parent = self.window()
        executor = getattr(parent, "executor", None)
        if executor is not None:
            executor.hal_mot_goto_positions = positions
        self._begin_motion(all_motors=True)
        try:
            if callable(self.event_hal_mot_send):
                self.event_hal_mot_send()
        finally:
            self._end_motion()
            self._clear_input_error()

    def _flash_button_success(
        self,
        button: QtWidgets.QPushButton,
        style_normal: str,
        timer_attr: str,
    ) -> None:
        timer = getattr(self, timer_attr, None)
        if timer is not None:
            timer.stop()
        button.setStyleSheet(self._BTN_SAVE_OK)
        new_timer = QtCore.QTimer(self)
        new_timer.setSingleShot(True)
        new_timer.timeout.connect(lambda b=button, s=style_normal: b.setStyleSheet(s))
        setattr(self, timer_attr, new_timer)
        new_timer.start(self._SAVE_OK_MS)

    def _flash_save_button_success(self) -> None:
        self._flash_button_success(
            self.btn_hal_save_coords,
            self._btn_save_style_normal,
            "_save_ok_timer",
        )

    def forward_save_coords(self):
        if self._motion_busy:
            return
        if not self._validate_save_ui():
            return
        if callable(self.event_hal_save_coords):
            self.event_hal_save_coords()

    def _forward_hal_park(self):
        if self._motion_busy:
            return
        self._clear_input_error()
        self._begin_motion(all_motors=True)
        try:
            if callable(self.event_hal_park):
                self.event_hal_park()
        finally:
            self._end_motion()

    def _forward_hal_zero(self):
        if self._motion_busy:
            return
        self._clear_input_error()
        self._begin_motion(all_motors=True)
        try:
            if callable(self.event_hal_zero):
                self.event_hal_zero()
        finally:
            self._end_motion()

    def _keyboard_geometry(self):
        w = self.keyboard.width()
        h = self.keyboard.height()
        bottom_margin = 8
        y = self.height() - h - bottom_margin
        x = max((self.width() - w) // 2, 0)
        return x, y, w, h

    def _show_keyboard(self, target):
        if self._keyboard_closing or self._motion_busy:
            return
        self._clear_input_error()
        if (
            self._keyboard_target is not None
            and self._keyboard_target is not target
        ):
            if self._keyboard_target is self.edit_cell_number:
                self._refresh_cell_mot_coords_label()
            self._normalize_coord_edit_if_empty(self._keyboard_target)
        if self._is_coord_input(target):
            target.blockSignals(True)
            target.setText("")
            target.blockSignals(False)
        self._keyboard_target = target
        if hasattr(target, "setFocus"):
            target.setFocus(QtCore.Qt.OtherFocusReason)
        x, y, w, h = self._keyboard_geometry()
        self.keyboard.setGeometry(x, y, w, h)
        self.keyboard.setVisible(True)
        self.keyboard.raise_()
        self.btn_back.hide()
        self.jog_panel.btn_hal_mot_send.hide()

    def _hide_keyboard(self):
        self._keyboard_closing = True
        if self._keyboard_target is self.edit_cell_number:
            self._refresh_cell_mot_coords_label()
        elif self._is_coord_input(self._keyboard_target):
            self._normalize_coord_edit_if_empty(self._keyboard_target)
        else:
            self._normalize_coord_edit_if_empty(self._keyboard_target)
        self.keyboard.setVisible(False)
        self.btn_back.show()
        if not self._motion_busy:
            self.jog_panel.btn_hal_mot_send.show()
        if self._keyboard_target is not None:
            self._keyboard_target.clearFocus()
        self.btn_back.setFocus(QtCore.Qt.OtherFocusReason)
        QtCore.QTimer.singleShot(self._KEYBOARD_CLOSE_MS, self._finish_keyboard_close)

    def _finish_keyboard_close(self):
        self._keyboard_closing = False
        self._keyboard_target = None

    def _add_digit(self, ch: str):
        if self._keyboard_target is None:
            return
        new_text = (self._keyboard_target.text() or "") + ch
        if self._keyboard_target is self.edit_cell_number:
            _, reason = validate_cell_number_text(new_text)
            if reason:
                return
        self._keyboard_target.setText(new_text)
        self._try_clear_error_on_valid_input()

    def _backspace(self):
        if self._keyboard_target is not None:
            t = self._keyboard_target.text()
            self._keyboard_target.setText(t[:-1])
            self._try_clear_error_on_valid_input()

    def set_data(self, *args, **kwargs):
        payload, _source = self.split_set_data_args(args, kwargs)
        data = {k: v for k, v in kwargs.items() if k != "source"}
        if isinstance(payload, dict):
            data.update(payload)

        positions = None
        if isinstance(payload, dict):
            positions = payload.get("hal_motor_positions")
        elif isinstance(payload, (list, tuple)):
            positions = payload

        if positions and len(positions) >= 5:
            self.jog_panel.set_motor_positions(positions)

        err_msg = data.get("hal_input_error")
        save_ok = data.get("hal_save_ok")
        park_ok = data.get("hal_park_ok")
        zero_ok = data.get("hal_zero_ok")

        if err_msg:
            self._show_input_error(str(err_msg))
        else:
            self._clear_input_error()

        if save_ok:
            self._flash_save_button_success()
            self._refresh_cell_mot_coords_label()
        if park_ok:
            self._flash_button_success(
                self.btn_hal_park,
                self._btn_park_style_normal,
                "_park_ok_timer",
            )
        if zero_ok:
            self._flash_button_success(
                self.btn_hal_zero,
                self._btn_zero_style_normal,
                "_zero_ok_timer",
            )

        prefill = data.get("engineer_cell_number")
        if prefill is not None:
            self.edit_cell_number.blockSignals(True)
            self.edit_cell_number.setText(str(int(prefill)))
            self.edit_cell_number.blockSignals(False)
        self._refresh_cell_mot_coords_label()
        self.edit_cell_number.clearFocus()

    def get_data(self):
        number, _reason = validate_cell_number_text(self.edit_cell_number.text())
        hal_x, hal_z, _bad, _mot_reason = self.jog_panel.get_mot13_hal_xz()
        data = {"engineer_cell_number": number, "number": number}
        if hal_x is not None and hal_z is not None:
            data["hal_x"] = hal_x
            data["hal_z"] = hal_z
        return data

    def hideEvent(self, event):
        self._keyboard_closing = False
        self.keyboard.setVisible(False)
        self.btn_back.show()
        self.jog_panel.btn_hal_mot_send.show()
        self.jog_panel.clear_motion_highlight()
        self._set_screen_blocked(False)
        self._motion_busy = False
        super().hideEvent(event)

    def _dismiss_keyboard_on_show(self):
        self._keyboard_closing = False
        self._keyboard_target = None
        self.keyboard.setVisible(False)
        self.keyboard.hide()
        self.btn_back.show()
        self.jog_panel.btn_hal_mot_send.show()
        self.edit_cell_number.clearFocus()
        self.setFocus(QtCore.Qt.OtherFocusReason)

    def showEvent(self, event):
        super().showEvent(event)
        self._dismiss_keyboard_on_show()
        self._sync_jog_step_to_executor()
        parent = self.window()
        executor = getattr(parent, "executor", None)
        if executor is not None:
            self.set_data(
                {
                    "hal_motor_positions": list(executor.hal_motor_positions),
                    "engineer_cell_number": executor.engineer_cell_number,
                }
            )
