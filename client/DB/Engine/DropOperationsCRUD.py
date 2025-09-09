import traceback

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, IntegrityError
from typing import List, Optional
from contextlib import contextmanager
import datetime
from .BaseCRUD import BaseCRUD
from ..Models.DropOperations import DropOperations  # Импортируем модель DropOperations
from sqlalchemy import select


class EngineDropOperations(BaseCRUD):
    """
    Класс EngineDropOperations инкапсулирует логику работы с моделью DropOperations,
    наследует базовые операции CRUD из BaseCRUD и предоставляет дополнительные методы для работы с операциями Drop.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineDropOperations.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
        super().__init__(session, DropOperations)

    def count_operations(self) -> int:
        """
        Получает количество операций Drop в базе данных.

        :return: Количество операций.
        """
        return self.count()

    def add_operation(self,
                      index: int,
                      drop_id: int,
                      tools_id: int,
                      status_id: int,
                      history_id: Optional[int] = None,
                      description: Optional[str] = None) -> bool:
        """
        Добавляет новую операцию Drop.

        :param index:
        :param drop_id: Внешний ключ на Drop.
        :param tools_id: Внешний ключ на Tools.
        :param status_id: Внешний ключ на Status.
        :param history_id: Внешний ключ на History (опционально).
        :param description: Дополнительное описание операции.
        :return: True, если операция успешно добавлена.
        """
        return self.add(
            id=index,
            date=datetime.datetime.now(),
            description=description,
            history_id=history_id,
            status_id=status_id,
            tools_id=tools_id,
            drop_id=drop_id
        )

    def get_all_operations(self) -> List[DropOperations]:
        """
        Получает все операции Drop.

        :return: Список всех операций.
        """
        return self.all()

    def get_operation_by_id(self, operation_id: int) -> Optional[DropOperations]:
        """
        Получает операцию Drop по её ID.

        :param operation_id: Уникальный идентификатор операции.
        :return: Экземпляр DropOperations или None, если операция не найдена.
        """
        return self.get(operation_id)

    def update_operation(self, operation_id: int, **kwargs) -> bool:
        """
        Обновляет операцию Drop.

        :param operation_id: Уникальный идентификатор операции.
        :param kwargs: Поля и значения для обновления.
        :return: True, если обновление прошло успешно.
        """
        return self.update(operation_id, **kwargs)

    def delete_operation(self, operation_id: int) -> bool:
        """
        Удаляет операцию Drop по её ID.

        :param operation_id: Уникальный идентификатор операции.
        :return: True, если удаление прошло успешно.
        """
        return self.delete(operation_id)

    def drop_operations_table(self) -> bool:
        """
        Удаляет таблицу DropOperations из базы данных.

        :return: True, если таблица успешно удалена.
        """
        return self.drop()

    def get_operations_by_drop_id(self, drop_id: int) -> List[DropOperations]:
        """
        Получает список операций Drop с указанным drop_id.

        :param drop_id: Значение поля drop_id.
        :return: Список экземпляров DropOperations с указанным drop_id.
        """

        query = select(DropOperations).where(DropOperations.drop_id == drop_id)
        result = self.session.execute(query).scalars().all()
        return result
        # try:except Exception as e:
        #     print(f"Ошибка при получении операций с drop_id={drop_id}: {e}")
        #     return []

    def get_operations_by_history_id(self, history_id: int) -> List[DropOperations]:
        """
        Возвращает все записи в таблице LoadOperations, относящиеся к указанной записи в таблице history.

        :param history_id: Идентификатор записи в таблице history.
        :return: Список объектов LoadOperations, связанных с указанным history_id.
        """
        try:
            query = select(DropOperations).where(DropOperations.history_id == history_id)
            result = self.session.execute(query).scalars().all()
            return result
        except Exception as e:
            print(f"Ошибка при извлечении операций с history_id={history_id}: {e}")
            print(traceback.format_exc())
            return []

    def get_operations_by_tool(self, tool_id):
        """
        Получает список операций Drop с указанным drop_id.

        :param tool_id: Значение поля tool_id.
        :return: Список экземпляров DropOperations с указанным tool_id.
        """

        query = select(DropOperations).where(DropOperations.tools_id == tool_id)
        result = self.session.execute(query).scalars().all()
        return result
