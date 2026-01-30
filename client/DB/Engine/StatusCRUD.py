import datetime
import traceback

from Core.app_logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)
from sqlalchemy.exc import NoResultFound, IntegrityError, SQLAlchemyError
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DB.Data.base import Base
from DB.Engine.BaseCRUD import BaseCRUD
from DB.Models.Status import Status


class EngineStatus(BaseCRUD):
    """
    Класс EngineStatus предоставляет удобные методы для работы с таблицей Status,
    инкапсулируя логику CRUD-операций через использование класса BaseCRUD.

    Методы класса:
    - count(): Получение количества статусов.
    - add(**kwargs): Добавление нового статуса.
    - all(): Получение списка всех статусов.
    - get(index): Получение статуса по уникальному идентификатору.
    - update(index, **kwargs): Обновление статуса по уникальному идентификатору.
    - delete(index): Удаление статуса по уникальному идентификатору.
    - drop(): Удаление таблицы Status из базы данных.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineStatus.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
        # Передаем сессию и модель Status в конструктор BaseCRUD
        super().__init__(session, Status)

    def add(self, index: int, stype: str, description: Optional[str] = None, created_at: Optional[datetime] = None) -> bool:
        """
        Добавляет новый статус в таблицу.

        :param index: Уникальный идентификатор статуса
        :param stype: Тип статуса (например, 'Active', 'Inactive').
        :param description: Описание статуса.
        :return: True если статус успешно добавлен, иначе False.
        """
        # Используем параметры для создания записи
        try:
            return super().add(id=index, stype=stype, description=description, created_at=created_at)
        except Exception as e:
            logger.exception("StatusCRUD.add: %s", e)
            return False


    def get_status_by_id(self, status_id: int) -> Optional[Status]:
        """
        Получает операцию Drop по её ID.

        :param status_id: Уникальный идентификатор операции.
        :return: Экземпляр DropOperations или None, если операция не найдена.
        """
        return self.get(index=status_id)


    def all(self) -> List[Status]:
        """Возвращает список всех статусов."""
        return super().all()

    def get(self, index: int) -> Optional[Status]:
        """
        Получает статус по уникальному идентификатору.

        :param index: Уникальный идентификатор статуса.
        :return: Статус или None если не найден.
        """
        return super().get(index)

    def update(self, index: int, stype: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        Обновляет существующий статус по уникальному идентификатору.

        :param index: Уникальный идентификатор статуса для обновления.
        :param stype: Новый тип статуса (если изменяется).
        :param description: Новое описание статуса (если изменяется).
        :return: True если статус успешно обновлен, иначе False.
        """
        return super().update(index=index, stype=stype, description=description)

    def delete(self, index: int) -> bool:
        """
        Удаляет статус по уникальному идентификатору.

        :param index: Уникальный идентификатор статуса для удаления.
        :return: True если статус успешно удален, иначе False.
        """
        return super().delete(index)

    def drop(self) -> bool:
        """
        Удаляет таблицу Status из базы данных.

        :return: True если таблица успешно удалена, иначе False.
        """
        return super().drop()

    def find_by_name(self, stype: str) -> Optional[Status]:
        """
        Ищет статус по его названию (stype).

        :param stype: Название статуса для поиска.
        :return: Объект Status, если найден, иначе None.
        """

        result = self.session.query(Status).filter_by(stype=stype).first()
        return result

