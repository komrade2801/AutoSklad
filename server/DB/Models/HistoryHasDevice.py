from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class HistoryHasDevice(Base, Model):
    __tablename__ = "HistoryHasDevice"

    history_id = Column(Integer, ForeignKey("History.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def stories(self):
        if "History" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["History"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="HistoryHasDevice")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="HistoryHasDevice")

    def __repr__(self):
        """Представляет объект LoadOperations в виде строки для удобства отладки."""
        return (f"<HistoryHasDevice("
                f"history_id={self.history_id}, "
                f"device_id={self.device_id}"
                f")>")
