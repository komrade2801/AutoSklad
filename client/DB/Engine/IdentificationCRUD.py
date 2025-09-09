from sqlalchemy.orm import Session
from typing import Optional, List
from ..Engine.BaseCRUD import BaseCRUD  # Предполагается, что BaseCRUD уже реализован
from ..Models.Identification import Identification  # Импорт модели Identification


class EngineIdentification(BaseCRUD):
    """
    Класс EngineIdentification предоставляет интерфейс для работы с таблицей Identification.
    Инкапсулирует логику CRUD операций и предоставляет методы для работы с идентификацией пользователей.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineIdentification.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, Identification)

    def add_identification(self, datetime, status: int, user_id: int, description: Optional[str] = None) -> bool:
        """
        Добавляет новую запись идентификации пользователя в таблицу Identification.

        :param datetime: Время идентификации.
        :param status: Статус идентификации.
        :param user_id: Идентификатор пользователя.
        :param description: Дополнительное описание или комментарий.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(datetime=datetime, Status=status, user_id=user_id, description=description)

    def get_identification_by_id(self, identification_id: int) -> Optional[Identification]:
        """
        Получает запись идентификации по уникальному идентификатору.

        :param identification_id: Уникальный идентификатор записи.
        :return: Объект Identification или None, если запись не найдена.
        """
        return self.get(identification_id)

    def get_identifications_by_user_id(self, user_id: int) -> List[Identification]:
        """
        Получает все записи идентификации для указанного пользователя.

        :param user_id: Идентификатор пользователя.
        :return: Список объектов Identification.
        """
        return self.session.query(self.model).filter_by(user_id=user_id).all()

    def get_identifications_by_status(self, status: int) -> List[Identification]:
        """
        Получает записи идентификации с указанным статусом.

        :param status: Статус идентификации.
        :return: Список объектов Identification.
        """
        return self.session.query(self.model).filter_by(Status=status).all()

    def get_identifications_by_datetime_range(self, start_datetime, end_datetime) -> List[Identification]:
        """
        Получает записи идентификации в указанном диапазоне времени.

        :param start_datetime: Начало диапазона.
        :param end_datetime: Конец диапазона.
        :return: Список объектов Identification.
        """
        return (self.session.query(self.model)
                .filter(self.model.datetime >= start_datetime, self.model.datetime <= end_datetime)
                .all())

    def update_identification_status(self, identification_id: int, status: int) -> bool:
        """
        Обновляет статус идентификации по её уникальному идентификатору.

        :param identification_id: Уникальный идентификатор идентификации.
        :param status: Новый статус идентификации.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(identification_id, Status=status)

    def update_identification_description(self, identification_id: int, description: str) -> bool:
        """
        Обновляет описание идентификации по её уникальному идентификатору.

        :param identification_id: Уникальный идентификатор идентификации.
        :param description: Новое описание или комментарий.
        :return: True, если запись успешно обновлена, иначе False.
        """
        return self.update(identification_id, description=description)

    def delete_identification(self, identification_id: int) -> bool:
        """
        Удаляет запись идентификации по её уникальному идентификатору.

        :param identification_id: Уникальный идентификатор записи.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(identification_id)

    def get_all_identifications(self) -> List[Identification]:
        """
        Возвращает список всех записей идентификации в таблице Identification.

        :return: Список всех записей идентификации.
        """
        return self.all()
