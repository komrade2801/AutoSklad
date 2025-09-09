from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class MassLoadHasDevice(Base, Model):
    __tablename__ = "MassLoadHasDevice"

    mass_load_id = Column(Integer, ForeignKey("MassLoad.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def mass_loads(self):
        if "MassLoads" not in Base.metadata.tables:
            from DB.Models.MassLoad import MassLoad
        else:
            MassLoad = Base.metadata.tables["MassLoads"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(MassLoad, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="MassLoads")

    def __repr__(self):
        """Представляет объект MassLoad в виде строки для удобства отладки."""
        return (f"<MassLoadHasDevice("
                f"mass_load_id={self.mass_load_id}, "
                f"device_id={self.device_id}"
                f")>")
