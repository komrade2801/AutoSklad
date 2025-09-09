from EventsSystem.action_db import ActionMapper as ActionMapper_db
from EventsSystem.action_cmd import ActionMapper as ActionMapper_cmd
from EventsSystem.action_cnf import ActionMapper as ActionMapper_cnf
# from EventsSystem.action_http import ActionMapper as ActionMapper_http

class ActionSelector:
    def __init__(self, executor):
        # Создаем модули с ActionMapper
        self.__db_mapper = ActionMapper_db(executor)
        self.__cmd_mapper = ActionMapper_cmd(executor)
        self.__cnf_mapper = ActionMapper_cnf(executor)
        # self.__http_mapper = ActionMapper_http(executor)
        self.mappers = {
            "db" : self.__db_mapper,
            "cmd" : self.__cmd_mapper,
            "cnf" : self.__cnf_mapper,
            # "http" : self.__http_mapper
        }

    def get_mapper(self, action):
        actors = action.split("_")
        for actor in actors:
            if actor in list(self.mappers.items())[0]:
                return self.__db_mapper
            elif actor in list(self.mappers.items())[1]:
                return self.__cmd_mapper
            elif actor in list(self.mappers.items())[2]:
                return self.__cnf_mapper
            # elif actor in list(self.mappers.items())[3]:
            #     return self.__http_mapper

        raise ValueError(f"Модуль не найден для действия '{action}'.")
