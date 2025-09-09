from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Device import Device


class EngineDevice(BaseCRUD):
    """
    Класс EngineDevice предоставляет интерфейс для работы с таблицей Device.
    Наследует BaseCRUD и использует его методы для стандартных операций,
    а также расширяет функционал методами, специфичными для устройств.
    """

    def __init__(self, session: Session=None):
        """
        Инициализирует EngineDevice.

        :param session: SQLAlchemy Session для работы с базой данных.
        """
                
        super().__init__(session=session, model=Device)

    def get_device_by_number(self, number: int) -> Optional[Device]:
        """
        Возвращает устройство по его уникальному полю number.

        :param number: Номер устройства.
        :return: Первый найденный объект Device или None.
        """
        devices = self.get_by_number(number)
        return devices[0] if devices else None

    def get_all_devices(self) -> List[Device]:
        """
        Возвращает список всех устройств.

        :return: Список объектов Device.
        """
        return self.all()

    def create_device(
            self,
            number: int,
            name: str,
            description: str,
            details: str,
            create: datetime.date
    ) -> Device:
        """
        Создает новое устройство и возвращает его.

        :param number: Номер устройства.
        :param name: Название устройства.
        :param description: Описание устройства.
        :param details: Дополнительные детали.
        :param create: Дата создания.
        :return: Созданный объект Device.
        """
        self.add_device(number, name, description, details, create)
        max_id = max(self.get_all_ids(), default=0)
        return self.get(max_id)

    def add_device(
            self,
            index:int,
            number: int,
            name: str,
            description: str,
            details: str,
            create: datetime.date
    ) -> bool:
        """
        Добавляет новое устройство без возврата объекта.

        :param number: Номер устройства.
        :param name: Название устройства.
        :param description: Описание устройства.
        :param details: Дополнительные детали.
        :param create: Дата создания.
        :return: True при успешном добавлении.
        """
        return self.add(
            index=index,
            number=number,
            name=name,
            description=description,
            details=details,
            create=create
        )

    def get_device_by_id(self, device_id: int) -> Optional[Device]:
        """
        Возвращает устройство по его первичному ключу.

        :param device_id: ID устройства.
        :return: Объект Device или None.
        """
        return self.get(device_id)

    def update_device(
            self,
            device_id: int,
            number: Optional[int] = None,
            name: Optional[str] = None,
            description: Optional[str] = None,
            details: Optional[str] = None,
            create: Optional[datetime.date] = None
    ) -> bool:
        """
        Обновляет атрибуты устройства.

        :param device_id: ID устройства.
        :param number: Новый номер (опционально).
        :param name: Новое название (опционально).
        :param description: Новое описание (опционально).
        :param details: Новые детали (опционально).
        :param create: Новая дата создания (опционально).
        :return: True при успешном обновлении.
        """
        return self.update(
            device_id,
            number=number,
            name=name,
            description=description,
            details=details,
            create=create
        )

    def delete_device(self, device_id: int) -> bool:
        """
        Удаляет устройство по его ID.

        :param device_id: ID удаляемого устройства.
        :return: True при успешном удалении.
        """
        return self.delete(index=device_id)


    def get_full_device(self, device_id: int) -> Optional[Device]:
        """
        Возвращает устройство с подгруженными всеми отношениями через Eager Loading.

        Модель Device должна содержать relationship() для всех перечисленных полей:
          errors, cells, mass_drops, mass_loads, tools,
          quota, operations_consumption, drop_operations,
          load_operations, commands.
        """
        return (
            self.session.query(self.model)
            .options(
                joinedload(Device.errors),
                joinedload(Device.cells),
                joinedload(Device.mass_drops),
                joinedload(Device.mass_loads),
                joinedload(Device.tools),
                joinedload(Device.quota),
                joinedload(Device.operations_consumption),
                joinedload(Device.drop_operations),
                joinedload(Device.load_operations),
                joinedload(Device.commands),
            )
            .filter(Device.id == device_id)
            .one_or_none()
        )

    async def validate_device(self, device_id: int, status=None):
        device = await self.session.get(Device, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        return device

