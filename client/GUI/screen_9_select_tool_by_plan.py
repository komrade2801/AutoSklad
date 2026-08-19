import traceback

from Core.app_logging import get_logger
from PyQt5 import QtGui
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen

logger = get_logger(__name__)
from .ui_classes.Ui_screen_9_select_tool_by_plan import Ui_screen_9_select_tool_by_plan
from .widgets.widget_plan_tool import WidgetPlanTool


class screen_9_select_tool_by_plan(BaseScreen, Ui_screen_9_select_tool_by_plan):
    def __init__(self):
        super().__init__()
        self.enable_touch_scroll = True
        self.setupUi(self)
        self.event_select_tool = lambda *args, **kwargs: logger.debug("screen_9_select_tool_by_plan %s %s", args, kwargs)

        self.plan_id_val = -1
        self.value = None
        self.trigger = None
        self.tool_list = {}
        # Не показываем UI-плейсхолдеры до получения валидных данных по чертежу.
        self.plan_number.setText("")
        self.plan_name.setText("")

    def set_data(self, *args, **kwargs):
        logger.debug("screen_9_select_tool_by_plan set_data args=%s kwargs=%s", args, kwargs)
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        # self.tool_list = {}

        try:
            payload, source = self.split_set_data_args(args, kwargs)
            if source == 'btn_back':
                logger.debug('data restored')
            else:
                if not isinstance(payload, (tuple, list)) or len(payload) < 4:
                    logger.warning("screen_9_select_tool_by_plan: invalid payload: %s", payload)
                    self.plan_number.setText("")
                    self.plan_name.setText("")
                    self.plan_id_val = -1
                    self.listWidget.clear()
                    self.setOkButtonState(False)
                    self.setCompleteButtonState(False)
                    return

                data = payload

                self.plan_number.setText(data[1])
                self.plan_name.setText(data[2])

                self.plan_id_val = data[3]

                tools = data[0]
                self.listWidget.clear()  # Очищаем список перед добавлением новых данных
                if not tools:
                    self.setOkButtonState(False)
                    self.setCompleteButtonState(False)
                    return

                can_be_completed = False

                for tool_data in tools:
                    logger.debug("tool_data: %s", tool_data)

                    # Создаём кастомный виджет
                    widget = WidgetPlanTool()
                    widget.set_data(tool_data, self.toolsCountUpdate)  # Передаём данные в кастомный виджет
                    # widget.event_select_tool = self.handle_select_tool
                    # widget.setSizeHint(QtCore.QSize(440, 80))  # Ширина и высота виджета
                    list_item = QListWidgetItem(self.listWidget)
                    list_item.setSizeHint(widget.sizeHint())  # Используем размер из виджета

                    if tool_data["load_count"] == 0:
                        widget.setDisabled(True)
                        widget.background.setStyleSheet("background-color: grey")

                    if tool_data["load_count"] < tool_data["plan_count"]:
                        can_be_completed = True

                    self.listWidget.addItem(list_item)
                    self.listWidget.setItemWidget(list_item, widget)

                self.setOkButtonState(False)
                self.setCompleteButtonState(can_be_completed)

        except Exception as e:
            print(traceback.format_exc())
            print(e)
    pass

    def get_data(self, *args, **kwargs):
        logger.debug("screen_9_select_tool_by_plan get_data args=%s kwargs=%s value=%s tool_list=%s",
                     args, kwargs, self.value, self.tool_list)
        try:
            # if self.value:
            #     return {"tool_type_id": self.value[0], "name": self.value[1], "group_name": self.value[2], "tool_description": self.value[3]}
            # else:
            #     return {"plan_id": self.plan_id_val}
            value = self.tool_list
            self.tool_list = {}
            return {"tool_list": value, "plan_id": self.plan_id_val}
        except Exception:
            logger.exception("screen_9_select_tool_by_plan get_data")


    # def handle_select_tool(self, *args, **kwargs):
    #     print("screen_9_select_tool_by_plan handle_select_tool")
    #     print(args)
    #     print(kwargs)
    #     self.value, self.trigger = args
    #     self.event_select_tool(self.value[0], self.trigger)

    def toolsCountUpdate(self, id: int, count: int):
        logger.debug("toolsCountUpdate id %s, count %s", id, count)

        if count == 0 and self.tool_list.get(id):
            self.tool_list.pop(id)
        else:
            self.tool_list.update({id: count})

        logger.debug("self.tool_list=%s", self.tool_list)

        if self.tool_list:
            self.setOkButtonState(True)
        else:
            self.setOkButtonState(False)

    def setOkButtonState(self, state):
        if state:
            icon_path = ":/icons/ok.png"
            self.btn_ok.setDisabled(False)
        else:
            icon_path = ":/icons/ok_disabled.png"
            self.btn_ok.setDisabled(True)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.btn_ok.setIcon(icon1)

    def setCompleteButtonState(self, state):
        if state:
            icon_path = ":/icons/plan-completed.png"
            self.btn_complete.setDisabled(False)
        else:
            icon_path = ":/icons/plan-completed_disabled.png"
            self.btn_complete.setDisabled(True)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.btn_complete.setIcon(icon1)
