from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from Core.app_logging import get_logger
from ..BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_widget_35_tool import Ui_widget_35_tool


class WidgetPlanCompleteTool(BaseScreen, Ui_widget_35_tool):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_data(self, tool):
        logger.debug("WidgetPlanCompleteTool set_data tool=%s tool_type=%s", tool, tool.get('tool_type'))
        tool_type = tool['tool_type']
        """Устанавливает текст. Реализуется в каждом экране."""
        self.lbl_name.setText(tool_type.name)
        self.lbl_count.setText(str(tool['load_count']))

    def get_data(self):
        pass

    def sizeHint(self):
        """Возвращает рекомендуемый размер виджета."""
        return QtCore.QSize(self.width(), self.height())