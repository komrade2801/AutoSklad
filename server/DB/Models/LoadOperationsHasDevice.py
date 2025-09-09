from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class LoadOperationsHasDevice(Base, Model):
    __tablename__ = "LoadOperationsHasDevice"

    load_operations_id = Column(Integer, ForeignKey("LoadOperations.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def loads(self):
        if "Loads" not in Base.metadata.tables:
            from DB.Models.LoadOperations import LoadOperations
        else:
            LoadOperations = Base.metadata.tables["Loads"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(LoadOperations, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="Loads")

    def __repr__(self):
        """Представляет объект LoadOperations в виде строки для удобства отладки."""
        return (f"<LoadOperationsHasDevice("
                f"load_operations_id={self.load_operations_id}, "
                f"device_id={self.device_id}"
                f")>")
