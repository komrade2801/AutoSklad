from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.DropOperationsHasDevice import DropOperationsHasDevice


class EngineDropOperationsHasDevice(BaseCRUD):
    """
    Класс EngineDropOperationsHasDevice предоставляет интерфейс для работы с таблицей dropOperations_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками операций выгрузки к устройствам.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация класса EngineDropOperationsHasDevice.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=DropOperationsHasDevice)

    def add_link(self, drop_operations_id: int, device_id: int) -> bool:
        """
        Добавляет связь между операцией выгрузки и устройством.
        :param drop_operations_id: ID операции выгрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно добавлена, иначе False.
        """
        existing = (
            self.session
            .query(self.model)
            .filter_by(drop_operations_id=drop_operations_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(drop_operations_id=drop_operations_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, drop_operations_id: int, device_id: int):
        """
        Получает связь между конкретной операцией выгрузки и устройством.
        :param drop_operations_id: ID операции выгрузки.
        :param device_id: ID устройства.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(drop_operations_id=drop_operations_id, device_id=device_id).first()

    def get_all_links(self):
        """
        Получает все связи операций выгрузки с устройствами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def delete_link(self, drop_operations_id: int, device_id: int):
        """
        Удаляет связь между операцией выгрузки и устройством.
        :param drop_operations_id: ID операции выгрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(drop_operations_id=drop_operations_id, device_id=device_id).delete()
