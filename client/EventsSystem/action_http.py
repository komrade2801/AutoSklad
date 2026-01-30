import json
import logging
import traceback

import requests

logger = logging.getLogger(__name__)


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
            'read_cnf': lambda *args, **kwargs: logger.debug("read_cnf %s %s", args, kwargs),  # read_db
            'read_history': lambda *args, **kwargs: logger.debug("read_history %s %s", args, kwargs),  # read_db
            'read_err': lambda *args, **kwargs: logger.debug("read_err %s %s", args, kwargs),  # read_db
            'read_users': lambda *args, **kwargs: logger.debug("read_users %s %s", args, kwargs),  # read_db
            'read_plans': lambda *args, **kwargs: logger.debug("read_plans %s %s", args, kwargs),  # read_db
            'read_rights_by_user_id': lambda *args, **kwargs: logger.debug("read_rights_by_user_id %s %s", args, kwargs),  # read_db
            'read_tools_by_plans_id': lambda *args, **kwargs: logger.debug("read_tools_by_plans_id %s %s", args, kwargs),  # read_db
            'read_mass_load_tools_by_plan': lambda *args, **kwargs: logger.debug("read_mass_load_tools_by_plan %s %s", args, kwargs),  # read_db
            'read_tools_by_group_id': lambda *args, **kwargs: logger.debug("read_tools_by_group_id %s %s", args, kwargs),  # read_db
            'read_groups': lambda *args, **kwargs: logger.debug("read_groups %s %s", args, kwargs),  # read_db
            'read_help': lambda *args, **kwargs: logger.debug("read_help %s %s", args, kwargs),  # read_db
            'read_operations': lambda *args, **kwargs: logger.debug("read_operations %s %s", args, kwargs),  # read_db
            'read_mass_drop_tools_by_plan': lambda *args, **kwargs: logger.debug("read_mass_drop_tools_by_plan %s %s", args, kwargs),  # read_db
            'read_mass_load_tools_by_free': lambda *args, **kwargs: logger.debug("read_mass_load_tools_by_free %s %s", args, kwargs),  # read_db
            'read_mass_drop_tools_by_free': lambda *args, **kwargs: logger.debug("read_mass_drop_tools_by_free %s %s", args, kwargs),  # read_db
            'write_help': lambda *args, **kwargs: logger.debug("write_help %s %s", args, kwargs),  # write_db
            'write_users': lambda *args, **kwargs: logger.debug("write_users %s %s", args, kwargs),  # write_db
            'write_plans': lambda *args, **kwargs: logger.debug("write_plans %s %s", args, kwargs),  # write_db
            'write_rights_by_user_id': lambda *args, **kwargs: logger.debug("write_rights_by_user_id %s %s", args, kwargs),  # write_db
            'write_mass_drop_tools_by_free': lambda *args, **kwargs: logger.debug("write_mass_drop_tools_by_free %s %s", args, kwargs),  # write_db
            'write_mass_load_tools_by_free': lambda *args, **kwargs: logger.debug("write_mass_load_tools_by_free %s %s", args, kwargs),  # write_db
            'write_mass_drop_tools_by_plan': lambda *args, **kwargs: logger.debug("write_mass_drop_tools_by_plan %s %s", args, kwargs),  # write_db
            'write_mass_load_tools_by_plan': lambda *args, **kwargs: logger.debug("write_mass_load_tools_by_plan %s %s", args, kwargs),  # write_db
        }


    def _load_config(self):
        """Загружает конфигурацию из config.json."""
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logger.exception("Ошибка загрузки конфигурации: %s", e)
            return {"serial_number": "unknown", "server_url": "http://localhost"}


    def execute(self, action, *args, **kwargs):
        """
        Выполняет заданное действие, если оно есть в списке.
        """
        if action in self.__actions:
            try:
                return self.__actions[action](*args, **kwargs)
            except Exception as e:
                logger.exception("Ошибка при выполнении %s: %s", action, e)
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
                logger.warning("Ошибка: команда не найдена в ответе сервера")
                return {"trigger": "cmd_empty"}

        except requests.exceptions.RequestException as e:
            logger.exception("Ошибка при выполнении GET-запроса: %s", e)
            return {"trigger": "cmd_empty"}
        except Exception as e:
            logger.exception("Неизвестная ошибка: %s", e)
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
