from sqlalchemy import Column, Integer, String, Date, ForeignKey, Index
from sqlalchemy.orm import relationship

from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Command(Base, Model):
    __tablename__ = "Command"
    __table_kwargs__ = {"extend_existing": True}  # Аргументы таблицы, как в модели Cell

    # Поля таблицы
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("Device.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("Type.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=False)
    name = Column(String(45), nullable=True)
    create = Column(Date, nullable=True)

    # Индексы
    __table_args__ = (
        Index("fk_Command_Device1_idx", "device_id"),
        Index("fk_Command_Status1_idx", "status_id"),
        Index("fk_Command_Type1_idx", "type_id"),
        Index("fk_Command_User1_idx", "user_id"),
    )

    @property
    def Status_(self):
        if "Status" not in Base.metadata.tables:
            from DB.Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_
        # Каждый вызов возвращает новый объект relationship, поэтому
        # его следует использовать только для отложенного определения
        return relationship(Status, back_populates="Command")

    @property
    def device_rel(self):
        if "Device" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Device"].class_
        return relationship(Device, back_populates="Command")

    @property
    def type_rel(self):
        if "Type" not in Base.metadata.tables:
            from DB.Models.Type import Type
        else:
            Type = Base.metadata.tables["Type"].class_
        return relationship(Type, back_populates="Command")

    @property
    def user_rel(self):
        if "User" not in Base.metadata.tables:
            from DB.Models.User import User
        else:
            User = Base.metadata.tables["User"].class_
        return relationship(User, back_populates="Command")

    def __repr__(self):
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"device_id={self.device_id}, "
                f"type_id={self.type_id}, "
                f"status_id={self.status_id}"
                f"name={self.name}, "
                f"create={self.create}, "
                f")>")
