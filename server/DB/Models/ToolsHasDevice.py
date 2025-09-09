from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class ToolsHasDevice(Base, Model):
    __tablename__ = "ToolsHasDevice"

    tools_id = Column(Integer, ForeignKey("Tools.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def tools(self):
        if "Tools" not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables["Tools"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="Tools")

    def __repr__(self):
        """Представляет объект Status в виде строки для удобства отладки."""
        return (f"<ToolsHasDevice("
                f"tools_id={self.tools_id}, "
                f"device_id={self.device_id}"
                f")>")
