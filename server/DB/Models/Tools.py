"""
Этот модуль содержит определение класса TableTools, который представляет
таблицу "Tools" в базе данных. Класс предназначен для хранения информации
об инструментах, связанных с планами, включая такие детали, как название,
описание, штрих-код и изображения, а также способы их группировки.
"""

# if "Group" not in Base.metadata.tables:
#     from DB.Models.Group import Group
# if "Cell" not in Base.metadata.tables:
#     from DB.Models.Cell import Cell
# if "History" not in Base.metadata.tables:
#     from DB.Models.History import History
# Tools.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from DB.Data.base import Base
from DB.Models.BaseModel import Model

if "Plan" not in Base.metadata.tables:
    from DB.Models.Plan import Plan

#  print("Tools")


class Tools(Base, Model):
    __tablename__ = "Tools"
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор инструмента")
    inventory_number = Column(String, nullable=True, comment="Инвентарный номер")
    barcode = Column(String(45), nullable=True, comment="Баркод инструмента")
    plan_id = Column(Integer, ForeignKey("Plan.id"), nullable=True, comment="Идентификатор чертежа")
    tool_type_id = Column(Integer, ForeignKey("ToolTypes.id"), nullable=True, comment="Ключ на тип инструмента")
    name = Column(String(45), nullable=True, comment="Название инструмента")
    description = Column(String(450), nullable=True, comment="Описание инструмента")
    count = Column(Integer, nullable=True, comment="Количество инструмента")
    img = Column(String(45), nullable=True, comment="Изображение инструмента")
    groups_id = Column(Integer, ForeignKey("Group.id"), nullable=True, comment="Ключ на группу инструмента")

    @property
    def plans(self):
        if "Plans" not in Base.metadata.tables:
            from DB.Models.Plan import Plan
        else:
            Plan = Base.metadata.tables["Plans"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Plan, back_populates="Tools")

    @property
    def groups(self):
        if "Groups" not in Base.metadata.tables:
            from DB.Models.Group import Group
        else:
            Group = Base.metadata.tables["Groups"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Group, back_populates="ToolTypes")

    @property
    def cells(self):
        if "Cells" not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables["Cells"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates="Tools")

    @property
    def stories(self):
        if "Stories" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["Stories"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="Tools")

    def __repr__(self):
        """Представляет объект Status в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"inventory_number={self.inventory_number}, "
                f"barcode={self.barcode}, "
                f"plan_id={self.plan_id}, "
                f"tool_type_id={self.tool_type_id}, "
                f"name={self.name}, "
                f"description={self.description}, "
                f"count={self.count}, "
                f"img={self.img}, "
                f"groups_id={self.groups_id}"
                f")>")
