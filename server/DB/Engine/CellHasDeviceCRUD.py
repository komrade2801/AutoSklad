from typing import List, Optional
from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.CellHasDevice import CellHasDevice


class EngineCellHasDevice(BaseCRUD):
    """
    Класс EngineCellHasDevice предоставляет интерфейс для работы с таблицей Cell_has_Device.
    Инкапсулирует CRUD-операции и обеспечивает удобные методы для работы с привязками ячеек к устройствам.
    """

    def __init__(self, session: Session = None):
        """
        Инициализация класса EngineCellHasDevice.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """

        super().__init__(session=session, model=CellHasDevice)

    def add_link(self,
                 cell_id: int,
                 device_id: int
                 ) -> bool:
        # сначала проверяем, есть ли уже такая связь
        existing = (
            self.session
            .query(self.model)
            .filter_by(cell_id=cell_id, device_id=device_id)
            .one_or_none()
        )
        if existing:
            return True

        instance = self.model(cell_id=cell_id, device_id=device_id)
        try:
            with self.transaction() as db:
                db.add(instance)
            self._cache.clear()
            return True
        except RuntimeError as e:
            if "UNIQUE constraint failed" in str(e):
                return True
            raise

    def get_link(self, cell_id: int, device_id: int) -> Optional[CellHasDevice]:
        return self.session.query(self.model).filter_by(cell_id=cell_id, device_id=device_id).first()

    def get_all_links(self) -> List[CellHasDevice]:
        return self.all()

    def delete_link(self, cell_id: int, device_id: int) -> bool:
        result = self.session.query(self.model).filter_by(cell_id=cell_id, device_id=device_id).delete()
        self.session.commit()
        return result > 0

    def get_cells_by_device_id(self, device_id: int) -> List[int]:
        """Возвращает список ID ячеек, связанных с устройством"""
        links = self.session.query(self.model.cell_id).filter_by(device_id=device_id).all()
        return [link.cell_id for link in links]

    def link_cell_to_device(self, cell_id: int, device_id: int) -> bool:
        """Альтернативный метод добавления связи с проверкой существования"""
        if self.get_link(cell_id, device_id):
            return False  # Связь уже существует
        return self.add_link(cell_id=cell_id, device_id=device_id)

    def check_cell_belongs_to_device(self, cell_id: int, device_id: int) -> bool:
        """Проверяет существование связи между ячейкой и устройством"""
        return self.get_link(cell_id=cell_id, device_id=device_id) is not None

    def unlink_cell_from_device(self, cell_id: int, device_id: int) -> bool:
        """Безопасное удаление связи с проверкой существования"""
        if not self.check_cell_belongs_to_device(cell_id, device_id):
            return False
        return self.delete_link(cell_id=cell_id, device_id=device_id)
