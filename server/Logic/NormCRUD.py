from datetime import datetime
from sqlalchemy.orm import Session

from DB.Engine.CRUD import BaseCRUD
# from DB.Engine.CRUD import BaseCRUD, T
# Импортируем модели и движки CRUD
from DB.Models.ActualNorm import ActualNorm
from DB.Models.ToolsNorm import ToolsNorm
from DB.Engine.ActualNormCRUD import EngineActualNorm
from DB.Engine.ToolsNormCRUD import EngineToolsNorm
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.ToolsCRUD import EngineTools
# from DB.Models.Type import Type


class EngineNorm(BaseCRUD):
    """
    Класс для агрегации данных из таблиц ActualNorm и ToolsNorm в единый формат.
    """
    def __init__(self, session: Session=None):        
        """        Инициализация сессии и создание экземпляров движков.
        """
        self.session = session
        self.engine_actual_norm = EngineActualNorm()
        self.engine_tools_norm = EngineToolsNorm()
        self.engine_user = EngineUser()
        self.engine_tools = EngineTools()
        #         
        super().__init__(session=session, model=ToolsNorm)


    def __get_username(self, user_id: int) -> str:
        """
        Dummy-функция для получения имени пользователя по его ID.
        В реальной реализации следует делать запрос в таблицу пользователей.
        """
        user = self.engine_user.get(user_id)
        # Предполагаем, что у объекта пользователя есть атрибут username
        if hasattr(user, 'username'):
            return user.username
        elif isinstance(user, dict) and 'username' in user:
            return user['username']
        return str(user)

    def __get_tool_name(self, tool_id: int) -> str:
        """
        Dummy-функция для получения названия инструмента по его ID.
        В реальной реализации следует делать запрос в таблицу инструментов.
        """
        tool = self.engine_tools.get(tool_id)
        if hasattr(tool, 'tool_name'):
            return tool.tool_name
        elif isinstance(tool, dict) and 'tool_name' in tool:
            return tool['tool_name']
        return str(tool)

    def find_and_update_tool_in_norm_from_user(self, user_id: int, tool_name: str) -> bool:
        """
        Находит запись инструмента по названию для пользователя и обновляет её.
        Например, обновляет поле sum_of_use на значение 0.
        """
        tool_record = None
        # Проходим по всем актуальным нормам данного пользователя
        actual_norms = self.session.query(ActualNorm).filter_by(user_id=user_id).all()
        for norm in actual_norms:
            tool_norms = self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).all()
            for t in tool_norms:
                current_tool_name = self.__get_tool_name(t.tools_id)
                if current_tool_name == tool_name:
                    tool_record = t
                    break
            if tool_record:
                break

        if tool_record:
            # Обновляем, например, поле sum_of_use на 0
            updated = self.engine_tools_norm.update(tool_record.id, summa_of_use=0)
            self.session.commit()
            return updated
        return False

    def find_tool_in_norm_from_user(self, user_id: int, tool_name: str) -> dict:
        """
        Находит и возвращает данные инструмента по названию для заданного пользователя.
        Если инструмент не найден, возвращается пустой словарь.
        """
        actual_norms = self.session.query(ActualNorm).filter_by(user_id=user_id).all()
        for norm in actual_norms:
            tool_norms = self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).all()
            for t in tool_norms:
                current_tool_name = self.__get_tool_name(t.tools_id)
                if current_tool_name == tool_name:
                    return {
                        "tool_name": current_tool_name,
                        "sum": f"{t.summa:.3f}" if t.summa is not None else "None",
                        "sum_of_periods": str(t.summa_of_periods) if t.summa_of_periods is not None else "None",
                        "type_periods": t.type_periods if t.type_periods is not None else "None",
                        "sum_of_use": str(t.summa_of_use) if t.summa_of_use is not None else "None",
                        "start_date": t.start_date.strftime("%d.%m.%Y") if t.start_date else "None"
                    }
        return {}

    def add_tool_to_norm_for_user(self, user_id: int, tool: dict) -> bool:
        """
        Добавляет новую запись нормы для инструмента для заданного пользователя.
        Ожидается, что tool - это словарь с ключами:
        tool_id, sum, sum_of_periods, type_periods, sum_of_use, start_date, description.
        """
        # Пытаемся найти существующую актуальную норму для пользователя
        actual_norm = self.session.query(ActualNorm).filter_by(user_id=user_id).first()
        if not actual_norm:
            # Если нормы нет, создаем новую с текущей датой
            if not self.engine_actual_norm.add_actual_norm(user_id, datetime.now()):
                return False
            actual_norm = self.session.query(ActualNorm).filter_by(user_id=user_id).first()

        result = self.engine_tools_norm.add_tools_norm(
            tools_id=tool.get("tool_id"),
            actual_norm_id=actual_norm.id,
            summa=tool.get("sum"),
            summa_of_periods=tool.get("sum_of_periods"),
            type_periods=tool.get("type_periods"),
            summa_of_use=tool.get("sum_of_use"),
            start_date=tool.get("start_date"),
            description=tool.get("description")
        )
        self.session.commit()
        return result

    def set_norm_data_from_user(self, user_id: int, data: dict) -> bool:
        """
        Устанавливает (создает) данные нормы для пользователя.
        Data должен содержать ключ 'tools' с набором инструментов.
        """
        # Если для пользователя еще нет актуальной нормы, создаем её
        actual_norm = self.session.query(ActualNorm).filter_by(user_id=user_id).first()
        if not actual_norm:
            if not self.engine_actual_norm.add_actual_norm(user_id, datetime.now()):
                return False
            actual_norm = self.session.query(ActualNorm).filter_by(user_id=user_id).first()

        # Добавляем все инструменты, переданные в data
        tools = data.get("tools", {})
        success = True
        for tool_key, tool_data in tools.items():
            if not self.add_tool_to_norm_for_user(user_id, tool_data):
                success = False
        self.session.commit()
        return success

    def update_norm_data_from_user(self, user_id: int, data: dict) -> bool:
        """
        Обновляет данные нормы для пользователя.
        Data должен содержать ключ 'tools' с набором инструментов для обновления.
        Если инструмент существует, обновляет его, иначе добавляет новый.
        """
        tools = data.get("tools", {})
        success = True
        for tool_key, tool_data in tools.items():
            tool_name = tool_data.get("tool_name")
            # Ищем существующую запись по названию инструмента
            existing_tool = self.find_tool_in_norm_from_user(user_id, tool_name)
            if existing_tool:
                # Получаем запись для обновления (поиск по tool_id в данном примере)
                actual_norms = self.session.query(ActualNorm).filter_by(user_id=user_id).all()
                tool_record = None
                for norm in actual_norms:
                    t = self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).filter(
                        ToolsNorm.tools_id == tool_data.get("tool_id")
                    ).first()
                    if t:
                        tool_record = t
                        break
                if tool_record:
                    updated = self.engine_tools_norm.update(
                        tool_record.id,
                        summa=tool_data.get("sum"),
                        summa_of_periods=tool_data.get("sum_of_periods"),
                        type_periods=tool_data.get("type_periods"),
                        summa_of_use=tool_data.get("sum_of_use"),
                        start_date=tool_data.get("start_date"),
                        description=tool_data.get("description")
                    )
                    if not updated:
                        success = False
            else:
                # Если запись не найдена, добавляем новый инструмент
                if not self.add_tool_to_norm_for_user(user_id, tool_data):
                    success = False
        self.session.commit()
        return success

    def get_norm_data_from_user(self, user_id) -> dict:
        """
        Получает агрегированные данные нормы для заданного пользователя.
        """
        norm_data = {"username": self.__get_username(user_id), "tools": {}}
        tools_list = []
        actual_norms = self.session.query(ActualNorm).filter_by(user_id=user_id).all()
        for norm in actual_norms:
            tool_norms = self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).all()
            for t in tool_norms:
                tool_entry = {
                    "tool_name": self.__get_tool_name(t.tools_id),
                    "sum": f"{t.summa:.3f}" if t.summa is not None else "None",
                    "sum_of_periods": str(t.summa_of_periods) if t.summa_of_periods is not None else "None",
                    "type_periods": t.type_periods if t.type_periods is not None else "None",
                    "sum_of_use": str(t.summa_of_use) if t.summa_of_use is not None else "None",
                    "start_date": t.start_date.strftime("%d.%m.%Y") if t.start_date else "None"
                }
                tools_list.append(tool_entry)
        # Преобразуем список инструментов в словарь с индексированными ключами
        for idx, tool in enumerate(tools_list):
            norm_data["tools"][str(idx)] = tool
        return norm_data

    def get_all_norm_data(self) -> dict:
        """
        Собирает и возвращает агрегированные данные в следующем формате:
        {
            "user": {
                "0": {
                    "username": "Иванов Иван",
                    "tools": {
                        "0": {
                            "tool_name": "сверло",
                            "sum": "999.000",
                            "sum_of_periods": "1",
                            "type_periods": "День",
                            "sum_of_use": "None",
                            "start_date": "18.11.2024"
                        },
                        ...
                    }
                },
                ...
            }
        }
        """
        norm_result = {"user": {}}
        # Получаем все записи актуальных норм
        actual_norms = self.engine_actual_norm.get_all_actual_norms()

        # Группируем данные по пользователям
        users_data = {}
        for norm in actual_norms:
            user_id = norm.user_id
            if user_id not in users_data:
                users_data[user_id] = {
                    "username": self.__get_username(user_id),
                    "tools": []
                }
            tool_norms = self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).all()
            for t in tool_norms:
                tool_entry = {
                    "tool_name": self.__get_tool_name(t.tools_id),
                    "sum": f"{t.summa:.3f}" if t.summa is not None else "None",
                    "sum_of_periods": str(t.summa_of_periods) if t.summa_of_periods is not None else "None",
                    "type_periods": t.type_periods if t.type_periods is not None else "None",
                    "sum_of_use": str(t.summa_of_use) if t.summa_of_use is not None else "None",
                    "start_date": t.start_date.strftime("%d.%m.%Y") if t.start_date else "None"
                }
                users_data[user_id]["tools"].append(tool_entry)

        norm_users = {}
        for idx, (user_id, user_info) in enumerate(users_data.items()):
            tools_dict = {}
            for tidx, tool in enumerate(user_info["tools"]):
                tools_dict[str(tidx)] = tool
            norm_users[str(idx)] = {
                "username": user_info["username"],
                "tools": tools_dict
            }

        norm_result["user"] = norm_users
        return norm_result

    def delete_last_tool(self, user_id: int, tool_name: str) -> bool:
        """
        Удаляет последнюю добавленную запись инструмента с указанным именем для пользователя.
        Возвращает True при успешном удалении, иначе False.
        """
        # Получаем все записи инструментов пользователя
        user_tools = []
        actual_norms = self.session.query(ActualNorm).filter_by(user_id=user_id).all()
        for norm in actual_norms:
            tools = self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).all()
            for tool in tools:
                if self.__get_tool_name(tool.tools_id) == tool_name:
                    user_tools.append(tool)

        if not user_tools:
            return False

        # Находим последнюю запись по максимальному ID
        last_tool = max(user_tools, key=lambda t: t.id)
        self.engine_tools_norm.delete(last_tool.id)
        self.session.commit()
        return True

    def delete_all_tools(self, user_id: int) -> bool:
        """
        Удаляет все инструменты для заданного пользователя.
        """
        # Удаляем все записи ToolsNorm, связанные с пользователем через ActualNorm
        actual_norms = self.session.query(ActualNorm).filter_by(user_id=user_id).all()
        for norm in actual_norms:
            self.session.query(ToolsNorm).filter_by(actual_norm_id=norm.id).delete()
        self.session.commit()
        return True