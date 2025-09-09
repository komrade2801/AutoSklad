from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.ErrorHasDevice import ErrorHasDevice


class EngineErrorHasDevice(BaseCRUD):
    """
    Класс EngineErrorHasDevice предоставляет интерфейс для работы с таблицей Error_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками ошибок к устройствам.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация класса EngineErrorHasDevice.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=ErrorHasDevice)

    def add_link(self, error_id: int, device_id: int) -> bool:
        """
        Добавляет связь между ошибкой и устройством.
        :param error_id: ID ошибки.
        :param device_id: ID устройства.
        :return: True, если запись успешно добавлена, иначе False.
        """
        existing = (
            self.session
            .query(self.model)
            .filter_by(error_id=error_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(error_id=error_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, error_id: int, device_id: int):
        """
        Получает связь между конкретной ошибкой и устройством.
        :param error_id: ID ошибки.
        :param device_id: ID устройства.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(error_id=error_id, device_id=device_id).first()

    def get_all_links(self):
        """
        Получает все связи ошибок с устройствами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def delete_link(self, error_id: int, device_id: int):
        """
        Удаляет связь между ошибкой и устройством.
        :param error_id: ID ошибки.
        :param device_id: ID устройства.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(error_id=error_id, device_id=device_id).delete()

    def check_link(self, error_id: int, device_id: int) -> bool:
        """
        Проверяет, существует ли связь между указанной ошибкой и устройством.
        :param error_id: ID ошибки.
        :param device_id: ID устройства.
        :return: True, если связь существует, иначе False.
        """
        return self.get_link(error_id=error_id, device_id=device_id) is not None

    def unlink_error_from_device(self, error_id: int, device_id: int):
        """
        Удаляет связь между ошибкой и устройством.
        :param error_id: ID ошибки.
        :param device_id: ID устройства.
        :return: True, если связь успешно удалена, иначе False.
        """
        return self.delete_link(error_id=error_id, device_id=device_id)

    def get_error_ids_by_device(self, device_id: int) -> list:
        """
        Возвращает список ID ошибок, связанных с указанным устройством.
        :param device_id: ID устройства.
        :return: Список ID ошибок.
        """
        links = self.session.query(self.model).filter_by(device_id=device_id).all()
        return [link.error_id for link in links]

    def link_error_to_device(self, id, id1):
        pass
