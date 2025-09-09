from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class OperationsConsumptionHasDevice(Base, Model):
    __tablename__ = "OperationsConsumptionHasDevice"

    operations_consumption_id = Column(Integer, ForeignKey("OperationsConsumption.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def operations_consumption(self):
        if "OperationsConsumption" not in Base.metadata.tables:
            from DB.Models.OperationsConsumption import OperationsConsumption
        else:
            OperationsConsumption = Base.metadata.tables["OperationsConsumption"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(OperationsConsumption, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="OperationsConsumption")

    def __repr__(self):
        """Представляет объект OperationsConsumption в виде строки для удобства отладки."""
        return (f"<OperationsConsumptionHasDevice("
                f"operations_consumption_id={self.operations_consumption_id}, "
                f"device_id={self.device_id}"
                f")>")