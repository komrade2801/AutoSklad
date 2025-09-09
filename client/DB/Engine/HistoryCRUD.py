from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Type
from DB.Engine.BaseCRUD import BaseCRUD  # Предполагается, что BaseCRUD уже реализован
from DB.Models.History import History  # Импорт модели History
from DB.Models.Role import Role  # Импорт модели  Role
from DB.Models.User import User  # Импорт модели  User
from DB.Models.Tools import Tools  # Импорт модели  Tools
from DB.Models.Plan import Plan  # Импорт модели  Plan


class EngineHistory(BaseCRUD):
    """
    Класс EngineHistory предоставляет интерфейс для работы с таблицей History.
    Инкапсулирует логику CRUD операций и предоставляет методы для работы с историей действий пользователей,
    ролями, инструментами и чертежами.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineHistory.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, History)

    def add_history(self,
                    id: int,
                    user_id: int,
                    role_id: int,
                    tools_id: int,
                    datetime_value,
                    status: Optional[int] = None,
                    description: Optional[str] = None) \
            -> bool:
        """
        Добавляет новую запись в таблицу History.

        :param user_id: Уникальный идентификатор пользователя.
        :param role_id: Уникальный идентификатор роли.
        :param tools_id: Уникальный идентификатор инструмента.
        :param datetime_value: Дата и время действия.
        :param status: Статус действия (опционально).
        :param description: Описание или комментарии (опционально).
        :param plan_id: Идентификатор чертежа (опционально).
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(
            id=id,
            datetime=datetime_value,
            Status=status,
            description=description,
            user_id=user_id,
            user_role_id=role_id,
            tools_id=tools_id
        )

    def get_history_by_id(self, history_id: int) -> Optional[History]:
        """
        Получает запись истории по её уникальному идентификатору.

        :param history_id: Уникальный идентификатор записи.
        :return: Объект History или None, если запись не найдена.
        """
        return self.get(history_id)

    def get_history_by_user(self, user_id: int) -> list[Type[History]]:
        """
        Возвращает список записей истории, связанных с указанным пользователем.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Список объектов History, связанных с пользователем.
        """
        return self.session.query(History).filter_by(user_id=user_id).all()

    def get_history_by_role(self, role_id: int) -> list[Type[History]]:
        """
        Возвращает список записей истории, связанных с указанной ролью.

        :param role_id: Уникальный идентификатор роли.
        :return: Список объектов History, связанных с ролью.
        """
        return self.session.query(History).filter_by(user_role_id=role_id).all()

    def get_history_by_tool(self, tools_id: int) -> list[Type[History]]:
        """
        Возвращает список записей истории, связанных с указанным инструментом.

        :param tools_id: Уникальный идентификатор инструмента.
        :return: Список объектов History, связанных с инструментом.
        """
        return self.session.query(History).filter_by(tools_id=tools_id).all()

    # def get_history_by_plan(self, plan_id: int) -> list[Type[History]]:
    #     """
    #     Возвращает список записей истории, связанных с указанным чертежом.
    #
    #     :param plan_id: Уникальный идентификатор чертежа.
    #     :return: Список объектов History, связанных с чертежом.
    #     """
    #     return self.session.query(History).filter_by(Plan_id=plan_id).all()

    def get_all_history(self) -> List[History]:
        """
        Возвращает список всех записей истории.

        :return: Список всех записей в таблице History.
        """
        return self.all()

    def update_history(self, history_id: int, **kwargs) -> bool:
        """
        Обновляет запись истории по её уникальному идентификатору.

        :param history_id: Уникальный идентификатор записи.
        :param kwargs: Поля и значения для обновления записи.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(history_id, **kwargs)

    def delete_history(self, history_id: int) -> bool:
        """
        Удаляет запись истории по её уникальному идентификатору.

        :param history_id: Уникальный идентификатор записи.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(history_id)

    def get_history_with_relations(self) -> list[Type[History]]:
        """
        Возвращает список записей истории со всеми связанными объектами (пользователи, роли, инструменты, чертежи).

        :return: Список объектов History с загруженными связями.
        """
        return self.session.query(History).options(
            joinedload(History.users),
            joinedload(History.role),
            joinedload(History.tools),
            joinedload(History.plans)
        ).all()

    def get_history_by_status(self, status: int) -> list[Type[History]]:
        """
        Возвращает список записей истории с указанным статусом.

        :param status: Статус действия в истории.
        :return: Список объектов History с заданным статусом.
        """
        return self.session.query(History).filter_by(Status=status).all()

    def get_all_ids(self) -> List[int]:
        """
        Возвращает список всех значений поля id из таблицы.

        :return: Список идентификаторов (id).
        """
        return [record.id for record in self.session.query(self.model.id).all()]
