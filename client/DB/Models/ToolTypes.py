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

from ..Data.base import Base
from ..Models.BaseModel import Model


# if "Plan" not in Base.metadata.tables:
#     from DB.Models.Plan import Plan

#  print("Tools")


class ToolTypes(Base, Model):
    __tablename__ = "ToolTypes"
    # Указываем аргументы таблицы отдельно
    __table_kwargs__ = {"extend_existing": True}

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False,
                autoincrement=True, comment="Уникальный идентификатор инструмента")
    name = Column(String(45), nullable=True, comment="Название инструмента")
    description = Column(String(450), nullable=True,
                         comment="Описание инструмента")
    count = Column(Integer, nullable=True, comment="Количество инструмента")
    img = Column(String(45), nullable=True, comment="Изображение инструмента")
    groups_id = Column(Integer, ForeignKey("Group.id"),
                       nullable=True, comment="Ключ на группу инструмента")

    # plans = relationship("Plan", back_populates="Tools")
    @property
    def tools(self):
        if "Tools" not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            # Получаем класс таблицы, если он уже зарегистрирован.
            Tools = Base.metadata.tables["Tools"].class_
        return relationship(Tools, back_populates="ToolTypes")

    @property
    def groups(self):
        if "Groups" not in Base.metadata.tables:
            from DB.Models.Group import Group
        else:
            # Получаем класс таблицы, если она уже зарегистрирован.
            Group = Base.metadata.tables["Groups"].class_
        return relationship(Group, back_populates="ToolTypes")

    def __repr__(self):
        """Представляет объект Status в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"name={self.name}, "
                f"description={self.description}, "
                f"count={self.count}, "
                f"img={self.img}, "
                f"groups_id={self.groups_id}"
                f")>")
