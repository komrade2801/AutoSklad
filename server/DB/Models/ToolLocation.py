from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class ToolLocation(Base, Model):
    __tablename__ = "ToolLocation"

    tools_id = Column(Integer, ForeignKey("Tools.id"), primary_key=True)
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=False)

    @property
    def tools(self):
        if "Tools" not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables["Tools"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="ToolLocations")

    @property
    def status(self):
        if "Status" not in Base.metadata.tables:
            from DB.Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Status, back_populates="ToolLocations")

    def __repr__(self):
        """Представляет объект Status в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"tools_id={self.tools_id}, "
                f"status_id={self.status_id}"
                f")>")
