"""
Этот модуль содержит определение класса PlanToolTypes, который представляет
таблицу "PlanToolTypes" в базе данных. Класс предназначен для хранения информации
о чертежах, включая такие детали, как название, штрих-код,
назначение и количество.
"""
# if "History" not in Base.metadata.tables:
#     from DB.Models.History import History
# if "Tools" not in Base.metadata.tables:
#     from DB.Models.Tools import Tools

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..Data.base import Base
from ..Models.BaseModel import Model


#  print("Plan")


class PlanToolTypes(Base, Model):
    __tablename__ = "PlanToolTypes"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Идентификатор связи чертежа и типа инструмента (первичный ключ)")
    tool_types_id = Column(Integer, ForeignKey("ToolTypes.id"), nullable=False, comment="Идентификатор типа инструмента")
    tool_types_count = Column(Integer, nullable=False, comment="Количество инструмента данного типа в чертеже")
    plan_id = Column(Integer, ForeignKey("Plan.id"), nullable=False, comment="Идентификатор чертежа")

    @property
    def tool_types(self):
        if "ToolTypes" not in Base.metadata.tables:
            from ..Models.ToolTypes import ToolTypes
        else:
            ToolTypes = Base.metadata.tables["ToolTypes"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(ToolTypes, back_populates="PlanToolTypes")

    @property
    def plans(self):
        if "Plan" not in Base.metadata.tables:
            from ..Models.Plan import Plan
        else:
            Plan = Base.metadata.tables["Plan"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Plan, back_populates="PlanToolTypes")

    # @property
    # def stories(self):
    #     if "Stories" not in Base.metadata.tables:
    #         from ..Models.History import History
    #     else:
    #         History = Base.metadata.tables["Stories"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
    #     return relationship(History, back_populates="PlanToolTypes")

    # Индексы
    __table_args__ = (
        Index("idx_plan_id", "plan_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект PlanToolTypes в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"tool_types_id={self.tool_types_id}, "
                f"tool_types_count={self.tool_types_count}, "
                f"plan_id={self.plan_id}"
                f")>")
