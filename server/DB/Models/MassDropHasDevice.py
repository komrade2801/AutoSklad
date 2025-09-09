from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class MassDropHasDevice(Base, Model):
    __tablename__ = "MassDropHasDevice"

    mass_drop_id = Column(Integer, ForeignKey("MassDrop.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def mass_drops(self):
        if "MassDrops" not in Base.metadata.tables:
            from DB.Models.MassDrop import MassDrop
        else:
            MassDrop = Base.metadata.tables["MassDrops"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(MassDrop, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="MassDrops")


    def __repr__(self):
        """Представляет объект LoadOperations в виде строки для удобства отладки."""
        return (f"<MassDropHasDevice("
                f"mass_drop_id={self.mass_drop_id}, "
                f"device_id={self.device_id}"
                f")>")
