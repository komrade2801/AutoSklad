from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.MassDropHasDevice import MassDropHasDevice


class EngineMassDropHasDevice(BaseCRUD):
    """
    Класс EngineMassDropHasDevice предоставляет интерфейс для работы с таблицей mass_drop_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками массовых выгрузок к устройствам.
    """

    def __init__(self, session: Session = None):
        """        Инициализация класса EngineMassDropHasDevice.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=MassDropHasDevice)

    def add_link(self, mass_drop_id: int, device_id: int) -> bool:
        """
        Добавляет связь между массовой выгрузкой и устройством.
        :param mass_drop_id: ID массовой выгрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно добавлена, иначе False.
        """
        existing = (
            self.session
            .query(self.model)
            .filter_by(mass_drop_id=mass_drop_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(mass_drop_id=mass_drop_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, mass_drop_id: int, device_id: int):
        """
        Получает связь между конкретной массовой выгрузкой и устройством.
        :param mass_drop_id: ID массовой выгрузки.
        :param device_id: ID устройства.
        :return: Найденная запись или None.
        """
        return self.session.query(self.model).filter_by(mass_drop_id=mass_drop_id, device_id=device_id).first()

    def get_all_links(self):
        """
        Получает все связи массовых выгрузок с устройствами.
        :return: Список всех записей в таблице.
        """
        return self.all()

    def delete_link(self, mass_drop_id: int, device_id: int):
        """
        Удаляет связь между массовой выгрузкой и устройством.
        :param mass_drop_id: ID массовой выгрузки.
        :param device_id: ID устройства.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.session.query(self.model).filter_by(mass_drop_id=mass_drop_id, device_id=device_id).delete()
