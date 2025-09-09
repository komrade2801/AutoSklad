from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.ActualNormHasDevice import ActualNormHasDevice


class EngineActualNormHasDevice(BaseCRUD):
    """
    Класс EngineQuotaHasDevice предоставляет интерфейс для работы с таблицей Quota_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками квот к устройствам.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация класса EngineQuotaHasDevice.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=ActualNormHasDevice)

    def add_link(self, actual_norm_id: int, device_id: int) -> bool:
        """
        Добавляет связь между квотой и устройством.
        :param actual_norm_id: ID квоты.
        :param device_id: ID устройства.
        :return: True, если запись успешно добавлена, иначе False.
        """
        existing = (
            self.session
            .query(self.model)
            .filter_by(actual_norm_id=actual_norm_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(actual_norm_id=actual_norm_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, actual_norm_id: int, device_id: int):
        """
        Получает связь между конкретной квотой и устройством.
        :param actual_norm_id: ID квоты.
        :param device_id: ID устройства.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(Quota_id=actual_norm_id, device_id=device_id).first()

    def get_all_links(self):
        """
        Получает все связи квот с устройствами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def delete_link(self, actual_norm_id: int, device_id: int):
        """
        Удаляет связь между квотой и устройством.
        :param actual_norm_id: ID квоты.
        :param device_id: ID устройства.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(Quota_id=actual_norm_id, device_id=device_id).delete()
