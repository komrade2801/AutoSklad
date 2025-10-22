import traceback

from .BaseScreen import BaseScreen
from .ui_classes.Ui_screen_3_authorization import Ui_screen_3_authorization
from .helper.MyLineEdit import MyLineEdit
from .widgets.widget_keyboard import WidgetKeyboard
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QTimer


class screen_3_authorization(BaseScreen, Ui_screen_3_authorization):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


        self.__is_read = True
        self.__is_write = False

        self.trigger_length_psw = 4
        self.trigger_length_login = 4

        self.trigger_max_length_psw = 5
        self.trigger_max_length_login = 5

        self.length_trigger_enable = True

        # Подключение сигналов MyLineEdit
        self.edit_psw.focus_in.connect(self.on_focus_in)
        self.edit_psw.focus_out.connect(self.on_focus_out)
        self.edit_login.focus_in.connect(self.on_focus_in)
        self.edit_login.focus_out.connect(self.on_focus_out)

        self.keyboard = WidgetKeyboard()
        self.keyboard.setParent(self)
        self.keyboard.hide()
        self.keyboard.btn_close.clicked.connect(self.hide_keyboard)

        self.btn_keyboard.clicked.connect(self.show_keyboard)
        self.focus_object_name = ""
        self.keyboard.btn_number_0.clicked.connect(lambda: self.add_value_key('0'))
        self.keyboard.btn_number_1.clicked.connect(lambda: self.add_value_key('1'))
        self.keyboard.btn_number_2.clicked.connect(lambda: self.add_value_key('2'))
        self.keyboard.btn_number_3.clicked.connect(lambda: self.add_value_key('3'))
        self.keyboard.btn_number_4.clicked.connect(lambda: self.add_value_key('4'))
        self.keyboard.btn_number_5.clicked.connect(lambda: self.add_value_key('5'))
        self.keyboard.btn_number_6.clicked.connect(lambda: self.add_value_key('6'))
        self.keyboard.btn_number_7.clicked.connect(lambda: self.add_value_key('7'))
        self.keyboard.btn_number_8.clicked.connect(lambda: self.add_value_key('8'))
        self.keyboard.btn_number_9.clicked.connect(lambda: self.add_value_key('9'))

        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.timeout_back = int(self.lbl_timeout_back.text())
        self.__timeout_back = self.timeout_back
        self.event_timeout_back = lambda *args, **kwargs: self.hide()
        self.edit_psw.textChanged.connect(self.on_password_changed)
        self.psw = ""
        self.edit_login.textChanged.connect(self.on_login_changed)
        self.login = ""
        self.event_edit_psw = lambda text, *args, **kwargs: print(text)
        self.event_edit_login = lambda text, *args, **kwargs: print(text)
        self.event_input_name_code = lambda text, *args, **kwargs: print(text)

    def on_login_changed(self, text):
        print(f"on_login_changed. Input text: {text}")
        if len(text)==0:
            print(f"clear login text: {text}")
            self.login = ''
            return
        if ((len(text) >= self.trigger_length_login) and
                (len(text) < self.trigger_max_length_login)):
            self.login = text  # Обновляем переменную
            self.event_input_name_code(self.login)
            self.edit_login.setStyleSheet("color: #FFFFFF;")
        elif len(text) >= self.trigger_max_length_login:
            self.edit_login.setStyleSheet("color: #FF0000;")


    def on_password_changed(self, text):
        print(f"on_password_changed. Input text: {text}")
        # Обновляем переменную
        try:
            if len(text)==0:
                print(f"clear password text: {text}")
                self.psw = ''
                return
            elif len(text)==1 and text != "*":
                self.psw = text
            else:
                char = text[len(text)-1]
                if char != "*":
                    self.psw = self.psw + char
            self.edit_psw.setText("*"*len(text))
        except:
            print(len(text))
            print(traceback.format_exc())

        if ((len(text) >= self.trigger_length_psw) and
                (len(text) < self.trigger_max_length_psw)):
                # self.event_input_name_code(self.psw)
                # print(f"Password updated: {self.psw}")
                self.hide_keyboard("")

                # self.edit_login.setStyleSheet("color: rgb(0, 0, 174);")

    def check_visibility(self):
        if self.timeout_back > 1:
            self.timeout_back = self.timeout_back - 1
            self.lbl_timeout_back.setText(str(self.timeout_back))
        else:
            self.timeout_back = self.__timeout_back
            self.lbl_timeout_back.setText(str(self.timeout_back))
            self.hide_keyboard(self.objectName())
            self.event_timeout_back("timeout_back")

    def showEvent(self, event):
        """Событие, которое срабатывает, когда виджет показывается."""
        super().showEvent(event)
        self.edit_login.setText("")
        self.edit_psw.setText("")
        self.visibility_timer.start(1000)
        self.timeout_back = self.__timeout_back
        # self.edit_login.setStyleSheet("color: rgb(0, 0, 0);")
        # self.edit_psw.setStyleSheet("color: rgb(0, 0, 0);")
        self.edit_login.setStyleSheet("color: #000000;\n"
            "background-color: #CAE2FF;\n"
            "border-width: 2px;\n"
            "border-style: groove;\n"
            "border-color: #15293D;\n"
            "border-radius: 0px;")
        self.edit_psw.setStyleSheet("color: #000000;\n"
            "background-color: #CAE2FF;\n"
            "border-width: 2px;\n"
            "border-style: groove;\n"
            "border-color: #15293D;\n"
            "border-radius: 0px;")


    def hideEvent(self, event):
        """Событие, которое срабатывает, когда виджет скрывается."""
        super().hideEvent(event)
        self.visibility_timer.stop()
        self.timeout_back = self.__timeout_back


    def add_value_key(self, value):
        edit = self.findChild(MyLineEdit, self.focus_object_name)
        edit.setText(edit.text() + value)

    def hide_keyboard(self, object_name):
        self.btn_keyboard.show()
        self.btn_authorization.show()
        self.btn_back.show()
        self.lbl_timeout_back.show()
        self.label_info_1.show()
        self.btn_authorization.setFocus()
        self.keyboard.hide()
        self.focus_object_name = ""

    def show_keyboard(self, object_name):
        """Отображение клавиатуры."""

        self.btn_keyboard.hide()
        self.btn_authorization.hide()
        self.btn_back.hide()

        self.lbl_timeout_back.hide()
        self.label_info_1.hide()

        x, y, w, h = self.calculate_keyboard_position()
        self.keyboard.setGeometry(x, y, w, h)  # Устанавливаем положение клавиатуры
        self.keyboard.show()
        self.keyboard.raise_()  # Поднимаем клавиатуру поверх всех виджетов

    def calculate_keyboard_position(self):
        """Вычисляет положение клавиатуры на экране."""
        screen_width = self.width()
        screen_height = self.height()
        keyboard_width = self.keyboard.width()
        keyboard_height = self.keyboard.height()

        # Центрирование клавиатуры внизу экрана
        x = (screen_width - keyboard_width) // 2
        y = screen_height - keyboard_height - 10  # Отступ 10 пикселей от нижнего края
        return x, y, keyboard_width, keyboard_height

    def on_focus_in(self, object_name):
        self.focus_object_name = object_name
        self.show_keyboard(object_name)
        self.timeout_back = self.__timeout_back

    def on_focus_out(self, object_name):...

    def is_read(self):
        return self.__is_read

    def is_write(self):
        return self.__is_write

    def set_data(self, *args, **kwargs):
        """Устанавливает текст. Реализуется в каждом экране."""
        print(f"set_data. Input args: {args}")
        try:
            if not isinstance(args, tuple):
                return
            if not isinstance(args[0], str):
                return
            if not len(args[0]) > 1:
                return
            full = args[0].split(" ")
            name = f"{full[0][0]}. {full[1][0]}. {full[2]}"
            self.edit_login.setText(name)
            self.edit_psw.setFocus()
        except:
            print(traceback.format_exc())

    def get_data(self):
        print(f"Before clearing: login={self.login}, password={self.psw}")

        # if self.psw == '':
        #     return
        arr = {"login": self.login, "password": self.psw}
        # print(f"Returning: {arr}")
        # if self.login != '' and self.psw != '':
        #     self.login = ''
        #     self.psw = ''
        return arr

    def handle_callback_executor(self, *args, **kwargs):
        print(f"handle_callback_executor. Input args: {args}")

        print(f"args[0]: {args[0]}")
        print(f"args[1]: {args[1]}")
        # print(f"args[2]: {args[2]}")

        self.psw = ""
        self.login = ""

        # Проверим, что первый аргумент существует и является списком
        triggers = args[0] if len(args) > 0 and isinstance(args[0], list) else []

        print(f"len(args): {len(args)}")
        print(f"isinstance(args[1], tuple): {isinstance(args[1], tuple)}")
        # Проверим, что второй аргумент существует и является кортежем
        user_and_role = args[1] if len(args) > 1 and isinstance(args[1], tuple) else ()
        print(f"user_and_role: {user_and_role}")

        # Извлечем пользователя и роль, если они есть
        user = user_and_role[0] if len(user_and_role) > 0 else None
        role = user_and_role[1] if len(user_and_role) > 1 else None

        print(f"user: {user}")
        print(f"role: {role}")
        if not user or not role:
            return 'err_authorization'
        # Вывод данных
        print("Triggers:", triggers)
        print("User:", user)
        print("Role:", role)
        role_name = role.name.lower()
        # Маппинг ролей к триггерам для корректного выбора destination
        role_to_trigger = {
            'stockman': 'type_storekeeper',
            'user': 'test_user',
            'admin': 'view_type_admin',
            'developer': 'view_type_admin',  # Developer имеет админские права
            'engineer': 'test_user',  # Если понадобится
            'manager': 'type_storekeeper'  # Если понадобится
        }
        if role_name in role_to_trigger:
            trigger_name = role_to_trigger[role_name]
            print(f'trigger: {trigger_name}')
            return trigger_name
        else:
            print(f'No matching trigger for role: {role_name}')
            return 'err_authorization'
