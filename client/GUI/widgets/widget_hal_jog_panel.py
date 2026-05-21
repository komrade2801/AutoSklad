from typing import List, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from EventsSystem.hal_coords import (
    HAL_MOT_X_DERIVED_INDEX,
    HAL_MOT_X_INDEX,
    HAL_MOT_Z_INDICES,
    HAL_SAVE_MOT_X_INDEX,
    HAL_SAVE_MOT_Z_INDEX,
    MOT_STEP_MAX,
    MOT_STEP_MIN,
    message_for_reason,
    parse_uint,
    validate_motor_position_texts,
)

# Строки панели: (подпись, −, +, индексы MOT 0..4 для подсветки)
_JOG_ROWS = (
    ("M1–M2", "hal_jog_z_minus", "hal_jog_z_plus", HAL_MOT_Z_INDICES),
    ("M3", "hal_jog_m3_minus", "hal_jog_m3_plus", (HAL_MOT_X_INDEX,)),
    ("M4", "hal_jog_m4_minus", "hal_jog_m4_plus", (HAL_MOT_X_DERIVED_INDEX,)),
    ("M5", "hal_jog_m5_minus", "hal_jog_m5_plus", (4,)),
)

_COL_AXIS = 0
_COL_VALUE = 1
_COL_MINUS = 2
_COL_PLUS = 3
_LABEL_WIDTH = 96
_JOG_BTN_WIDTH = 52
_JOG_ROW_HEIGHT = 40


class WidgetHalJogPanel(QtWidgets.QWidget):
    """Панель JOG: M1–M2 (общее hal_z), M3, M4, M5; ±; «Отправка»."""

    _BTN_STYLE = (
        "QPushButton { color: #FFFFFF; background-color: #f09022;"
        "border-radius: 8px; font-size: 22px; font-weight: 600; min-height: 40px; }"
        "QPushButton:disabled { background-color: #6a7a8f; color: #cccccc; }"
    )
    _LBL_MOTOR_IDLE = "color: #FFFFFF; font-size: 18px; font-weight: 600;"
    _LBL_MOTOR_ACTIVE = (
        "color: #FFFFFF; font-size: 18px; font-weight: 600;"
        "background-color: #2d7a3e; border-radius: 6px;"
    )
    _EDIT_OK = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 1px solid #4a6a8a; border-radius: 6px; font-size: 18px;"
        "padding: 4px; }"
        "QLineEdit:disabled { color: #aaaaaa; background-color: #253a52; }"
    )
    _EDIT_ERR = (
        "QLineEdit { color: #FFFFFF; background-color: #1e3350;"
        "border: 2px solid #e04040; border-radius: 6px; font-size: 18px;"
        "padding: 4px; }"
    )
    _SEND_BTN_STYLE = (
        "QPushButton { color: #FFFFFF; background-color: #f09022;"
        "border-radius: 8px; font-size: 20px; font-weight: 600; min-height: 48px; }"
        "QPushButton:disabled { background-color: #6a7a8f; color: #cccccc; }"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget_hal_jog_panel")
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._motor_labels: List[QtWidgets.QLabel] = []
        self._coord_edits: List[QtWidgets.QLineEdit] = []
        self._row_mot_indices: List[tuple] = []
        self.event_hal_jog = None
        self.event_hal_mot_send = None

        mot_validator = QtGui.QIntValidator(MOT_STEP_MIN, MOT_STEP_MAX, self)

        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnMinimumWidth(_COL_AXIS, _LABEL_WIDTH)
        grid.setColumnMinimumWidth(_COL_MINUS, _JOG_BTN_WIDTH)
        grid.setColumnMinimumWidth(_COL_PLUS, _JOG_BTN_WIDTH)
        grid.setColumnStretch(_COL_VALUE, 1)

        header_style = "color: #CCCCCC; font-size: 15px; font-weight: 600;"
        for col, text in enumerate(("", "Коорд.", "−", "+")):
            hdr = QtWidgets.QLabel(text, self)
            hdr.setStyleSheet(header_style)
            hdr.setAlignment(QtCore.Qt.AlignCenter)
            if col == _COL_AXIS:
                hdr.setFixedWidth(_LABEL_WIDTH)
                hdr.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            elif col in (_COL_MINUS, _COL_PLUS):
                hdr.setFixedWidth(_JOG_BTN_WIDTH)
            grid.addWidget(hdr, 0, col)

        for row_idx, (label, minus_name, plus_name, mot_indices) in enumerate(_JOG_ROWS):
            grid_row = row_idx + 1
            lbl_motor = QtWidgets.QLabel(label, self)
            lbl_motor.setFixedSize(_LABEL_WIDTH, _JOG_ROW_HEIGHT)
            lbl_motor.setAlignment(QtCore.Qt.AlignCenter)
            lbl_motor.setStyleSheet(self._LBL_MOTOR_IDLE)
            lbl_motor.setObjectName(f"lbl_jog_row_{row_idx}")

            edit_coord = QtWidgets.QLineEdit("0", self)
            edit_coord.setAlignment(QtCore.Qt.AlignCenter)
            edit_coord.setMinimumHeight(_JOG_ROW_HEIGHT)
            edit_coord.setStyleSheet(self._EDIT_OK)
            edit_coord.setValidator(mot_validator)
            edit_coord.setObjectName(f"edit_jog_row_{row_idx}")
            edit_coord.setFocusPolicy(QtCore.Qt.ClickFocus)
            edit_coord.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed,
            )

            btn_minus = QtWidgets.QPushButton("−", self)
            btn_minus.setObjectName(minus_name)
            btn_minus.setFixedWidth(_JOG_BTN_WIDTH)
            btn_minus.setStyleSheet(self._BTN_STYLE)
            btn_plus = QtWidgets.QPushButton("+", self)
            btn_plus.setObjectName(plus_name)
            btn_plus.setFixedWidth(_JOG_BTN_WIDTH)
            btn_plus.setStyleSheet(self._BTN_STYLE)

            grid.addWidget(lbl_motor, grid_row, _COL_AXIS)
            grid.addWidget(edit_coord, grid_row, _COL_VALUE)
            grid.addWidget(btn_minus, grid_row, _COL_MINUS)
            grid.addWidget(btn_plus, grid_row, _COL_PLUS)

            self._motor_labels.append(lbl_motor)
            self._coord_edits.append(edit_coord)
            self._row_mot_indices.append(tuple(mot_indices))

            btn_minus.clicked.connect(
                lambda checked=False, n=minus_name: self._on_jog(n)
            )
            btn_plus.clicked.connect(
                lambda checked=False, n=plus_name: self._on_jog(n)
            )

        root.addLayout(grid)

        self.btn_hal_mot_send = QtWidgets.QPushButton("Отправка", self)
        self.btn_hal_mot_send.setObjectName("btn_hal_mot_send")
        self.btn_hal_mot_send.setStyleSheet(self._SEND_BTN_STYLE)
        self.btn_hal_mot_send.clicked.connect(self._on_send_clicked)
        root.addWidget(self.btn_hal_mot_send)

        self.btn_hal_save_coords = QtWidgets.QPushButton("Сохранить координаты", self)
        self.btn_hal_save_coords.setObjectName("btn_hal_save_coords")
        self.btn_hal_save_coords.setStyleSheet(self._SEND_BTN_STYLE)
        root.addWidget(self.btn_hal_save_coords)

    def _on_jog(self, trigger_name: str):
        if callable(self.event_hal_jog):
            self.event_hal_jog(trigger_name)

    def _on_send_clicked(self):
        if callable(self.event_hal_mot_send):
            self.event_hal_mot_send()

    def _five_motor_texts(self) -> List[str]:
        """Тексты M1..M5: значение M1–M2 дублируется на MOT1 и MOT2."""
        if len(self._coord_edits) < 4:
            return ["0"] * 5
        z_text = (self._coord_edits[0].text() or "").strip()
        m3 = (self._coord_edits[1].text() or "").strip()
        m4 = (self._coord_edits[2].text() or "").strip()
        m5 = (self._coord_edits[3].text() or "").strip()
        return [z_text, z_text, m3, m4, m5]

    def set_motor_positions(self, positions) -> None:
        if not positions:
            return
        p = list(positions[:5])
        while len(p) < 5:
            p.append(0)
        row_values = [int(p[HAL_MOT_Z_INDICES[0]]), int(p[2]), int(p[3]), int(p[4])]
        for edit, val in zip(self._coord_edits, row_values):
            edit.blockSignals(True)
            edit.setText(str(val))
            edit.setStyleSheet(self._EDIT_OK)
            edit.blockSignals(False)

    def motor_coord_texts(self) -> list:
        return self._five_motor_texts()

    def parse_motor_positions(self):
        return validate_motor_position_texts(self._five_motor_texts())

    def get_motor_positions(self) -> list:
        positions, _bad, _reason = self.parse_motor_positions()
        if positions is None:
            return []
        return positions

    def get_mot13_hal_xz(self):
        """
        hal_z ← M1–M2 (MOT1/MOT2), hal_x ← M3.
        Возвращает (hal_x, hal_z, bad_index, reason); bad_index 0..4 по MOT.
        """
        texts = self._five_motor_texts()
        out = []
        checks = (
            (HAL_SAVE_MOT_Z_INDEX, "M1–M2"),
            (HAL_SAVE_MOT_X_INDEX, "M3"),
        )
        for idx, label in checks:
            raw = texts[idx] if idx < len(texts) else ""
            value, reason = parse_uint(
                raw,
                min_value=MOT_STEP_MIN,
                max_value=MOT_STEP_MAX,
            )
            if reason:
                return None, None, idx, reason
            out.append(value)
        return out[1], out[0], None, None

    def _row_index_for_motor(self, motor_index: int) -> Optional[int]:
        for row_i, indices in enumerate(self._row_mot_indices):
            if motor_index in indices:
                return row_i
        return None

    def set_field_error(self, index: Optional[int], active: bool) -> None:
        row_i = self._row_index_for_motor(index) if index is not None else None
        for i, edit in enumerate(self._coord_edits):
            edit.setStyleSheet(
                self._EDIT_ERR if active and i == row_i else self._EDIT_OK
            )

    def clear_field_errors(self) -> None:
        for edit in self._coord_edits:
            edit.setStyleSheet(self._EDIT_OK)

    def validation_error_message(self) -> Optional[str]:
        _positions, bad_index, reason = self.parse_motor_positions()
        if bad_index is None:
            return None
        row_i = self._row_index_for_motor(bad_index)
        if row_i == 0:
            label = "M1–M2"
        elif row_i is not None:
            label = _JOG_ROWS[row_i][0]
        else:
            label = f"M{bad_index + 1}"
        return message_for_reason(
            reason,
            motor_label=label,
            min_v=MOT_STEP_MIN,
            max_v=MOT_STEP_MAX,
        )

    def set_motion_highlight(self, motor_index=None, all_motors: bool = False) -> None:
        for i, lbl in enumerate(self._motor_labels):
            if all_motors:
                lbl.setStyleSheet(self._LBL_MOTOR_ACTIVE)
                continue
            indices = self._row_mot_indices[i]
            if motor_index is not None and motor_index in indices:
                lbl.setStyleSheet(self._LBL_MOTOR_ACTIVE)
            else:
                lbl.setStyleSheet(self._LBL_MOTOR_IDLE)

    def clear_motion_highlight(self) -> None:
        self.set_motion_highlight()

    def set_blocked(self, blocked: bool) -> None:
        for edit in self._coord_edits:
            edit.setEnabled(not blocked)
        for btn in self.findChildren(QtWidgets.QPushButton):
            btn.setEnabled(not blocked)

    def coord_edits(self):
        return list(self._coord_edits)
