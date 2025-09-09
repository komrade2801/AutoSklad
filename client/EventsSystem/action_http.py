import json
import traceback

import requests

class ActionMapper:
    def __init__(self, executor):
        self.__executor = executor
        self.__config = self._load_config()

        self.__actions = {
            # 'http_get_request_take_command': lambda *args, **kwargs: self.http_get_request_take_command(*args, **kwargs),
            'http_parse_answer': lambda *args, **kwargs: self.http_parse_answer(*args, **kwargs),
            'http_post_request_send_data': lambda *args, **kwargs: self.http_post_request_send_data(*args, **kwargs),
            'http_wait_get_answer': lambda *args, **kwargs: self.http_wait_get_answer(*args, **kwargs),
            'http_wait_post_answer': lambda *args, **kwargs: self.http_wait_post_answer(*args, **kwargs),
        }
        self.__request__ = {
            'read_cnf': lambda *args, **kwargs: print("read_cnf", *args, **kwargs),  # read_db
            'read_history':lambda *args, **kwargs: print("read_history", *args, **kwargs),  # read_db
            'read_err':lambda *args, **kwargs: print("read_err", *args, **kwargs),  # read_db
            'read_users':lambda *args, **kwargs: print("read_users", *args, **kwargs),  # read_db
            'read_plans':lambda *args, **kwargs: print("read_plans", *args, **kwargs),  # read_db
            'read_rights_by_user_id':lambda *args, **kwargs: print("read_rights_by_user_id", *args, **kwargs),  # read_db
            'read_tools_by_plans_id':lambda *args, **kwargs: print("read_tools_by_plans_id", *args, **kwargs),  # read_db
            'read_mass_load_tools_by_plan':lambda *args, **kwargs: print("read_mass_load_tools_by_plan", *args, **kwargs),  # read_db
            'read_tools_by_group_id':lambda *args, **kwargs: print("read_tools_by_group_id", *args, **kwargs),  # read_db
            'read_groups':lambda *args, **kwargs: print("read_groups", *args, **kwargs),  # read_db
            'read_help':lambda *args, **kwargs: print("read_help", *args, **kwargs),  # read_db
            'read_operations':lambda *args, **kwargs: print("read_operations", *args, **kwargs),  # read_db
            'read_mass_drop_tools_by_plan':lambda *args, **kwargs: print("read_mass_drop_tools_by_plan", *args, **kwargs),  # read_db
            'read_mass_load_tools_by_free':lambda *args, **kwargs: print("read_mass_load_tools_by_free", *args, **kwargs),  # read_db
            'read_mass_drop_tools_by_free':lambda *args, **kwargs: print("read_mass_drop_tools_by_free", *args, **kwargs),  # read_db
            'write_help':lambda *args, **kwargs: print("write_help", *args, **kwargs),  # write_db
            'write_users':lambda *args, **kwargs: print("write_users", *args, **kwargs),  # write_db
            'write_plans':lambda *args, **kwargs: print("write_plans", *args, **kwargs),  # write_db
            'write_rights_by_user_id':lambda *args, **kwargs: print("write_rights_by_user_id", *args, **kwargs),  # write_db
            'write_mass_drop_tools_by_free':lambda *args, **kwargs: print("write_mass_drop_tools_by_free", *args, **kwargs),  # write_db
            'write_mass_load_tools_by_free':lambda *args, **kwargs: print("write_mass_load_tools_by_free", *args, **kwargs),  # write_db
            'write_mass_drop_tools_by_plan':lambda *args, **kwargs: print("write_mass_drop_tools_by_plan", *args, **kwargs),  # write_db
            'write_mass_load_tools_by_plan':lambda *args, **kwargs: print("write_mass_load_tools_by_plan", *args, **kwargs),  # write_db
        }


    def _load_config(self):
        """Загружает конфигурацию из config.json."""
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            print(traceback.format_exc())
            return {"serial_number": "unknown", "server_url": "http://localhost"}


    def execute(self, action, *args, **kwargs):
        """
        Выполняет заданное действие, если оно есть в списке.
        """
        if action in self.__actions:
            try:
                return self.__actions[action](*args, **kwargs)
            except Exception as e:
                print(f"Ошибка при выполнении {action}: {e}")
                print(traceback.format_exc())
        else:
            raise ValueError(f"Команда '{action}' не найдена.")

    def http_get_request_take_command(self, *args, **kwargs):
        """
        Запрашивает команды у сервера для текущего аппарата.
        Возвращает триггер для следующего действия.
        """
        try:
            # 1. Получаем серийный номер из конфигурации
            serial_number = self.__config.get("serial_number", "unknown")
            server_url = self.__config.get("server_url", "http://192.168.0.10/devices")

            # 2. Формируем URL для запроса команд
            url = f"{server_url}/command"
            params = {"serial_number": serial_number}

            # 3. Выполняем GET-запрос
            response = requests.get(url, params=kwargs)
            response.raise_for_status()  # Проверяем на ошибки HTTP

            # 4. Извлекаем команду из ответа
            command_data = response.json()
            if "command" in command_data:
                return {"trigger": "send_request_get", "command": command_data["command"]}
            else:
                print("Ошибка: команда не найдена в ответе сервера")
                return {"trigger": "cmd_empty"}

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении GET-запроса: {e}")
            print(traceback.format_exc())
            return {"trigger": "cmd_empty"}
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            print(traceback.format_exc())
            return {"trigger": "cmd_empty"}

        # return {'trigger':'send_request_get'}


    def http_parse_answer(self, *args, **kwargs):
        return {'trigger': 'empty'}

    def http_post_request_send_data(self, *args, **kwargs):
        return {'trigger': 'send_request_get'}

    def http_wait_answer(self, *args, **kwargs):
        return {'trigger': 'received_command'}

    def http_wait_get_answer(self, *args, **kwargs):
        return {'trigger': 'received_command'}

    def http_wait_post_answer(self, *args, **kwargs):
        return {'trigger': 'received_ok'}
