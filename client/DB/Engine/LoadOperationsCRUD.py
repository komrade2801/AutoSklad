import datetime
import traceback
from typing import List, Optional, Type

from Core.app_logging import get_logger
from sqlalchemy import create_engine, select

logger = get_logger(__name__)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from ..Data.base import Base
from .BaseCRUD import BaseCRUD  # Импортируем ваш класс BaseCRUD
from ..Models.LoadOperations import LoadOperations  # Импортируем модель LoadOperations
from ..Models.Load import Load  # Импорт модели Load

from typing import Optional, List, Type
from sqlalchemy.orm import Session
from datetime import datetime
# from LoadOperations import LoadOperations


class EngineLoadOperations(BaseCRUD):
    """
    Класс EngineLoadOperations инкапсулирует логику работы с таблицей LoadOperations,
    предоставляя удобный интерфейс для операций CRUD и дополнительных операций.
    Наследуется от BaseCRUD, добавляя методы, специфичные для LoadOperations.
    """

    def __init__(self, session: Session):
        """
        Инициализация EngineLoadOperations.

        :param session: Объект сессии SQLAlchemy.
        """
        super().__init__(session, LoadOperations)

    def add_operation(
        self,
        id: int,
        date: datetime,
        load_id: int,
        load_tools_id: int,
        status_id: int,
        history_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Добавляет новую запись в таблицу LoadOperations.

        :param id:
        :param date:
        :param load_id: Идентификатор загрузки.
        :param load_tools_id: Идентификатор инструмента.
        :param status_id: Идентификатор статуса.
        :param history_id: Идентификатор истории.
        :param description: Описание операции.
        :return: True, если операция выполнена успешно, иначе False.
        """
        return self.add(
            id=id,
            date=date,
            load_id=load_id,
            load_tools_id=load_tools_id,
            status_id=status_id,
            history_id=history_id,
            description=description
        )

    def find_by_status(self, status_id: int) -> List[LoadOperations]:
        """
        Находит операции загрузки с указанным статусом.

        :param status_id: Идентификатор статуса.
        :return: Список объектов LoadOperations с данным статусом.
        """
        return self.session.query(LoadOperations).filter_by(status_id=status_id).all()

    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[LoadOperations]:
        """
        Находит операции загрузки в указанном диапазоне дат.

        :param start_date: Начальная дата.
        :param end_date: Конечная дата.
        :return: Список объектов LoadOperations в данном диапазоне.
        """
        return self.session.query(LoadOperations).filter(LoadOperations.date.between(start_date, end_date)).all()


    def get_operations_by_load_id(self, load_id: int) -> List[LoadOperations]:
        """
        Получает список операций Drop с указанным load_id.

        :param load_id: Значение поля load_id.
        :return: Список экземпляров LoadOperations с указанным load_id.
        """

        query = select(LoadOperations).where(LoadOperations.load_id == load_id)
        result = self.session.execute(query).scalars().all()
        return result
        # try:except Exception as e:
        #     print(f"Ошибка при получении операций с drop_id={load_id}: {e}")
        #     return []

    def get_operations_by_history_id(self, history_id: int) -> List[LoadOperations]:
        """
        Возвращает все записи в таблице LoadOperations, относящиеся к указанной записи в таблице history.

        :param history_id: Идентификатор записи в таблице history.
        :return: Список объектов LoadOperations, связанных с указанным history_id.
        """
        try:
            query = select(LoadOperations).where(LoadOperations.history_id == history_id)
            result = self.session.execute(query).scalars().all()
            return result
        except Exception as e:
            logger.exception("LoadOperationsCRUD get_operations_by_history_id history_id=%s: %s", history_id, e)
            return []

    def get_operations_by_tool(self, tool_id):
        """
        Возвращает все записи в таблице LoadOperations, относящиеся к указанной записи в таблице history.

        :param tool_id: Идентификатор записи в таблице LoadOperations.
        :return: Список объектов LoadOperations, связанных с указанным tool_id.
        """
        try:
            query = select(LoadOperations).where(LoadOperations.load_tools_id == tool_id)
            result = self.session.execute(query).scalars().all()
            return result
        except Exception as e:
            logger.exception("LoadOperationsCRUD get_operations_by_tool tool_id=%s: %s", tool_id, e)
            return []
