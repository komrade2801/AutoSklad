from PyQt5 import QtCore, QtWidgets

from GUI.BaseScreen import BaseScreen

FONT_SIZE_PX = 22
COL_NUM_WIDTH = 56
ROW_H_MARGIN = 16


def hal_table_column_widths(viewport_width: int):
    """Ширины столбцов: № фиксированный, X и Z — поровну на оставшуюся ширину."""
    inner = max(0, viewport_width - ROW_H_MARGIN)
    remaining = max(0, inner - COL_NUM_WIDTH)
    half = remaining // 2
    return COL_NUM_WIDTH, half, remaining - half


def _cell_style() -> str:
    return f"color: #FFFFFF; font-size: {FONT_SIZE_PX}px;"


class WidgetCellHalRow(BaseScreen):
    """Строка таблицы HAL: номер ячейки, hal_x, hal_z."""

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setObjectName("widget_cell_hal_row")
        self.cell_id = None
        self.cell_number = None

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(0)

        style = _cell_style()
        self.lbl_number = QtWidgets.QLabel(self)
        self.lbl_hal_x = QtWidgets.QLabel(self)
        self.lbl_hal_z = QtWidgets.QLabel(self)
        for lbl in (self.lbl_number, self.lbl_hal_x, self.lbl_hal_z):
            lbl.setStyleSheet(style)
            lbl.setAlignment(QtCore.Qt.AlignCenter)

        root.addWidget(self.lbl_number)
        root.addWidget(self.lbl_hal_x)
        root.addWidget(self.lbl_hal_z)

    def apply_column_widths(self, viewport_width: int) -> None:
        num_w, x_w, z_w = hal_table_column_widths(viewport_width)
        self.lbl_number.setFixedWidth(num_w)
        self.lbl_hal_x.setFixedWidth(x_w)
        self.lbl_hal_z.setFixedWidth(z_w)

    def set_data(self, *args, **kwargs):
        self.cell_id = kwargs.get("cell_id")
        self.cell_number = kwargs.get("number")
        hx = kwargs.get("hal_x")
        hz = kwargs.get("hal_z")
        self.lbl_number.setText(str(self.cell_number or "—"))
        self.lbl_hal_x.setText("NULL" if hx is None else str(int(hx)))
        self.lbl_hal_z.setText("NULL" if hz is None else str(int(hz)))

    def get_data(self):
        pass

    def sizeHint(self):
        return QtCore.QSize(self.width(), 52)
