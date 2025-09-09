from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class DropOperationsHasDevice(Base, Model):
    __tablename__ = "DropOperationsHasDevice"

    drop_operations_id = Column(Integer, ForeignKey("DropOperations.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def drops(self):
        if "Drops" not in Base.metadata.tables:
            from DB.Models.Drop import Drop
        else:
            Drop = Base.metadata.tables["Drops"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Drop, back_populates="DropOperations")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="DropOperations")

    def __repr__(self):
        """Представляет объект DropOperations в виде строки для удобства отладки."""
        return (f"<DropOperationsHasDevice("
                f"drop_operations_id={self.drop_operations_id}, "
                f"device_id={self.device_id}"
                f")>")
