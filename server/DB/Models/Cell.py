"""
Этот модуль содержит определение класса TableCell, который представляет
таблицу "Cell" в базе данных. Класс используется для хранения информации
о ячейках, включая их номер и связи с другими таблицами: Tools и Group.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Cell(Base, Model):
    """Модель для хранения информации о ячейке с инструментами и группами."""
    __tablename__ = "Cell"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор ячейки")
    number = Column(Integer, nullable=True, unique=True, comment="Номер ячейки")
    description = Column(String(255), nullable=True, comment="Описание ячейки или дополнительные детали")
    groups_id = Column(Integer, ForeignKey("Group.id"), nullable=True, comment="Внешний ключ на таблицу Group")
    tools_id = Column(Integer, ForeignKey("ToolTypes.id"), nullable=True)
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=True, comment="Внешний ключ на таблицу Status")
    hal_x = Column(Integer, nullable=True, comment="Целевая координата X для HAL-сценария")
    hal_z = Column(Integer, nullable=True, comment="Целевая координата Z для HAL-сценария")

    @property
    def devices(self):
        from ..Models.CellHasDevice import CellHasDevice
        return relationship(CellHasDevice, back_populates="Cell")

    @property
    def status(self):
        if "Status" not in Base.metadata.tables:
            from ..Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Status, back_populates="Cell")

    @property
    def groups(self):
        if "Groups" not in Base.metadata.tables:
            from ..Models.Group import Group
        else:
            Group = Base.metadata.tables["Groups"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Group, back_populates="Cell")

    # @property
    # def tools(self):
    #     if "Tools" not in Base.metadata.tables:
    #         from ..Models.Tools import Tools
    #     else:
    #         Tools = Base.metadata.tables["Tools"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
    #     return relationship(Tools, back_populates="Cells")
    #
    # __table_args__ = (
    #     Index("idx_cell_groups_id", "groups_id", unique=False),
    #     Index("idx_cell_tools_id", "tools_id", unique=False),
    # )
    @property
    def tools(self):
        if "ToolTypes" not in Base.metadata.tables:
            from ..Models.ToolTypes import ToolTypes
        else:
            ToolTypes = Base.metadata.tables["ToolTypes"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(ToolTypes, back_populates="Cells")

    __table_args__ = (
        Index("idx_cell_groups_id", "groups_id", unique=False),
        Index("idx_cell_tools_id", "tools_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект Cell в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"number={self.number}, "
                f"description={self.description}, "
                f"groups_id={self.groups_id}, "
                f"tools_id={self.tools_id}, "
                f"status_id={self.status_id}, "
                f"hal_x={self.hal_x}, "
                f"hal_z={self.hal_z}"
                f")>")


# tools = relationship("Tools", back_populates="Cells")
# groups = relationship("Group", back_populates="Cells")

