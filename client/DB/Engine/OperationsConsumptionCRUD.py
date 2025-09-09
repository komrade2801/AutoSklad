import datetime
import random
import traceback

from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import select

from DB.Data.base import Base
from .BaseCRUD import BaseCRUD  # Предположительно BaseCRUD находится в этом модуле
from ..Models.OperationsConsumption import OperationsConsumption  # Предположительно модель OperationsConsumption находится здесь


class EngineOperationsConsumption(BaseCRUD):
    """
    Класс EngineOperationsConsumption инкапсулирует всю логику работы с таблицей OperationsConsumption,
    предоставляя методы для удобной работы с записями в базе данных.
    Наследуется от BaseCRUD для использования стандартных операций CRUD.
    """

    def __init__(self, session: Session):
        """
        Инициализирует экземпляр класса EngineOperationsConsumption.

        :param session: Сессия SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, OperationsConsumption)

    def count_operations(self) -> int:
        """
        Получает количество операций.

        :return: Количество записей в таблице OperationsConsumption.
        """
        return self.count()  # Используем метод count() из BaseCRUD

    def add_operation(
            self,
            index: int,
            consumption_id: int,
            consumption_tools_id: int,
            status_id: int,
            history_id: int,
            description: Optional[str] = None,
    ) -> bool:
        """
        Добавляет новую операцию.

        :param index:
        :param consumption_id: Идентификатор расхода.
        :param consumption_tools_id: Идентификатор инструмента.
        :param status_id: Идентификатор статуса операции.
        :param history_id: Идентификатор истории.
        :param description: Описание операции (опционально).
        :return: True, если операция успешно добавлена, иначе False.
        """
        return self.add(
            id=index,
            date=datetime.datetime.now(),
            consumption_id=consumption_id,
            consumption_tools_id=consumption_tools_id,
            status_id=status_id,
            history_id=history_id,
            description=description,
        )

    def get_operation(self, operation_id: int) -> Optional[OperationsConsumption]:
        """
        Получает операцию по идентификатору.

        :param operation_id: Уникальный идентификатор операции.
        :return: Экземпляр OperationsConsumption или None, если не найдено.
        """
        return self.get(operation_id)  # Используем метод get() из BaseCRUD

    def get_all_operations(self) -> List[OperationsConsumption]:
        """
        Возвращает все операции.

        :return: Список всех записей OperationsConsumption.
        """
        return self.all()  # Используем метод all() из BaseCRUD

    def update_operation(
            self,
            operation_id: int,
            **kwargs
    ) -> bool:
        """
        Обновляет операцию по идентификатору.

        :param operation_id: Уникальный идентификатор операции.
        :param kwargs: Поля и значения для обновления.
        :return: True, если обновление успешно, иначе False.
        """
        return self.update(operation_id, **kwargs)  # Используем метод update() из BaseCRUD

    def delete_operation(self, operation_id: int) -> bool:
        """
        Удаляет операцию по идентификатору.

        :param operation_id: Уникальный идентификатор операции.
        :return: True, если операция успешно удалена, иначе False.
        """
        return self.delete(operation_id)  # Используем метод delete() из BaseCRUD

    def drop_operations_table(self) -> bool:
        """
        Удаляет таблицу OperationsConsumption из базы данных.

        :return: True, если таблица успешно удалена, иначе False.
        """
        return self.drop()  # Используем метод drop() из BaseCRUD


    def get_operations_by_history_id(self, history_id: int) -> List[OperationsConsumption]:
        """
        Возвращает все записи в таблице LoadOperations, относящиеся к указанной записи в таблице history.

        :param history_id: Идентификатор записи в таблице history.
        :return: Список объектов LoadOperations, связанных с указанным history_id.
        """
        try:
            query = select(OperationsConsumption).where(OperationsConsumption.history_id == history_id)
            result = self.session.execute(query).scalars().all()
            return result
        except Exception as e:
            print(f"Ошибка при извлечении операций с history_id={history_id}: {e}")
            print(traceback.format_exc())
            return []

    def get_operations_by_tool(self, tool_id):
        """
        Возвращает все записи в таблице LoadOperations, относящиеся к указанной записи в таблице history.

        :param tool_id: Идентификатор записи в таблице LoadOperations.
        :return: Список объектов LoadOperations, связанных с указанным tool_id.
        """
        try:
            query = select(OperationsConsumption).where(OperationsConsumption.consumption_tools_id == tool_id)
            result = self.session.execute(query).scalars().all()
            return result
        except Exception as e:
            print(f"Ошибка при извлечении операций с history_id={tool_id}: {e}")
            print(traceback.format_exc())
            return []
