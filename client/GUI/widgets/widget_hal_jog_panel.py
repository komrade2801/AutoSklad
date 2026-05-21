from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from EventsSystem.hal_coords import (
    HAL_SAVE_MOT_X_INDEX,
    HAL_SAVE_MOT_Z_INDEX,
    MOT_STEP_MAX,
    MOT_STEP_MIN,
    message_for_reason,
    parse_uint,
    validate_motor_position_texts,
)


class WidgetHalJogPanel(QtWidgets.QWidget):
    """Панель JOG: координаты M1..M5 (ввод), ±, кнопка «Отправка»."""

    _BTN_STYLE = (
        "QPushButton { color: #FFFFFF; background-color: #f09022;"
        "border-radius: 8px; font-size: 22px; font-weight: 600; min-height: 40px; }"
        "QPushButton:disabled { background-color: #6a7a8f; color: #cccccc; }"
    )
    _LBL_MOTOR_IDLE = "color: #FFFFFF; font-size: 18px; font-weight: 600;"
    _LBL_MOTOR_ACTIVE = (
        "color: #FFFFFF; font-size: 18px; font-weight: 600;"
        "background-color: #2d7a3e; border-radius: 6px; padding: 2px 6px;"
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
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._motor_labels = []
        self._coord_edits = []
        self.event_hal_jog = None
        self.event_hal_mot_send = None

        mot_validator = QtGui.QIntValidator(MOT_STEP_MIN, MOT_STEP_MAX, self)

        for i in range(1, 6):
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(8)
            lbl_motor = QtWidgets.QLabel(f"M{i}", self)
            lbl_motor.setMinimumWidth(40)
            lbl_motor.setStyleSheet(self._LBL_MOTOR_IDLE)
            lbl_motor.setObjectName(f"lbl_mot_{i}_title")

            edit_coord = QtWidgets.QLineEdit("0", self)
            edit_coord.setAlignment(QtCore.Qt.AlignCenter)
            edit_coord.setMinimumHeight(40)
            edit_coord.setStyleSheet(self._EDIT_OK)
            edit_coord.setValidator(mot_validator)
            edit_coord.setObjectName(f"edit_mot_{i}_coord")
            edit_coord.setFocusPolicy(QtCore.Qt.ClickFocus)

            btn_minus = QtWidgets.QPushButton("−", self)
            btn_minus.setObjectName(f"hal_jog_m{i}_minus")
            btn_minus.setStyleSheet(self._BTN_STYLE)
            btn_plus = QtWidgets.QPushButton("+", self)
            btn_plus.setObjectName(f"hal_jog_m{i}_plus")
            btn_plus.setStyleSheet(self._BTN_STYLE)

            row.addWidget(lbl_motor)
            row.addWidget(edit_coord, 1)
            row.addWidget(btn_minus, 1)
            row.addWidget(btn_plus, 1)
            layout.addLayout(row)
            self._motor_labels.append(lbl_motor)
            self._coord_edits.append(edit_coord)

            for name in (f"hal_jog_m{i}_minus", f"hal_jog_m{i}_plus"):
                btn = self.findChild(QtWidgets.QPushButton, name)
                if btn:
                    btn.clicked.connect(
                        lambda checked=False, n=name: self._on_jog(n)
                    )

        self.btn_hal_mot_send = QtWidgets.QPushButton("Отправка", self)
        self.btn_hal_mot_send.setObjectName("btn_hal_mot_send")
        self.btn_hal_mot_send.setStyleSheet(self._SEND_BTN_STYLE)
        self.btn_hal_mot_send.clicked.connect(self._on_send_clicked)
        layout.addWidget(self.btn_hal_mot_send)

    def _on_jog(self, trigger_name: str):
        if callable(self.event_hal_jog):
            self.event_hal_jog(trigger_name)

    def _on_send_clicked(self):
        if callable(self.event_hal_mot_send):
            self.event_hal_mot_send()

    def set_motor_positions(self, positions) -> None:
        if not positions:
            return
        for i, val in enumerate(positions[:5]):
            self._coord_edits[i].blockSignals(True)
            self._coord_edits[i].setText(str(int(val)))
            self._coord_edits[i].setStyleSheet(self._EDIT_OK)
            self._coord_edits[i].blockSignals(False)

    def motor_coord_texts(self) -> list:
        return [(e.text() or "").strip() for e in self._coord_edits]

    def parse_motor_positions(self):
        """
        (positions, bad_index, reason) — без подстановки 0 при ошибке.
        """
        return validate_motor_position_texts(self.motor_coord_texts())

    def get_motor_positions(self) -> list:
        positions, _bad, _reason = self.parse_motor_positions()
        if positions is None:
            return []
        return positions

    def get_mot13_hal_xz(self):
        """
        Координаты для сохранения в ячейку: M1 → hal_x, M3 → hal_z.
        Возвращает (hal_x, hal_z, bad_index, reason).
        """
        texts = self.motor_coord_texts()
        out = []
        indices = (
            (HAL_SAVE_MOT_X_INDEX, "M1"),
            (HAL_SAVE_MOT_Z_INDEX, "M3"),
        )
        for idx, _label in indices:
            raw = texts[idx] if idx < len(texts) else ""
            value, reason = parse_uint(
                raw,
                min_value=MOT_STEP_MIN,
                max_value=MOT_STEP_MAX,
            )
            if reason:
                return None, None, idx, reason
            out.append(value)
        return out[0], out[1], None, None

    def set_field_error(self, index: Optional[int], active: bool) -> None:
        for i, edit in enumerate(self._coord_edits):
            edit.setStyleSheet(self._EDIT_ERR if active and i == index else self._EDIT_OK)

    def clear_field_errors(self) -> None:
        for edit in self._coord_edits:
            edit.setStyleSheet(self._EDIT_OK)

    def validation_error_message(self) -> Optional[str]:
        _positions, bad_index, reason = self.parse_motor_positions()
        if bad_index is None:
            return None
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
            elif motor_index is not None and i == motor_index:
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
