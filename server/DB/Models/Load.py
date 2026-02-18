from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Load(Base, Model):
    """Модель для хранения информации о загрузке инструментов."""
    __tablename__ = "Load"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор записи загрузки")
    description = Column(String(255), nullable=True, comment="Описание загрузки или дополнительные детали")
    tools_id = Column(Integer, ForeignKey("ToolTypes.id"), nullable=False, comment="Внешний ключ на таблицу ToolTypes")
    mass_load_id = Column(Integer, ForeignKey("MassLoad.id"), nullable=False, comment="Внешний ключ на таблицу mass_load")
    cell_id = Column(Integer, ForeignKey("Cell.id"), nullable=False, comment="Внешний ключ на таблицу Cell")
    plan_id = Column(Integer, ForeignKey("Plan.id"), nullable=True, comment="Внешний ключ на таблицу Plan")
    history_id = Column(Integer, ForeignKey("History.id"), nullable=False, comment="Идентификатор записи из таблицы History")
    status_id = Column(Integer, ForeignKey("Status.id"), nullable=True, comment="Внешний ключ на таблицу Status")

    @property
    def cells(self):
        if "Cells" not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables["Cells"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates="Load")

    @property
    def mass_loads(self):
        if "MassLoads" not in Base.metadata.tables:
            from DB.Models.MassLoad import MassLoad
        else:
            MassLoad = Base.metadata.tables["MassLoads"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(MassLoad, back_populates="Load")

    @property
    def tools(self):
        if "ToolTypes" not in Base.metadata.tables:
            from DB.Models.ToolTypes import ToolTypes
        else:
            ToolTypes = Base.metadata.tables["ToolTypes"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(ToolTypes, back_populates="Load")

    @property
    def plans(self):
        if "Plan" not in Base.metadata.tables:
            from DB.Models.Plan import Plan
        else:
            Plan = Base.metadata.tables["Plan"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Plan, back_populates="Load")

    @property
    def stories(self):
        if "History" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["History"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="Load")

    @property
    def status(self):
        if "Status" not in Base.metadata.tables:
            from ..Models.Status import Status
        else:
            Status = Base.metadata.tables["Status"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Status, back_populates="Load")

    # Индексы
    __table_args__ = (
        Index("idx_load_tools_id", "tools_id", unique=False),
        Index("idx_load_mass_load_id", "mass_load_id", unique=False),
        Index("idx_load_cell_id", "cell_id", unique=False),
        Index("idx_load_plan_id", "plan_id", unique=False),
        Index("idx_load_history_id", "history_id", unique=False)
    )

    def __repr__(self):
        """Представляет объект Load в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"description={self.description}, "
                f"tools_id={self.tools_id}, "
                f"mass_load_id={self.mass_load_id}, "
                f"cell_id={self.cell_id}, "
                f"plan_id={self.plan_id}, "
                f"history_id={self.history_id}, "
                f"status_id={self.status_id}"
                f")>")
