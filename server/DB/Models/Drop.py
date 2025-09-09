import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Drop(Base, Model):
    """Модель для учета операций выдачи инструментов."""
    __tablename__ = "Drop"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор записи в таблице Drop")
    description = Column(String(255), nullable=True, comment="Описание операции или дополнительные детали")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False,comment="Дата и время создания записи")
    cell_id = Column(Integer, ForeignKey("Cell.id"), nullable=False, comment="Внешний ключ на таблицу Cell")
    mass_drop_id = Column(Integer, ForeignKey("MassDrop.id"), nullable=False,comment="Внешний ключ на таблицу massdrop")
    tools_id = Column(Integer, ForeignKey("Tools.id"), nullable=False, comment="Внешний ключ на таблицу Tools")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="DropOperations")

    @property
    def tools(self):
        if "Tools" not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables["Tools"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="Drops")

    @property
    def mass_drops(self):
        if "MassDrops" not in Base.metadata.tables:
            from DB.Models.MassDrop import MassDrop
        else:
            MassDrop = Base.metadata.tables["MassDrops"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(MassDrop, back_populates="Drops")

    @property
    def cells(self):
        if "Cells" not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables["Cells"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates="Drops")

    # Индексы
    __table_args__ = (
        Index("idx_drop_tools_id", "tools_id", unique=False),
        Index("idx_drop_mass_drop_id", "mass_drop_id", unique=False),
        Index("idx_drop_cell_id", "cell_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект Drop в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"description={self.description}, "
                f"created_at={self.created_at}, "
                f"cell_id={self.cell_id}, "
                f"mass_drop_id={self.mass_drop_id}, "
                f"tools_id={self.tools_id}"
                f")>")

# mass_drop = relationship("MassDrop", back_populates="Drops")
# cells = relationship("Cell", back_populates="Drops")
# tools = relationship("Tools", back_populates="Drops")
