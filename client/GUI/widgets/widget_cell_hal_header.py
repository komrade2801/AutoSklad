from PyQt5 import QtCore, QtWidgets

from GUI.widgets.widget_cell_hal_row import FONT_SIZE_PX, hal_table_column_widths


class WidgetCellHalHeader(QtWidgets.QWidget):
    """Фиксированная строка заголовков таблицы HAL: №, X, Z."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("widget_cell_hal_header")
        self.setFixedHeight(44)

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(0)

        header_style = (
            f"color: #FFFFFF; font-size: {FONT_SIZE_PX}px; font-weight: 700;"
        )
        self.lbl_num = QtWidgets.QLabel("№", self)
        self.lbl_x = QtWidgets.QLabel("X", self)
        self.lbl_z = QtWidgets.QLabel("Z", self)
        for lbl in (self.lbl_num, self.lbl_x, self.lbl_z):
            lbl.setStyleSheet(header_style)
            lbl.setAlignment(QtCore.Qt.AlignCenter)

        root.addWidget(self.lbl_num)
        root.addWidget(self.lbl_x)
        root.addWidget(self.lbl_z)

        self.apply_column_widths(self.width() or 456)

    def apply_column_widths(self, viewport_width: int) -> None:
        num_w, x_w, z_w = hal_table_column_widths(viewport_width)
        self.lbl_num.setFixedWidth(num_w)
        self.lbl_x.setFixedWidth(x_w)
        self.lbl_z.setFixedWidth(z_w)

    def sizeHint(self):
        return QtCore.QSize(self.width(), 44)
