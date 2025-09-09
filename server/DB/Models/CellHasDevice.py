from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class CellHasDevice(Base, Model):
    __tablename__ = "CellHasDevice"

    cell_id = Column(Integer, ForeignKey("Cell.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def cells(self):
        # from DB.Models.CellHasDevice import CellHasDevice
        return relationship(CellHasDevice, back_populates="Device")

    @property
    def devices(self):
        # from DB.Models.CellHasDevice import CellHasDevice
        return relationship(CellHasDevice, back_populates="Cell")

    def __repr__(self):
        """Представляет объект Cell в виде строки для удобства отладки."""
        return (f"<CellHasDevice("
                f"cell_id={self.cell_id}, "
                f"device_id={self.device_id}"
                f")>")