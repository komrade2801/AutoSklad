from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Consumption(Base, Model):
    """Модель для хранения информации о расходе инструментов."""
    __tablename__ = "Consumption"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, comment="Уникальный идентификатор записи расхода")
    cell_id = Column(Integer, ForeignKey("Cell.id"), nullable=False, comment="Идентификатор ячейки")
    tools_id = Column(Integer, ForeignKey("ToolTypes.id"), nullable=False, comment="Идентификатор инструмента")
    plan_id = Column(Integer, ForeignKey("Plan.id"), nullable=True, comment="Внешний ключ на таблицу Plan")
    history_id = Column(Integer, ForeignKey("History.id"), nullable=False, comment="Идентификатор записи из таблицы History")

    @property
    def tools(self):
        if "ToolTypes" not in Base.metadata.tables:
            from DB.Models.ToolTypes import ToolTypes
        else:
            ToolTypes = Base.metadata.tables["ToolTypes"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(ToolTypes, back_populates="Consumptions")

    @property
    def cells(self):
        if "Cells" not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables["Cells"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates="Consumptions")

    @property
    def plans(self):
        if "Plan" not in Base.metadata.tables:
            from DB.Models.Plan import Plan
        else:
            Plan = Base.metadata.tables["Plan"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Plan, back_populates="Consumptions")

    @property
    def stories(self):
        if "History" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["History"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="Consumptions")

    # Индексы
    __table_args__ = (
        Index("idx_consumption_tools_id", "tools_id", unique=False),
        Index("idx_consumption_cell_id", "cell_id", unique=False),
        Index("idx_consumption_plan_id", "plan_id", unique=False),
        Index("idx_consumption_history_id", "history_id", unique=False)
    )

    def __repr__(self):
        """Представляет объект Consumption в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"cell_id={self.cell_id}, "
                f"tools_id={self.tools_id}, "
                f"plan_id={self.plan_id}, "
                f"history_id={self.history_id}, "
                f")>")

# cells = relationship("Cell", back_populates="Consumptions")
# operations_consumptions = relationship("OperationsConsumption", back_populates="Consumptions")
# tools = relationship("Tools", back_populates="Consumptions")
