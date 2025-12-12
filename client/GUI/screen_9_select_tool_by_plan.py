import traceback

from PyQt5 import QtGui
from PyQt5.QtWidgets import QListWidgetItem

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_9_select_tool_by_plan import Ui_screen_9_select_tool_by_plan
from .widgets.widget_plan_tool import WidgetPlanTool


class screen_9_select_tool_by_plan(BaseScreen, Ui_screen_9_select_tool_by_plan):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.event_select_tool = lambda *args, **kwargs: print("screen_9_select_tool_by_plan", *args, **kwargs)

        self.plan_id_val = -1
        self.value = None
        self.trigger = None
        self.tool_list = {}

    def set_data(self, *args, **kwargs):
        print("screen_9_select_tool_by_plan set_data")
        print(args)
        print(kwargs)
        """Устанавливает текст. Реализуется в каждом экране.
        Отображает данные в listWidget.

        Ожидается, что данные передаются в виде:
        [{'id': 1, 'name': 'Group Name', 'description': 'Description', 'status': 0}, ...]
        """
        # self.tool_list = {}

        try:
            source = args[1]
            if source == 'btn_back':
                print('data restored')
            else:
                data = args[0]

                self.plan_number.setText(data[1])
                self.plan_name.setText(data[2])

                self.plan_id_val = data[3]

                tools = data[0]
                if not tools:
                    return
                self.listWidget.clear()  # Очищаем список перед добавлением новых данных

                can_be_completed = False

                for tool_data in tools:
                    print(tool_data)

                    has_tools = tool_data['has_tools']

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
        print(f"screen_9_select_tool_by_plan get_data {args} {kwargs} {self.value}, self.tool_list {self.tool_list}")
        try:
            # if self.value:
            #     return {"tool_type_id": self.value[0], "name": self.value[1], "group_name": self.value[2], "tool_description": self.value[3]}
            # else:
            #     return {"plan_id": self.plan_id_val}
            value = self.tool_list
            self.tool_list = {}
            return {"tool_list": value, "plan_id": self.plan_id_val}
        except:
            print(traceback.format_exc())


    # def handle_select_tool(self, *args, **kwargs):
    #     print("screen_9_select_tool_by_plan handle_select_tool")
    #     print(args)
    #     print(kwargs)
    #     self.value, self.trigger = args
    #     self.event_select_tool(self.value[0], self.trigger)

    def toolsCountUpdate(self, id: int, count: int):
        print(f"toolsCountUpdate id {id}, count {count}")

        if count == 0 and self.tool_list.get(id):
            self.tool_list.pop(id)
        else:
            self.tool_list.update({id: count})

        print(f"self.tool_list {self.tool_list}")

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
