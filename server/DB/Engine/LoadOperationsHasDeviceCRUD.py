from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.LoadOperationsHasDevice import LoadOperationsHasDevice


class EngineLoadOperationsHasDevice(BaseCRUD):
    """
    Класс EngineLoadOperationsHasDevice предоставляет интерфейс для работы с таблицей loadOperations_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками операций загрузки к устройствам.
    """

    def __init__(self, session: Session = None):
        """        Инициализация класса EngineLoadOperationsHasDevice.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=LoadOperationsHasDevice)

    def add_link(self,
                 load_operations_id: int,
                 device_id: int
                 ) -> bool:
        """
        Добавляет связь между операцией загрузки и устройством.
        :param load_operations_id: ID операции загрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно добавлена, иначе False.
        """
        existing = (
            self.session
            .query(self.model)
            .filter_by(load_operations_id=load_operations_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(load_operations_id=load_operations_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, load_operations_id: int, device_id: int):
        """
        Получает связь между конкретной операцией загрузки и устройством.
        :param load_operations_id: ID операции загрузки.
        :param device_id: ID устройства.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(load_operations_id=load_operations_id, device_id=device_id).first()

    def get_all_links(self):
        """
        Получает все связи операций загрузки с устройствами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def delete_link(self, load_operations_id: int, device_id: int):
        """
        Удаляет связь между операцией загрузки и устройством.
        :param load_operations_id: ID операции загрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(load_operations_id=load_operations_id, device_id=device_id).delete()

    def get_by_device(self, device_id):
        pass
