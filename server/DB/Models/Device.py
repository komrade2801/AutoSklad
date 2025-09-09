from sqlalchemy import Column, Date, Integer, String, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Device(Base, Model):
    """Модель для хранения информации об устройствах"""
    __tablename__ = "Device"
    __table_args__ = (
        Index("number_UNIQUE", "number", unique=True),
        {"extend_existing": True}
    )

    # Основные поля
    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, comment="Уникальный номер устройства")
    name = Column(String(45), comment="Название устройства")
    description = Column(String(150), comment="Краткое описание")
    details = Column(String(450), comment="Подробная информация")
    create = Column(Date, comment="Дата создания записи")

    @property
    def cells(self):
        from DB.Models.CellHasDevice import CellHasDevice
        return relationship(CellHasDevice, back_populates="Device")

    @property
    def drops(self):
        if "Drops" not in Base.metadata.tables:
            from DB.Models.Drop import Drop
        else:
            Drop = Base.metadata.tables["Drops"].class_
        return relationship(Drop, back_populates="Devices")

    @property
    def errors(self):
        if "Error" not in Base.metadata.tables:
            pass
        return relationship("Error", secondary="ErrorHasDevice", back_populates="Devices")

    @property
    def mass_drops(self):
        if "MassDrop" not in Base.metadata.tables:
            pass
        return relationship("MassDrop", secondary="MassDropHasDevice", back_populates="Devices")

    @property
    def mass_loads(self):
        if "MassLoad" not in Base.metadata.tables:
            pass
        return relationship("MassLoad", secondary="MassLoadHasDevice", back_populates="Devices")

    def __repr__(self):
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"number={self.number}, "
                f"name={self.name}, "
                f"description={self.description}"
                f"details={self.details}"
                f"create={self.create}"
                f")>")
