from PyQt5 import QtCore, QtGui, QtWidgets

from Core.app_logging import get_logger
from EventsSystem.hal_coords import (
    CELL_NUMBER_MAX,
    CELL_NUMBER_MIN,
    MOT_EXCEEDS_MAX_MESSAGE,
    MOT_STEP_MAX,
    MOT_STEP_MIN,
    clamp_motor_text,
    clamp_motor_value,
    message_for_reason,
    validate_cell_number_text,
    validate_motor_position_texts,
)
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_40_hal_dispense import Ui_screen_40_hal_dispense
from GUI.widgets.widget_keyboard import WidgetKeyboard

logger = get_logger(__name__)


class screen_40_hal_dispense(BaseScreen, Ui_screen_40_hal_dispense):
    _PARK_ROW_MOTOR_INDICES = (0, 2, 3, 4)
    _KEYBOARD_CLOSE_MS = 350
    _SAVE_OK_MS = 3000
    _EDIT_CELL_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 17px; }"
    )
    _EDIT_CELL_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 17px; }"
    )
    _EDIT_PARK_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 17px; }"
    )
    _EDIT_PARK_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 17px; }"
    )
    _BTN_SAVE_OK = (
        "QPushButton { color: #FFFFFF; background-color: #2d7a3e;"
        "border-radius: 8px; font-size: 19px; font-weight: 600; min-height: 43px; }"
    )
    _BTN_HAL_ACTIVE = (
        "QPushButton { color: #FFFFFF; background-color: #2d7a3e;"
        "border-radius: 8px; font-size: 19px; font-weight: 600; min-height: 43px; }"
        "QPushButton:disabled { color: #FFFFFF; background-color: #2d7a3e; }"
    )
    _HAL_PULSE_MS = 10_000

    def __init__(self):
        super().__init__()
        self.event_hal_park_save = None
        self.event_hal_led_toggle = None
        self.event_hal_solenoid = None
        self.event_hal_lock = None
        self._hal_led_on = False
        self._pulse_timers = {}
        self._keyboard_target = None
        self._keyboard_closing = False
        self._park_save_ok_timer = None
        self._park_edits = []
        self.setupUi(self)
        stretch_idx = self.layout_cell_row.indexOf(self.edit_cell_number)
        self.layout_cell_row.setStretch(stretch_idx, 1)
        self.lbl_input_error.setText("")
        self.lbl_input_error.hide()
        self.edit_cell_number.setValidator(
            QtGui.QIntValidator(CELL_NUMBER_MIN, CELL_NUMBER_MAX, self)
        )
        self.edit_cell_number.setStyleSheet(self._EDIT_CELL_OK)
        self._setup_park_rows()
        self._setup_keyboard()
        self._btn_park_save_style_normal = self.btn_hal_park_save.styleSheet()
        self._btn_hal_led_style_normal = self.btn_hal_led.styleSheet()
        self._btn_hal_solenoid_style_normal = self.btn_hal_solenoid.styleSheet()
        self._btn_hal_lock_style_normal = self.btn_hal_lock.styleSheet()
        for edit in [self.edit_cell_number, *self._park_edits]:
            edit.setFocusPolicy(QtCore.Qt.ClickFocus)
            edit.installEventFilter(self)
        self.btn_back.clicked.connect(self._clear_input_error)
        self.btn_hal_dispense_run.clicked.connect(self._clear_input_error)
        self.edit_cell_number.textChanged.connect(self._try_clear_error_on_valid_input)
        for edit in self._park_edits:
            edit.textChanged.connect(self._try_clear_error_on_valid_input)
        self.normalize_screen_geometry()

    def _setup_park_rows(self):
        layout = QtWidgets.QVBoxLayout(self.widget_park_rows)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label_style = "color: #FFFFFF; font-size: 13px; font-weight: 600;"
        park_rows = (
            ("M1–M2", "edit_park_m12"),
            ("M3", "edit_park_m3"),
            ("M4", "edit_park_m4"),
            ("M5", "edit_park_m5"),
        )
        for row_i, (label, obj_name) in enumerate(park_rows):
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(8)
            lbl = QtWidgets.QLabel(label, self.widget_park_rows)
            lbl.setMinimumWidth(48)
            lbl.setStyleSheet(label_style)
            edit = QtWidgets.QLineEdit(self.widget_park_rows)
            edit.setAlignment(QtCore.Qt.AlignCenter)
            edit.setMinimumHeight(35)
            edit.setStyleSheet(self._EDIT_PARK_OK)
            edit.setValidator(
                QtGui.QIntValidator(MOT_STEP_MIN, MOT_STEP_MAX, self)
            )
            edit.setObjectName(obj_name)
            row.addWidget(lbl)
            row.addWidget(edit, 1)
            layout.addLayout(row)
            self._park_edits.append(edit)

    def _park_five_texts(self):
        """Пять значений парковки: M1–M2 → park_m1 и park_m2."""
        if len(self._park_edits) < 4:
            return ["0"] * 5
        z_text = (self._park_edits[0].text() or "").strip()
        return [
            z_text,
            z_text,
            (self._park_edits[1].text() or "").strip(),
            (self._park_edits[2].text() or "").strip(),
            (self._park_edits[3].text() or "").strip(),
        ]

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

    def _is_park_input(self, obj) -> bool:
        return obj in self._park_edits

    def _is_numeric_input(self, obj) -> bool:
        return obj is self.edit_cell_number or self._is_park_input(obj)

    def _motor_index_for_park_edit(self, edit) -> int:
        try:
            row_i = self._park_edits.index(edit)
            return self._PARK_ROW_MOTOR_INDICES[row_i]
        except ValueError:
            return 0

    def _set_hal_led_style(self, active: bool) -> None:
        self._hal_led_on = bool(active)
        self.btn_hal_led.setStyleSheet(
            self._BTN_HAL_ACTIVE if active else self._btn_hal_led_style_normal
        )

    def _begin_pulse(self, button: QtWidgets.QPushButton) -> None:
        name = button.objectName()
        timer = self._pulse_timers.get(name)
        if timer is not None:
            timer.stop()
        button.setEnabled(False)
        button.setStyleSheet(self._BTN_HAL_ACTIVE)
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(
            lambda b=button: self._end_pulse(b)
        )
        timer.start(self._HAL_PULSE_MS)
        self._pulse_timers[name] = timer

    def _end_pulse(self, button: QtWidgets.QPushButton) -> None:
        name = button.objectName()
        timer = self._pulse_timers.pop(name, None)
        if timer is not None:
            timer.stop()
        if name == "btn_hal_solenoid":
            normal = self._btn_hal_solenoid_style_normal
        elif name == "btn_hal_lock":
            normal = self._btn_hal_lock_style_normal
        else:
            normal = button.styleSheet()
        button.setStyleSheet(normal)
        button.setEnabled(True)

    def forward_hal_led_toggle(self) -> None:
        if callable(self.event_hal_led_toggle):
            self.event_hal_led_toggle()

    def forward_hal_solenoid(self) -> None:
        if self._pulse_timers.get("btn_hal_solenoid") is not None:
            return
        self._begin_pulse(self.btn_hal_solenoid)
        if callable(self.event_hal_solenoid):
            self.event_hal_solenoid()

    def forward_hal_lock(self) -> None:
        if self._pulse_timers.get("btn_hal_lock") is not None:
            return
        self._begin_pulse(self.btn_hal_lock)
        if callable(self.event_hal_lock):
            self.event_hal_lock()

    def forward_park_save(self) -> None:
        """Сохранить парковку; при превышении лимита — усечь поля, предупредить, без БД."""
        if self._clamp_park_inputs():
            self._show_input_error(MOT_EXCEEDS_MAX_MESSAGE)
            return
        self._clear_input_error()
        if callable(self.event_hal_park_save):
            self.event_hal_park_save()

    def _clamp_park_inputs(self) -> bool:
        """Ограничить поля парковки по осям MOT."""
        any_clamped = False
        for edit, mot_idx in zip(self._park_edits, self._PARK_ROW_MOTOR_INDICES):
            new_text, clamped = clamp_motor_text(edit.text(), mot_idx)
            if not clamped:
                continue
            any_clamped = True
            edit.blockSignals(True)
            edit.setText(new_text)
            edit.blockSignals(False)
        return any_clamped

    def _clamp_park_edit(self, edit) -> bool:
        """Усечь одно поле парковки; True, если значение превышало лимит оси."""
        if edit is None or not self._is_park_input(edit):
            return False
        mot_idx = self._motor_index_for_park_edit(edit)
        new_text, clamped = clamp_motor_text(edit.text(), mot_idx)
        if not clamped:
            return False
        edit.blockSignals(True)
        edit.setText(new_text)
        edit.blockSignals(False)
        return True

    def _normalize_park_edit_if_empty(self, edit) -> None:
        """При уходе с поля: пустое → «0»; при превышении — усечь и предупредить."""
        if edit is None or not self._is_park_input(edit):
            return
        if not (edit.text() or "").strip():
            edit.blockSignals(True)
            edit.setText("0")
            edit.blockSignals(False)
        if self._clamp_park_edit(edit):
            self._show_input_error(MOT_EXCEEDS_MAX_MESSAGE)

    def _clear_field_for_entry(self, target) -> None:
        """При фокусе на поле — очистить для нового ввода."""
        if target is None:
            return
        target.blockSignals(True)
        target.setText("")
        target.blockSignals(False)

    def eventFilter(self, obj, event):
        if self._is_numeric_input(obj):
            if self._keyboard_closing and event.type() in (
                QtCore.QEvent.FocusIn,
                QtCore.QEvent.MouseButtonPress,
            ):
                return True
            if (
                event.type() == QtCore.QEvent.MouseButtonPress
                and event.button() == QtCore.Qt.LeftButton
            ):
                self._show_keyboard(obj)
        return super().eventFilter(obj, event)

    def _keyboard_geometry(self):
        w = self.keyboard.width()
        h = self.keyboard.height()
        bottom_margin = 8
        y = self.height() - h - bottom_margin
        x = max((self.width() - w) // 2, 0)
        return x, y, w, h

    def _show_keyboard(self, target):
        if self._keyboard_closing:
            return
        self._clear_input_error()
        if (
            self._keyboard_target is not None
            and self._keyboard_target is not target
        ):
            self._normalize_park_edit_if_empty(self._keyboard_target)
        self._clear_field_for_entry(target)
        self._keyboard_target = target
        if hasattr(target, "setFocus"):
            target.setFocus(QtCore.Qt.OtherFocusReason)
        x, y, w, h = self._keyboard_geometry()
        self.keyboard.setGeometry(x, y, w, h)
        self.keyboard.setVisible(True)
        self.keyboard.raise_()
        self.btn_back.hide()

    def _hide_keyboard(self):
        self._keyboard_closing = True
        if self._is_park_input(self._keyboard_target):
            self._normalize_park_edit_if_empty(self._keyboard_target)
        else:
            self._normalize_park_edit_if_empty(self._keyboard_target)
        self.keyboard.setVisible(False)
        self.btn_back.show()
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

    def _set_cell_field_error(self, active: bool) -> None:
        self.edit_cell_number.setStyleSheet(
            self._EDIT_CELL_ERR if active else self._EDIT_CELL_OK
        )

    def _set_park_field_errors(self, bad_index=None) -> None:
        for i, edit in enumerate(self._park_edits):
            edit.setStyleSheet(
                self._EDIT_PARK_ERR if bad_index == i else self._EDIT_PARK_OK
            )

    def _show_input_error(self, message: str, *, bad_park_index=None) -> None:
        text = (message or "").strip()
        if not text:
            self._clear_input_error()
            return
        self.lbl_input_error.setText(text)
        self.lbl_input_error.show()
        if bad_park_index is not None:
            self._set_cell_field_error(False)
            self._set_park_field_errors(bad_park_index)
        elif "ячейк" in text.lower():
            self._set_cell_field_error(True)
            self._set_park_field_errors()
        else:
            self._set_cell_field_error(False)
            self._set_park_field_errors()

    def _clear_input_error(self) -> None:
        self.lbl_input_error.clear()
        self.lbl_input_error.hide()
        self._set_cell_field_error(False)
        self._set_park_field_errors()

    def _try_clear_error_on_valid_input(self) -> None:
        if not self.lbl_input_error.isVisible():
            return
        err_lower = self.lbl_input_error.text().lower()
        if "ячейк" in err_lower:
            _, reason = validate_cell_number_text(self.edit_cell_number.text())
            if reason is not None:
                return
        elif any(
            x in err_lower
            for x in (
                "m1",
                "m2",
                "m3",
                "m4",
                "m5",
                "m1–m2",
                "допустимо",
                "поле",
                "превышено",
                "максимальное",
            )
        ):
            _, bad_index, reason = validate_motor_position_texts(
                self._park_five_texts()
            )
            if reason is not None:
                return
        self._clear_input_error()

    def _park_values_from_db(self) -> dict:
        """Парковка M1..M5 только из HardwareConfig (без config.json)."""
        try:
            from DB.Data.db import SessionLocal, engine
            from DB.Engine.DeviceConfigCRUD import EngineDeviceConfig
            from DB.Engine.HardwareConfigCRUD import EngineHardwareConfig
            from DB.hardware_config_migrate import migrate_hardware_config_park_motors

            eng = engine()
            migrate_hardware_config_park_motors(eng)
            session = SessionLocal(eng)
            try:
                device_cfg = EngineDeviceConfig(session).get_active()
                if not device_cfg:
                    return {}
                hw_cfg = EngineHardwareConfig(session).get_by_device(device_cfg.id)
                if not hw_cfg:
                    return {}
                return {
                    f"park_m{i}": int(getattr(hw_cfg, f"park_m{i}_default", 0))
                    for i in range(1, 6)
                }
            finally:
                session.close()
        except Exception as e:
            logger.warning("Не удалось прочитать park_m из БД: %s", e)
            return {}

    def _load_park_current_values(self) -> None:
        profile = self._park_values_from_db()
        row_values = [
            int(profile.get("park_m1", profile.get("park_m2", 0))),
            int(profile.get("park_m3", 0)),
            int(profile.get("park_m4", 0)),
            int(profile.get("park_m5", 0)),
        ]
        for edit, val, mot_idx in zip(
            self._park_edits, row_values, self._PARK_ROW_MOTOR_INDICES
        ):
            edit.blockSignals(True)
            edit.setText(str(clamp_motor_value(val, mot_idx)))
            edit.setStyleSheet(self._EDIT_PARK_OK)
            edit.blockSignals(False)

    def _apply_park_values(self, data: dict) -> None:
        if not data:
            return
        row_values = [
            int(data.get("park_m1", data.get("park_m2", 0))),
            int(data.get("park_m3", 0)),
            int(data.get("park_m4", 0)),
            int(data.get("park_m5", 0)),
        ]
        for edit, val, mot_idx in zip(
            self._park_edits, row_values, self._PARK_ROW_MOTOR_INDICES
        ):
            edit.blockSignals(True)
            edit.setText(str(clamp_motor_value(val, mot_idx)))
            edit.setStyleSheet(self._EDIT_PARK_OK)
            edit.blockSignals(False)

    def _flash_park_save_success(self) -> None:
        if self._park_save_ok_timer is not None:
            self._park_save_ok_timer.stop()
        self.btn_hal_park_save.setStyleSheet(self._BTN_SAVE_OK)
        self._park_save_ok_timer = QtCore.QTimer(self)
        self._park_save_ok_timer.setSingleShot(True)
        self._park_save_ok_timer.timeout.connect(
            lambda: self.btn_hal_park_save.setStyleSheet(
                self._btn_park_save_style_normal
            )
        )
        self._park_save_ok_timer.start(self._SAVE_OK_MS)

    def _dismiss_keyboard_on_show(self):
        self._keyboard_closing = False
        self._keyboard_target = None
        self.keyboard.setVisible(False)
        self.keyboard.hide()
        self.btn_back.show()
        self.edit_cell_number.clearFocus()
        self.setFocus(QtCore.Qt.OtherFocusReason)

    def showEvent(self, event):
        super().showEvent(event)
        self._dismiss_keyboard_on_show()
        self._load_park_current_values()

    def hideEvent(self, event):
        self._keyboard_closing = False
        self.keyboard.setVisible(False)
        self.btn_back.show()
        super().hideEvent(event)

    def set_data(self, *args, **kwargs):
        err_msg = kwargs.get("hal_input_error")
        if err_msg is None and args:
            for a in args:
                if isinstance(a, dict) and "hal_input_error" in a:
                    err_msg = a["hal_input_error"]
                    break
        if err_msg:
            bad_park = None
            err_lower = str(err_msg).lower()
            _mot_to_park_row = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3}
            for i in range(1, 6):
                if f"m{i}" in err_lower:
                    bad_park = _mot_to_park_row.get(i - 1)
                    break
            self._show_input_error(str(err_msg), bad_park_index=bad_park)
        else:
            self._clear_input_error()

        park_data = {}
        for i in range(1, 6):
            key = f"park_m{i}"
            if key in kwargs:
                park_data[key] = kwargs[key]
        if not park_data and args:
            for a in args:
                if isinstance(a, dict):
                    for i in range(1, 6):
                        key = f"park_m{i}"
                        if key in a:
                            park_data[key] = a[key]
        if park_data:
            self._apply_park_values(park_data)
        else:
            self._load_park_current_values()

        if kwargs.get("hal_park_save_ok"):
            self._flash_park_save_success()

        if "hal_led_on" in kwargs:
            self._set_hal_led_style(bool(kwargs["hal_led_on"]))
        else:
            for a in args:
                if isinstance(a, dict) and "hal_led_on" in a:
                    self._set_hal_led_style(bool(a["hal_led_on"]))
                    break

        cancel = kwargs.get("hal_pulse_cancel")
        if cancel is None:
            for a in args:
                if isinstance(a, dict) and "hal_pulse_cancel" in a:
                    cancel = a["hal_pulse_cancel"]
                    break
        if cancel == "solenoid":
            self._end_pulse(self.btn_hal_solenoid)
        elif cancel == "lock":
            self._end_pulse(self.btn_hal_lock)

        prefill = kwargs.get("engineer_cell_number")
        if prefill is None and args:
            for a in args:
                if isinstance(a, dict) and "engineer_cell_number" in a:
                    prefill = a["engineer_cell_number"]
                    break
        if prefill is not None:
            self.edit_cell_number.blockSignals(True)
            self.edit_cell_number.setText(str(int(prefill)))
            self.edit_cell_number.blockSignals(False)
        self.edit_cell_number.clearFocus()

    def get_data(self):
        number, _reason = validate_cell_number_text(self.edit_cell_number.text())
        positions, _bad_index, _reason = validate_motor_position_texts(
            self._park_five_texts()
        )
        data = {"engineer_cell_number": number, "number": number}
        if positions is not None:
            for i, val in enumerate(positions, start=1):
                data[f"park_m{i}"] = val
        return data
