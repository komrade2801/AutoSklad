from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class ErrorHasDevice(Base, Model):
    __tablename__ = "ErrorHasDevice"

    error_id = Column(Integer, ForeignKey("Error.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def errors(self):
        if "Errors" not in Base.metadata.tables:
            from DB.Models.Error import Error
        else:
            Error = Base.metadata.tables["Errors"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Error, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="Errors")

    def __repr__(self):
        """Представляет объект DropOperations в виде строки для удобства отладки."""
        return (f"<ErrorHasDevice("
                f"error_id={self.error_id}, "
                f"device_id={self.device_id}"
                f")>")