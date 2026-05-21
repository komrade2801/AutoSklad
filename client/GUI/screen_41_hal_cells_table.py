from Core.app_logging import get_logger
from PyQt5.QtWidgets import QListWidgetItem

from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_41_hal_cells_table import Ui_screen_41_hal_cells_table
from GUI.widgets.widget_cell_hal_header import WidgetCellHalHeader
from GUI.widgets.widget_cell_hal_row import WidgetCellHalRow

logger = get_logger(__name__)


class screen_41_hal_cells_table(BaseScreen, Ui_screen_41_hal_cells_table):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.enable_touch_scroll = True
        self.event_hal_cell_row = None
        self._table_header = WidgetCellHalHeader()
        header_layout = self.widget_table_header.layout()
        if header_layout is None:
            from PyQt5.QtWidgets import QVBoxLayout

            header_layout = QVBoxLayout(self.widget_table_header)
            header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(self._table_header)
        self.normalize_screen_geometry()
        self._sync_table_geometry()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_table_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_table_geometry()

    def _table_viewport_width(self) -> int:
        return self.listWidget.viewport().width()

    def _sync_table_geometry(self) -> None:
        width = self._table_viewport_width()
        if width <= 0:
            return
        self._table_header.setFixedWidth(width)
        self._table_header.apply_column_widths(width)
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widget = self.listWidget.itemWidget(item)
            if widget is None:
                continue
            widget.setFixedWidth(width)
            widget.apply_column_widths(width)
            item.setSizeHint(widget.sizeHint())

    def set_data(self, *args, **kwargs):
        cells = kwargs.get("cells")
        if cells is None and args:
            first = args[0]
            if isinstance(first, dict):
                cells = first.get("cells")
            elif isinstance(first, list):
                cells = first
        if not cells:
            return

        self.listWidget.clear()
        width = self._table_viewport_width()
        for row in cells:
            if not isinstance(row, dict):
                continue
            widget = WidgetCellHalRow()
            widget.set_data(**row)
            widget.event_select_row = self._on_row_selected
            if width > 0:
                widget.setFixedWidth(width)
                widget.apply_column_widths(width)
            item = QListWidgetItem(self.listWidget)
            item.setSizeHint(widget.sizeHint())
            self.listWidget.addItem(item)
            self.listWidget.setItemWidget(item, widget)
        self._sync_table_geometry()

    def _on_row_selected(self, number: int):
        if callable(self.event_hal_cell_row):
            self.event_hal_cell_row(number)

    def get_data(self):
        return None
