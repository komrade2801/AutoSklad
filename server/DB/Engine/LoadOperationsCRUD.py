from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List

from Core.app_logging import get_logger
from .CRUD import BaseCRUD  # Предполагается, что BaseCRUD уже реализован

logger = get_logger(__name__)
from ..Models.LoadOperations import LoadOperations  # Импорт модели LoadOperations


class EngineLoadOperations(BaseCRUD):
    """
    Класс EngineLoadOperations инкапсулирует логику работы с таблицей LoadOperations,
    предоставляя удобный интерфейс для операций CRUD и дополнительных операций.
    Наследуется от BaseCRUD, добавляя методы, специфичные для LoadOperations.
    """

    def __init__(self, session: Session=None):        
        """        Инициализация EngineLoadOperations.

        :param session: Объект сессии SQLAlchemy.
        """
                
        super().__init__(session=session, model=LoadOperations)

    def add_operation(
        self,
        operation_id: int,
        date: datetime,
        load_id: int,
        load_tools_id: int,
        status_id: int,
        history_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Добавляет новую запись в таблицу LoadOperations.

        :param operation_id: Уникальный идентификатор операции.
        :param date: Дата операции.
        :param load_id: Идентификатор загрузки.
        :param load_tools_id: Идентификатор инструмента.
        :param status_id: Идентификатор статуса.
        :param history_id: Идентификатор истории (опционально).
        :param description: Описание операции (опционально).
        :return: True, если операция выполнена успешно, иначе False.
        """
        return self.add(
            index=operation_id,
            date=date,
            load_id=load_id,
            load_tools_id=load_tools_id,
            status_id=status_id,
            history_id=history_id,
            description=description
        )

    def find_by_status(self, status_id: int):
        """
        Находит операции загрузки с указанным статусом.

        :param status_id: Идентификатор статуса.
        :return: Список объектов LoadOperations с данным статусом.
        """
        return self.session.query(LoadOperations).filter_by(status_id=status_id).all()

    def find_by_date_range(self, start_date: datetime, end_date: datetime):
        """
        Находит операции загрузки в указанном диапазоне дат.

        :param start_date: Начальная дата.
        :param end_date: Конечная дата.
        :return: Список объектов LoadOperations в данном диапазоне.
        """
        return self.session.query(LoadOperations).filter(LoadOperations.date.between(start_date, end_date)).all()

    def get_operations_by_load_id(self, load_id: int):
        """
        Получает список операций LoadOperations с указанным load_id.

        :param load_id: Значение поля load_id.
        :return: Список экземпляров LoadOperations с указанным load_id.
        """
        query = select(LoadOperations).where(LoadOperations.load_id == load_id)
        result = self.session.execute(query).scalars().all()
        return result

    def get_operations_by_history_id(self, history_id: int):
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

    def get_operations_by_tool(self, tool_id: int):
        """
        Возвращает все записи в таблице LoadOperations, относящиеся к указанному инструменту.

        :param tool_id: Идентификатор инструмента.
        :return: Список объектов LoadOperations, связанных с указанным tool_id.
        """
        try:
            query = select(LoadOperations).where(LoadOperations.load_tools_id == tool_id)
            result = self.session.execute(query).scalars().all()
            return result
        except Exception as e:
            logger.exception("LoadOperationsCRUD get_operations_by_tool tool_id=%s: %s", tool_id, e)
            return []

    def get_loads_by_tool_ids(self, tool_ids: List[int]):
        """
        Возвращает список операций LoadOperations, для которых поле load_tools_id входит в переданный список.

        :param tool_ids: Список идентификаторов инструментов.
        :return: Список объектов LoadOperations.
        """
        query = select(LoadOperations).where(LoadOperations.load_tools_id.in_(tool_ids))
        return self.session.execute(query).scalars().all()

    def create_load(self, load_data) -> Optional[LoadOperations]:
        """
        Создает новую запись в таблице LoadOperations на основе данных load_data.
        Ожидается, что load_data содержит необходимые атрибуты:
          - id, date, load_id, load_tools_id, status_id, (опционально) history_id, description.
        Если создание прошло успешно, возвращает созданную запись, иначе None.

        :param load_data: Объект с данными для создания записи.
        :return: Созданный объект LoadOperations или None.
        """
        if self.add(
            index=load_data.id,
            date=load_data.date,
            load_id=load_data.load_id,
            load_tools_id=load_data.load_tools_id,
            status_id=load_data.status_id,
            history_id=load_data.history_id,
            description=load_data.description
        ):
            return self.get(load_data.id)
        return None

    def get_load_by_id(self, load_id: int) -> Optional[LoadOperations]:
        """
        Получает запись из таблицы LoadOperations по её уникальному идентификатору.

        :param load_id: Уникальный идентификатор записи.
        :return: Объект LoadOperations или None, если запись не найдена.
        """
        return self.get(load_id)

    def update_load(self, load_id: int, load_data) -> Optional[LoadOperations]:
        """
        Обновляет запись в таблице LoadOperations по её уникальному идентификатору.
        :param load_id: Уникальный идентификатор записи.
        :param load_data: Словарь или объект с обновляемыми данными.
        :return: Обновленный объект LoadOperations или None, если обновление не удалось.
        """
        if self.update(index=load_id, **load_data):
            return self.get(index=load_id)
        return None

    def delete_load(self, load_id: int) -> bool:
        """
        Удаляет запись из таблицы LoadOperations по её уникальному идентификатору.

        :param load_id: Уникальный идентификатор записи.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(index=load_id)
