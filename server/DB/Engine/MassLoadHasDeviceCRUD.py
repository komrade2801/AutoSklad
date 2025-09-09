from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.MassLoadHasDevice import MassLoadHasDevice


class EngineMassLoadHasDevice(BaseCRUD):
    """
    Класс EngineMassLoadHasDevice предоставляет интерфейс для работы с таблицей mass_load_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками массовых загрузок к устройствам.
    """

    def __init__(self, session: Session = None):
        """        Инициализация класса EngineMassLoadHasDevice.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=MassLoadHasDevice)

    def add_link(self, mass_load_id: int, device_id: int) -> bool:
        """
        Добавляет связь между массовой загрузкой и устройством.
        :param mass_load_id: ID массовой загрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно добавлена, иначе False.
        """
        existing = (
            self.session
            .query(self.model)
            .filter_by(mass_load_id=mass_load_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(mass_load_id=mass_load_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, mass_load_id: int, device_id: int):
        """
        Получает связь между конкретной массовой загрузкой и устройством.
        :param mass_load_id: ID массовой загрузки.
        :param device_id: ID устройства.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(mass_load_id=mass_load_id, device_id=device_id).first()

    def get_all_links(self):
        """
        Получает все связи массовых загрузок с устройствами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def delete_link(self, mass_load_id: int, device_id: int):
        """
        Удаляет связь между массовой загрузкой и устройством.
        :param mass_load_id: ID массовой загрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(mass_load_id=mass_load_id, device_id=device_id).delete()
