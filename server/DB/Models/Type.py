from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Type(Base, Model):
    __tablename__ = "Type"

    # Поля таблицы
    id = Column(Integer, primary_key=True, comment="Уникальный идентификатор типа")
    name = Column(String(50), nullable=True, comment="Название типа")
    operation = Column(String(10), nullable=True, comment="Описание операции, связанной с типом")

    # Свойство для отношения с командой
    @property
    def commands(self):
        if "Command" not in Base.metadata.tables:
            from DB.Models.Command import Command
        else:
            Command = Base.metadata.tables["Command"].class_
        return relationship(Command, back_populates="Type")

    def __repr__(self):
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"name={self.name}, "
                f"operation={self.operation}"
                f")>")
