from PyQt5 import QtCore, QtGui, QtWidgets

from Core.app_logging import get_logger
from EventsSystem.hal_coords import (
    CELL_NUMBER_MAX,
    CELL_NUMBER_MIN,
    MOT_EXCEEDS_MAX_MESSAGE,
    MOT_STEP_MIN,
    RGB_BYTE_MAX,
    RGB_BYTE_MIN,
    RGB_EXCEEDS_MAX_MESSAGE,
    clamp_motor_text,
    clamp_motor_value,
    clamp_rgb_text,
    clamp_sol_s_text,
    message_for_reason,
    rgb_channel_label,
    SOL_S_DEFAULT,
    SOL_S_MAX,
    SOL_S_MIN,
    validate_cell_number_text,
    validate_motor_position_texts,
    validate_rgb_texts,
    validate_sol_s_text,
)
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_40_hal_dispense import Ui_screen_40_hal_dispense
from GUI.widgets.widget_keyboard import WidgetKeyboard

logger = get_logger(__name__)


class screen_40_hal_dispense(BaseScreen, Ui_screen_40_hal_dispense):
    _PARK_ROW_MOTOR_INDICES = (0, 2, 3, 4)
    _KEYBOARD_CLOSE_MS = 350
    _SAVE_OK_MS = 3000
    _COMPACT_EDIT_MIN_WIDTH = 52
    _RGB_EDIT_MIN_WIDTH = 40
    _RGB_ROW_CONTROL_HEIGHT = 40
    _COMPACT_EDIT_MAX_LEN = 4
    _RGB_EDIT_MAX_LEN = 3
    _SOL_EDIT_MAX_LEN = 2
    _PARK_FIELD_MAX = 9999
    _RGB_FIELD_MAX = RGB_BYTE_MAX
    _ROW_CONTROL_HEIGHT = 48
    _PARK_LABEL_HEIGHT = 16
    _ACTION_BTN_MIN_WIDTH = 104
    _EDIT_CELL_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 18px; }"
    )
    _EDIT_CELL_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 18px; }"
    )
    _EDIT_PARK_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 18px; }"
    )
    _EDIT_PARK_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 18px; }"
    )
    _EDIT_RGB_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 15px; }"
    )
    _EDIT_RGB_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 15px; }"
    )
    _EDIT_SOL_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 16px; }"
    )
    _EDIT_SOL_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 16px; }"
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
    _BTN_SOL_SAVE_NORMAL = (
        "QPushButton { color: #FFFFFF; background-color: #f09022;"
        "border-radius: 6px; font-size: 11px; font-weight: 600; padding: 0px; }"
    )
    _BTN_SOL_SAVE_OK = (
        "QPushButton { color: #FFFFFF; background-color: #2d7a3e;"
        "border-radius: 6px; font-size: 11px; font-weight: 600; padding: 0px; }"
    )
    _SOL_CONTROL_WIDTH = 72

    def __init__(self):
        super().__init__()
        self.event_hal_park_save = None
        self.event_hal_rgb_save = None
        self.event_hal_sol_save = None
        self.event_hal_led_toggle = None
        self.event_hal_solenoid = None
        self.event_hal_lock = None
        self._hal_led_on = False
        self._hal_lock_active = False
        self._hal_lock_pending = False
        self._hal_sol_active = False
        self._hal_sol_pending = False
        self._keyboard_target = None
        self._keyboard_closing = False
        self._park_save_ok_timer = None
        self._rgb_save_ok_timer = None
        self._sol_save_ok_timer = None
        self._park_edits = []
        self._rgb_edits = []
        self.edit_sol_s = None
        self.setupUi(self)
        self.lbl_input_error.setText("")
        self.lbl_input_error.hide()
        self.edit_cell_number.setValidator(
            QtGui.QIntValidator(CELL_NUMBER_MIN, CELL_NUMBER_MAX, self)
        )
        self.edit_cell_number.setStyleSheet(self._EDIT_CELL_OK)
        self._setup_cell_row_layout()
        self._setup_park_rows()
        self._setup_rgb_rows()
        self._setup_sol_time_row()
        self._setup_keyboard()
        self._btn_park_save_style_normal = self.btn_hal_park_save.styleSheet()
        self._btn_rgb_save_style_normal = self.btn_hal_rgb_save.styleSheet()
        self._btn_sol_save_style_normal = self._BTN_SOL_SAVE_NORMAL
        self._btn_hal_led_style_normal = self.btn_hal_led.styleSheet()
        self._btn_hal_solenoid_style_normal = self.btn_hal_solenoid.styleSheet()
        self._btn_hal_lock_style_normal = self.btn_hal_lock.styleSheet()
        for edit in [self.edit_cell_number, *self._park_edits, *self._rgb_edits]:
            edit.setFocusPolicy(QtCore.Qt.ClickFocus)
            edit.installEventFilter(self)
        if self.edit_sol_s is not None:
            self.edit_sol_s.setFocusPolicy(QtCore.Qt.ClickFocus)
            self.edit_sol_s.installEventFilter(self)
        self.btn_back.clicked.connect(self._clear_input_error)
        self.btn_hal_dispense_run.clicked.connect(self._clear_input_error)
        self.edit_cell_number.textChanged.connect(self._try_clear_error_on_valid_input)
        for edit in self._park_edits:
            edit.textChanged.connect(self._try_clear_error_on_valid_input)
        for edit in self._rgb_edits:
            edit.textChanged.connect(self._try_clear_error_on_valid_input)
        if self.edit_sol_s is not None:
            self.edit_sol_s.textChanged.connect(self._try_clear_error_on_valid_input)
        self.normalize_screen_geometry()

    def _setup_cell_row_layout(self) -> None:
        self.layout_cell_row.setStretch(0, 0)
        self.layout_cell_row.setStretch(1, 1)
        self.layout_cell_row.setStretch(2, 0)
        self.edit_cell_number.setMaximumHeight(self._ROW_CONTROL_HEIGHT)
        self.btn_hal_dispense_run.setMaximumHeight(self._ROW_CONTROL_HEIGHT)

    def _configure_compact_edit(self, edit: QtWidgets.QLineEdit) -> None:
        edit.setMaxLength(self._COMPACT_EDIT_MAX_LEN)
        edit.setMinimumWidth(self._COMPACT_EDIT_MIN_WIDTH)
        edit.setMinimumHeight(self._ROW_CONTROL_HEIGHT)
        edit.setMaximumHeight(self._ROW_CONTROL_HEIGHT)
        edit.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        edit.setValidator(
            QtGui.QIntValidator(MOT_STEP_MIN, self._PARK_FIELD_MAX, self)
        )

    def _setup_park_rows(self):
        layout = QtWidgets.QHBoxLayout(self.widget_park_rows)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label_style = (
            "color: #FFFFFF; font-size: 13px; font-weight: 600;"
        )
        park_rows = (
            ("M1–M2", "edit_park_m12"),
            ("M3", "edit_park_m3"),
            ("M4", "edit_park_m4"),
            ("M5", "edit_park_m5"),
        )
        for label, obj_name in park_rows:
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(4)
            lbl = QtWidgets.QLabel(label, self.widget_park_rows)
            lbl.setFixedHeight(self._PARK_LABEL_HEIGHT)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet(label_style)
            edit = QtWidgets.QLineEdit(self.widget_park_rows)
            edit.setAlignment(QtCore.Qt.AlignCenter)
            edit.setStyleSheet(self._EDIT_PARK_OK)
            edit.setObjectName(obj_name)
            self._configure_compact_edit(edit)
            col.addWidget(lbl)
            col.addWidget(edit)
            layout.addLayout(col, 1)
            self._park_edits.append(edit)

        save_col = QtWidgets.QVBoxLayout()
        save_col.setSpacing(4)
        save_spacer = QtWidgets.QLabel("", self.widget_park_rows)
        save_spacer.setFixedHeight(self._PARK_LABEL_HEIGHT)
        self.btn_hal_park_save.setVisible(True)
        self.btn_hal_park_save.setMinimumWidth(self._ACTION_BTN_MIN_WIDTH)
        self.btn_hal_park_save.setMinimumHeight(self._ROW_CONTROL_HEIGHT)
        self.btn_hal_park_save.setMaximumHeight(self._ROW_CONTROL_HEIGHT)
        save_col.addWidget(save_spacer)
        save_col.addWidget(self.btn_hal_park_save)
        layout.addLayout(save_col, 1)

    def _configure_rgb_edit(self, edit: QtWidgets.QLineEdit) -> None:
        edit.setMaxLength(self._RGB_EDIT_MAX_LEN)
        edit.setMinimumWidth(self._RGB_EDIT_MIN_WIDTH)
        edit.setMaximumWidth(56)
        edit.setMinimumHeight(self._RGB_ROW_CONTROL_HEIGHT)
        edit.setMaximumHeight(self._RGB_ROW_CONTROL_HEIGHT)
        edit.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        edit.setValidator(
            QtGui.QIntValidator(RGB_BYTE_MIN, self._RGB_FIELD_MAX, self)
        )

    def _setup_rgb_rows(self) -> None:
        layout = QtWidgets.QHBoxLayout(self.widget_rgb_rows)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label_style = (
            "color: #FFFFFF; font-size: 13px; font-weight: 600;"
        )
        rgb_rows = (
            ("R", "edit_rgb_r"),
            ("G", "edit_rgb_g"),
            ("B", "edit_rgb_b"),
        )
        for label, obj_name in rgb_rows:
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(4)
            lbl = QtWidgets.QLabel(label, self.widget_rgb_rows)
            lbl.setFixedHeight(self._PARK_LABEL_HEIGHT)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet(label_style)
            edit = QtWidgets.QLineEdit(self.widget_rgb_rows)
            edit.setAlignment(QtCore.Qt.AlignCenter)
            edit.setStyleSheet(self._EDIT_RGB_OK)
            edit.setObjectName(obj_name)
            self._configure_rgb_edit(edit)
            col.addWidget(lbl)
            col.addWidget(edit)
            layout.addLayout(col, 0)
            self._rgb_edits.append(edit)

        save_col = QtWidgets.QVBoxLayout()
        save_col.setSpacing(4)
        save_spacer = QtWidgets.QLabel("", self.widget_rgb_rows)
        save_spacer.setFixedHeight(self._PARK_LABEL_HEIGHT)
        self.btn_hal_rgb_save.setVisible(True)
        self.btn_hal_rgb_save.setMinimumWidth(self._ACTION_BTN_MIN_WIDTH)
        self.btn_hal_rgb_save.setMinimumHeight(self._ROW_CONTROL_HEIGHT)
        self.btn_hal_rgb_save.setMaximumHeight(self._ROW_CONTROL_HEIGHT)
        save_col.addWidget(save_spacer)
        save_col.addWidget(self.btn_hal_rgb_save)
        layout.addLayout(save_col, 1)

        toggle_col = QtWidgets.QVBoxLayout()
        toggle_col.setSpacing(4)
        toggle_spacer = QtWidgets.QLabel("", self.widget_rgb_rows)
        toggle_spacer.setFixedHeight(self._PARK_LABEL_HEIGHT)
        self.btn_hal_led.setVisible(True)
        self.btn_hal_led.setText("LED")
        self.btn_hal_led.setIcon(QtGui.QIcon())
        self.btn_hal_led.setMinimumWidth(56)
        self.btn_hal_led.setMaximumWidth(16777215)
        self.btn_hal_led.setMinimumHeight(self._ROW_CONTROL_HEIGHT)
        self.btn_hal_led.setMaximumHeight(self._ROW_CONTROL_HEIGHT)
        toggle_col.addWidget(toggle_spacer)
        toggle_col.addWidget(self.btn_hal_led)
        layout.addLayout(toggle_col, 0)

    def _setup_sol_time_row(self) -> None:
        layout = QtWidgets.QHBoxLayout(self.widget_sol_time_row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.edit_sol_s = QtWidgets.QLineEdit(self.widget_sol_time_row)
        self.edit_sol_s.setObjectName("edit_sol_s")
        self.edit_sol_s.setAlignment(QtCore.Qt.AlignCenter)
        self.edit_sol_s.setStyleSheet(self._EDIT_SOL_OK)
        self.edit_sol_s.setMaxLength(self._SOL_EDIT_MAX_LEN)
        self.edit_sol_s.setFixedSize(
            self._SOL_CONTROL_WIDTH,
            self._RGB_ROW_CONTROL_HEIGHT,
        )
        self.edit_sol_s.setValidator(
            QtGui.QIntValidator(SOL_S_MIN, SOL_S_MAX, self)
        )
        layout.addWidget(self.edit_sol_s, 0, QtCore.Qt.AlignLeft)

        self.btn_hal_sol_save.setVisible(True)
        self.btn_hal_sol_save.setStyleSheet(self._BTN_SOL_SAVE_NORMAL)
        self.btn_hal_sol_save.setFixedSize(
            self._SOL_CONTROL_WIDTH,
            self._RGB_ROW_CONTROL_HEIGHT,
        )
        layout.addWidget(self.btn_hal_sol_save, 0, QtCore.Qt.AlignLeft)
        layout.addStretch(1)

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

    def _rgb_three_texts(self):
        if len(self._rgb_edits) < 3:
            return ["0", "0", "0"]
        return [(edit.text() or "").strip() for edit in self._rgb_edits]

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

    def _is_rgb_input(self, obj) -> bool:
        return obj in self._rgb_edits

    def _is_sol_input(self, obj) -> bool:
        return obj is self.edit_sol_s

    def _is_numeric_input(self, obj) -> bool:
        return (
            obj is self.edit_cell_number
            or self._is_park_input(obj)
            or self._is_rgb_input(obj)
            or self._is_sol_input(obj)
        )

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

    def _is_lock_busy(self) -> bool:
        return self._hal_lock_active or self._hal_lock_pending

    def _is_sol_busy(self) -> bool:
        return self._hal_sol_active or self._hal_sol_pending

    def apply_hal_actuator_state(
        self, channel: str, active: bool, pending: bool
    ) -> None:
        """Слот HalPulseBridge: обновление кнопок без полного set_data."""
        if channel == "lock":
            self._hal_lock_active = bool(active)
            self._hal_lock_pending = bool(pending)
        elif channel == "sol":
            self._hal_sol_active = bool(active)
            self._hal_sol_pending = bool(pending)
        else:
            return
        self._sync_actuator_buttons()

    def _apply_actuator_ui(self, channel: str) -> None:
        """Пессимистичный UI: зелёный только при active (после WAIT), disabled при busy."""
        if channel == "lock":
            btn = self.btn_hal_lock
            normal = self._btn_hal_lock_style_normal
            busy = self._is_lock_busy()
            active = self._hal_lock_active
        elif channel == "sol":
            btn = self.btn_hal_solenoid
            normal = self._btn_hal_solenoid_style_normal
            busy = self._is_sol_busy()
            active = self._hal_sol_active
        else:
            return
        btn.setEnabled(not busy)
        btn.setStyleSheet(self._BTN_HAL_ACTIVE if active else normal)

    def _sync_actuator_buttons(self) -> None:
        self._apply_actuator_ui("lock")
        self._apply_actuator_ui("sol")

    def forward_hal_led_toggle(self) -> None:
        if callable(self.event_hal_led_toggle):
            self.event_hal_led_toggle()

    def forward_hal_solenoid(self) -> None:
        if self._is_sol_busy():
            return
        if callable(self.event_hal_solenoid):
            self.event_hal_solenoid()

    def forward_hal_lock(self) -> None:
        if self._is_lock_busy():
            return
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

    def forward_rgb_save(self) -> None:
        """Отправить RGB; при превышении 255 — усечь поля и предупредить."""
        if self._clamp_rgb_inputs():
            self._show_input_error(RGB_EXCEEDS_MAX_MESSAGE)
            return
        self._clear_input_error()
        if callable(self.event_hal_rgb_save):
            self.event_hal_rgb_save()

    def forward_sol_save(self) -> None:
        if self._clamp_sol_input():
            self._show_input_error("Превышено максимальное значение", bad_sol=True)
            return
        self._clear_input_error()
        if callable(self.event_hal_sol_save):
            self.event_hal_sol_save()

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

    def _clamp_rgb_inputs(self) -> bool:
        any_clamped = False
        for edit in self._rgb_edits:
            new_text, clamped = clamp_rgb_text(edit.text())
            if not clamped:
                continue
            any_clamped = True
            edit.blockSignals(True)
            edit.setText(new_text)
            edit.blockSignals(False)
        return any_clamped

    def _clamp_sol_input(self) -> bool:
        if self.edit_sol_s is None:
            return False
        new_text, clamped = clamp_sol_s_text(self.edit_sol_s.text())
        if not clamped:
            return False
        self.edit_sol_s.blockSignals(True)
        self.edit_sol_s.setText(new_text)
        self.edit_sol_s.blockSignals(False)
        return True

    def _clamp_rgb_edit(self, edit) -> bool:
        if edit is None or not self._is_rgb_input(edit):
            return False
        new_text, clamped = clamp_rgb_text(edit.text())
        if not clamped:
            return False
        edit.blockSignals(True)
        edit.setText(new_text)
        edit.blockSignals(False)
        return True

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

    def _normalize_rgb_edit_if_empty(self, edit) -> None:
        if edit is None or not self._is_rgb_input(edit):
            return
        if not (edit.text() or "").strip():
            edit.blockSignals(True)
            edit.setText("0")
            edit.blockSignals(False)
        if self._clamp_rgb_edit(edit):
            self._show_input_error(RGB_EXCEEDS_MAX_MESSAGE)

    def _normalize_sol_edit_if_empty(self) -> None:
        if self.edit_sol_s is None:
            return
        if not (self.edit_sol_s.text() or "").strip():
            self.edit_sol_s.blockSignals(True)
            self.edit_sol_s.setText(str(SOL_S_DEFAULT))
            self.edit_sol_s.blockSignals(False)
        if self._clamp_sol_input():
            self._show_input_error(
                f"SOL: допустимо {SOL_S_MIN}…{SOL_S_MAX}",
                bad_sol=True,
            )

    def _normalize_numeric_edit_if_empty(self, edit) -> None:
        if self._is_park_input(edit):
            self._normalize_park_edit_if_empty(edit)
        elif self._is_rgb_input(edit):
            self._normalize_rgb_edit_if_empty(edit)
        elif self._is_sol_input(edit):
            self._normalize_sol_edit_if_empty()

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
            self._normalize_numeric_edit_if_empty(self._keyboard_target)
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
        self._normalize_numeric_edit_if_empty(self._keyboard_target)
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
        elif self._is_park_input(self._keyboard_target):
            if len(new_text) > self._COMPACT_EDIT_MAX_LEN:
                return
        elif self._is_rgb_input(self._keyboard_target):
            if len(new_text) > self._RGB_EDIT_MAX_LEN:
                return
        elif self._is_sol_input(self._keyboard_target):
            if len(new_text) > self._SOL_EDIT_MAX_LEN:
                return
            _, reason = validate_sol_s_text(new_text)
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

    def _set_rgb_field_errors(self, bad_index=None) -> None:
        for i, edit in enumerate(self._rgb_edits):
            edit.setStyleSheet(
                self._EDIT_RGB_ERR if bad_index == i else self._EDIT_RGB_OK
            )

    def _set_sol_field_error(self, active: bool) -> None:
        if self.edit_sol_s is None:
            return
        self.edit_sol_s.setStyleSheet(
            self._EDIT_SOL_ERR if active else self._EDIT_SOL_OK
        )

    def _show_input_error(
        self,
        message: str,
        *,
        bad_park_index=None,
        bad_rgb_index=None,
        bad_sol=False,
    ) -> None:
        text = (message or "").strip()
        if not text:
            self._clear_input_error()
            return
        self.lbl_input_error.setText(text)
        self.lbl_input_error.show()
        if bad_park_index is not None:
            self._set_cell_field_error(False)
            self._set_park_field_errors(bad_park_index)
            self._set_rgb_field_errors()
            self._set_sol_field_error(False)
        elif bad_rgb_index is not None:
            self._set_cell_field_error(False)
            self._set_park_field_errors()
            self._set_rgb_field_errors(bad_rgb_index)
            self._set_sol_field_error(False)
        elif bad_sol:
            self._set_cell_field_error(False)
            self._set_park_field_errors()
            self._set_rgb_field_errors()
            self._set_sol_field_error(True)
        elif "ячейк" in text.lower():
            self._set_cell_field_error(True)
            self._set_park_field_errors()
            self._set_rgb_field_errors()
            self._set_sol_field_error(False)
        else:
            self._set_cell_field_error(False)
            self._set_park_field_errors()
            self._set_rgb_field_errors()
            self._set_sol_field_error(False)

    def _clear_input_error(self) -> None:
        self.lbl_input_error.clear()
        self.lbl_input_error.hide()
        self._set_cell_field_error(False)
        self._set_park_field_errors()
        self._set_rgb_field_errors()
        self._set_sol_field_error(False)

    def _try_clear_error_on_valid_input(self) -> None:
        if not self.lbl_input_error.isVisible():
            return
        err_lower = self.lbl_input_error.text().lower()
        if "ячейк" in err_lower:
            _, reason = validate_cell_number_text(self.edit_cell_number.text())
            if reason is not None:
                return
        elif any(err_lower.startswith(f"{label}:") for label in ("r", "g", "b")):
            _, _bad_index, reason = validate_rgb_texts(self._rgb_three_texts())
            if reason is not None:
                return
        elif err_lower.startswith("sol:"):
            _, reason = validate_sol_s_text(
                self.edit_sol_s.text() if self.edit_sol_s is not None else ""
            )
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

    def _park_display_value(self, val: int, mot_idx: int) -> int:
        return min(clamp_motor_value(val, mot_idx), self._PARK_FIELD_MAX)

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
            edit.setText(str(self._park_display_value(val, mot_idx)))
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
            edit.setText(str(self._park_display_value(val, mot_idx)))
            edit.setStyleSheet(self._EDIT_PARK_OK)
            edit.blockSignals(False)

    def _rgb_values_from_profile(self) -> dict:
        """RGB из hal_motion_profile (config.json) или 0,0,0."""
        defaults = {"rgb_issue_r": 0, "rgb_issue_g": 0, "rgb_issue_b": 0}
        try:
            from pathlib import Path
            import json

            config_path = (
                Path(__file__).resolve().parent.parent / "config.json"
            )
            if config_path.is_file():
                cfg = json.loads(config_path.read_text(encoding="utf-8"))
                blob = (cfg.get("hardware") or {}).get("hal_motion_profile")
                if isinstance(blob, dict):
                    for key in defaults:
                        if blob.get(key) is not None:
                            defaults[key] = int(blob[key])
        except Exception as e:
            logger.warning("Не удалось прочитать RGB из config.json: %s", e)
        return defaults

    def _sol_value_from_db(self) -> int:
        try:
            from DB.Data.db import SessionLocal, engine
            from DB.Engine.DeviceConfigCRUD import EngineDeviceConfig
            from DB.Engine.HardwareConfigCRUD import EngineHardwareConfig

            session = SessionLocal(engine())
            try:
                device_cfg = EngineDeviceConfig(session).get_active()
                if not device_cfg:
                    return SOL_S_DEFAULT
                hw_cfg = EngineHardwareConfig(session).get_by_device(device_cfg.id)
                if not hw_cfg:
                    return SOL_S_DEFAULT
                return max(
                    SOL_S_MIN,
                    min(SOL_S_MAX, int(getattr(hw_cfg, "sol_s_default", SOL_S_DEFAULT))),
                )
            finally:
                session.close()
        except Exception as e:
            logger.warning("Не удалось прочитать sol_s из БД: %s", e)
            return SOL_S_DEFAULT

    def _load_sol_current_value(self) -> None:
        if self.edit_sol_s is None:
            return
        value = self._sol_value_from_db()
        self.edit_sol_s.blockSignals(True)
        self.edit_sol_s.setText(str(value))
        self.edit_sol_s.setStyleSheet(self._EDIT_SOL_OK)
        self.edit_sol_s.blockSignals(False)

    def _apply_sol_value(self, value: int) -> None:
        if self.edit_sol_s is None:
            return
        clamped = max(SOL_S_MIN, min(SOL_S_MAX, int(value)))
        self.edit_sol_s.blockSignals(True)
        self.edit_sol_s.setText(str(clamped))
        self.edit_sol_s.setStyleSheet(self._EDIT_SOL_OK)
        self.edit_sol_s.blockSignals(False)

    def _load_rgb_current_values(self) -> None:
        profile = self._rgb_values_from_profile()
        values = [
            int(profile.get("rgb_issue_r", 0)),
            int(profile.get("rgb_issue_g", 0)),
            int(profile.get("rgb_issue_b", 0)),
        ]
        for edit, val in zip(self._rgb_edits, values):
            edit.blockSignals(True)
            edit.setText(str(max(RGB_BYTE_MIN, min(self._RGB_FIELD_MAX, val))))
            edit.setStyleSheet(self._EDIT_RGB_OK)
            edit.blockSignals(False)

    def _apply_rgb_values(self, data: dict) -> None:
        if not data:
            return
        values = [
            int(data.get("rgb_issue_r", 0)),
            int(data.get("rgb_issue_g", 0)),
            int(data.get("rgb_issue_b", 0)),
        ]
        for edit, val in zip(self._rgb_edits, values):
            edit.blockSignals(True)
            edit.setText(str(max(RGB_BYTE_MIN, min(self._RGB_FIELD_MAX, val))))
            edit.setStyleSheet(self._EDIT_RGB_OK)
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

    def _flash_rgb_save_success(self) -> None:
        if self._rgb_save_ok_timer is not None:
            self._rgb_save_ok_timer.stop()
        self.btn_hal_rgb_save.setStyleSheet(self._BTN_SAVE_OK)
        self._rgb_save_ok_timer = QtCore.QTimer(self)
        self._rgb_save_ok_timer.setSingleShot(True)
        self._rgb_save_ok_timer.timeout.connect(
            lambda: self.btn_hal_rgb_save.setStyleSheet(
                self._btn_rgb_save_style_normal
            )
        )
        self._rgb_save_ok_timer.start(self._SAVE_OK_MS)

    def _flash_sol_save_success(self) -> None:
        if self._sol_save_ok_timer is not None:
            self._sol_save_ok_timer.stop()
        self.btn_hal_sol_save.setStyleSheet(self._BTN_SOL_SAVE_OK)
        self._sol_save_ok_timer = QtCore.QTimer(self)
        self._sol_save_ok_timer.setSingleShot(True)
        self._sol_save_ok_timer.timeout.connect(
            lambda: self.btn_hal_sol_save.setStyleSheet(
                self._btn_sol_save_style_normal
            )
        )
        self._sol_save_ok_timer.start(self._SAVE_OK_MS)

    def _dismiss_keyboard_on_show(self):
        self._keyboard_closing = False
        self._keyboard_target = None
        self.keyboard.setVisible(False)
        self.keyboard.hide()
        self.btn_back.show()
        self.edit_cell_number.clearFocus()
        self.setFocus(QtCore.Qt.OtherFocusReason)

    def _sync_hal_actuator_state_from_app(self) -> None:
        """При повторном входе на экран — подтянуть LOCK/SOL из action_cmd."""
        window = self.window()
        executor = getattr(window, "executor", None)
        if executor is None:
            return
        cmd_mapper = getattr(getattr(executor, "selector", None), "mappers", {}).get("cmd")
        if cmd_mapper is None:
            return
        self._hal_lock_active = bool(getattr(cmd_mapper, "_hal_lock_active", False))
        self._hal_lock_pending = bool(getattr(cmd_mapper, "_hal_lock_pending", False))
        self._hal_sol_active = bool(getattr(cmd_mapper, "_hal_sol_active", False))
        self._hal_sol_pending = bool(getattr(cmd_mapper, "_hal_sol_pending", False))
        self._sync_actuator_buttons()

    def showEvent(self, event):
        super().showEvent(event)
        self._dismiss_keyboard_on_show()
        self._load_park_current_values()
        self._load_rgb_current_values()
        self._load_sol_current_value()
        self._sync_hal_actuator_state_from_app()

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
            bad_rgb = None
            err_lower = str(err_msg).lower()
            _mot_to_park_row = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3}
            for i in range(1, 6):
                if f"m{i}" in err_lower:
                    bad_park = _mot_to_park_row.get(i - 1)
                    break
            for i, label in enumerate(("r", "g", "b")):
                if err_lower.startswith(f"{label}:") or f" {label}:" in err_lower:
                    bad_rgb = i
                    break
            bad_sol = err_lower.startswith("sol:")
            self._show_input_error(
                str(err_msg),
                bad_park_index=bad_park,
                bad_rgb_index=bad_rgb,
                bad_sol=bad_sol,
            )
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

        if kwargs.get("hal_rgb_save_ok"):
            self._flash_rgb_save_success()

        if kwargs.get("hal_sol_save_ok"):
            self._flash_sol_save_success()

        if "sol_s" in kwargs:
            self._apply_sol_value(int(kwargs["sol_s"]))
        elif args:
            for a in args:
                if isinstance(a, dict) and "sol_s" in a:
                    self._apply_sol_value(int(a["sol_s"]))
                    break

        rgb_data = {}
        for key in ("rgb_issue_r", "rgb_issue_g", "rgb_issue_b"):
            if key in kwargs:
                rgb_data[key] = kwargs[key]
        if not rgb_data and args:
            for a in args:
                if isinstance(a, dict):
                    for key in ("rgb_issue_r", "rgb_issue_g", "rgb_issue_b"):
                        if key in a:
                            rgb_data[key] = a[key]
        if rgb_data:
            self._apply_rgb_values(rgb_data)

        if "hal_led_on" in kwargs:
            self._set_hal_led_style(bool(kwargs["hal_led_on"]))
        else:
            for a in args:
                if isinstance(a, dict) and "hal_led_on" in a:
                    self._set_hal_led_style(bool(a["hal_led_on"]))
                    break

        for key, attr in (
            ("hal_lock_active", "_hal_lock_active"),
            ("hal_lock_pending", "_hal_lock_pending"),
            ("hal_sol_active", "_hal_sol_active"),
            ("hal_sol_pending", "_hal_sol_pending"),
        ):
            if key in kwargs:
                setattr(self, attr, bool(kwargs[key]))
            else:
                for a in args:
                    if isinstance(a, dict) and key in a:
                        setattr(self, attr, bool(a[key]))
                        break
        self._sync_actuator_buttons()

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
        rgb, _rgb_bad, _rgb_reason = validate_rgb_texts(self._rgb_three_texts())
        data = {"engineer_cell_number": number, "number": number}
        if positions is not None:
            for i, val in enumerate(positions, start=1):
                data[f"park_m{i}"] = val
        if rgb is not None:
            data["rgb_issue_r"], data["rgb_issue_g"], data["rgb_issue_b"] = rgb
        if self.edit_sol_s is not None:
            sol_s, _reason = validate_sol_s_text(self.edit_sol_s.text())
            if sol_s is not None:
                data["sol_s"] = sol_s
        return data
