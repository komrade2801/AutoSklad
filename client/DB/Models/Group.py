"""
Этот модуль содержит определение класса TableGroup, который представляет
таблицу "Group" в базе данных. Класс предназначен для хранения информации
о группах, их названиях и возможных связях с другими таблицами.
"""

# if 'Cell' not in Base.metadata.tables:
#     from .Cell import Cell
# # if TYPE_CHECKING:
# if 'Tools' not in Base.metadata.tables:
#     from .Tools import Tools

# Group.py
from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# print("Group")


class Group(Base, Model):
    __tablename__ = 'Group'  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='Уникальный идентификатор группы (первичный ключ)')
    name = Column(String(100), nullable=True, comment='Название группы')  # Увеличен размер для более длинных названий
    description = Column(String(450), nullable=True, comment='Описание группы')  # Описание группы
    paren_group_id = Column(Integer, nullable=True, comment="Код родительской группы")

    @property
    def cells(self):
        if 'Cells' not in Base.metadata.tables:
            from DB.Models.Cell import Cell
        else:
            Cell = Base.metadata.tables['Cells'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Cell, back_populates="Drops")

    @property
    def tools(self):
        if 'Tools' not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables['Tools'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="Drops")

    # Индексы
    __table_args__ = (
        Index('idx_group_name', 'name', unique=False),
        Index("idx_group_paren_group_id", "paren_group_id", unique=False),
    )

    def __repr__(self):
        """Представляет объект Group в виде строки для удобства отладки."""
        return (f"<Group("
                f"id={self.id}, "
                f"name={self.name}, "
                f"description={self.description}, "
                f"paren_group_id={self.paren_group_id}"
                f")>")

# Внешние связи
# cells = relationship('Cell', back_populates='Groups')
# tools = relationship('Tools', back_populates='Groups')
# cell: Mapped['Cell'] = mapped_column(ForeignKey('Cell.id'))
# cell_rel: Mapped['Cell'] = relationship('Cell', back_populates='Groups')
