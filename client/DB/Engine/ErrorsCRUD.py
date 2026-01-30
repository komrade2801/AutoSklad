import traceback

from Core.app_logging import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)
from typing import Optional, List
from DB.Engine.BaseCRUD import BaseCRUD  # Импортируем BaseCRUD
from DB.Models.Error import Error  # Импортируем модель Error
import datetime


class EngineError(BaseCRUD):
    """
    Класс EngineError предоставляет удобный интерфейс для работы с таблицей Error в базе данных
    Он инкапсулирует логику CRUD операций и предоставляет дополнительные методы, специфичные для ошибок
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineError

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных
        """
        super().__init__(session, Error)

    def add_error(self, error_type, message) -> bool:
        """
        Добавляет новую запись об ошибке в таблицу Error.

        :param error_type: Тип ошибки (например, Timeout, Device Error и др.).
        :param message: Сообщение, объясняющее ошибку.
        :return: True если запись об ошибке успешно добавлена, иначе False.
        """

        _id = self.count() + 1
        _error_type = error_type
        _message = message
        _timestamp = datetime.datetime.utcnow()
        new_error = Error(id=_id, error_type=_error_type, message=_message, timestamp=_timestamp)
        self.session.add(new_error)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.exception("ErrorsCRUD add_error")
            raise
        return True
        # try:except Exception as e:
        #     # self.session.rollback()
        #     print(f"Error adding new error: {e}")
        #     return False

    def get_error_by_id(self, error_id: int) -> Optional[Error]:
        """
        Получает запись об ошибке по уникальному идентификатору.

        :param error_id: Уникальный идентификатор ошибки.
        :return: Объект Error или None, если ошибка не найдена.
        """
        return self.get(error_id)

    def get_errors_by_type(self, error_type: str) -> List[Error]:
        """
        Возвращает все записи об ошибках с заданным типом.

        :param error_type: Тип ошибки.
        :return: Список объектов Error с указанным типом ошибки.
        """
        try:
            return self.session.query(self.model).filter_by(error_type=error_type).all()
        except Exception as e:
            logger.exception("ErrorsCRUD get_errors_by_type: %s", e)
            return []

    def get_recent_errors(self, limit: int = 10) -> List[Error]:
        """
        Возвращает список последних ошибок, отсортированных по времени их возникновения.

        :param limit: Максимальное количество записей об ошибках для возврата (по умолчанию 10).
        :return: Список последних ошибок.
        """
        try:
            return self.session.query(self.model).order_by(Error.timestamp.desc()).limit(limit).all()
        except Exception as e:
            logger.exception("ErrorsCRUD get_recent_errors: %s", e)
            return []

    def delete_error(self, error_id: int) -> bool:
        """
        Удаляет запись об ошибке по уникальному идентификатору.

        :param error_id: Уникальный идентификатор ошибки.
        :return: True если запись об ошибке успешно удалена, иначе False.
        """

        return self.delete(error_id)
        # try:except Exception as e:
        #     print(f"Error deleting error with id {error_id}: {e}")
        #     return False

    def get_all_errors(self) -> List[Error]:
        """
        Возвращает список всех записей об ошибках в таблице Error.

        :return: Список всех ошибок.
        """

        return self.all()
        # try:except Exception as e:
        #     print(f"Error retrieving all errors: {e}")
        #     return []
