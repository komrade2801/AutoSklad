"""
Этот модуль содержит определение класса TablePlan, который представляет
таблицу "Plan" в базе данных. Класс предназначен для хранения информации
о чертежах, включая такие детали, как название, штрих-код,
назначение и количество.
"""
# if 'History' not in Base.metadata.tables:
#     from DB.Models.History import History
# if 'Tools' not in Base.metadata.tables:
#     from DB.Models.Tools import Tools

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# print("Plan")


class Plan(Base, Model):
    __tablename__ = 'Plan'  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='Идентификатор чертежа (первичный ключ)')
    enterprise = Column(String(45), nullable=True, comment='Название предприятия')
    barcode = Column(String(45), nullable=True, comment='Штрих-код чертежа')
    name = Column(String(45), nullable=True, comment='Название чертежа')
    description = Column(String(450), nullable=True, comment='Описание чертежа')  # Добавлено описание
    designation = Column(String(100), nullable=True, comment='Назначение чертежа')
    index_list = Column(Integer, nullable=True, comment='Идентификатор списка')
    list_count = Column(Integer, nullable=True, comment='Количество в списке')
    parent_plan_id = Column(Integer, ForeignKey('Plan.id'), nullable=True, comment='Идентификатор родительского чертежа для создания иерархии чертежей')
    parent_plan = relationship('Plan', remote_side=[id], backref='child_plans')

    @property
    def tools(self):
        if 'Tools' not in Base.metadata.tables:
            from ..Models.Tools import Tools
        else:
            Tools = Base.metadata.tables['Tools'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates="Plans")

    @property
    def stories(self):
        if 'Stories' not in Base.metadata.tables:
            from ..Models.History import History
        else:
            History = Base.metadata.tables['Stories'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="Plans")

    # Индексы
    __table_args__ = (
        Index('idx_plan_barcode', 'barcode', unique=False),
        Index('idx_plan_name', 'name', unique=False),
        Index('fk_plan_parent_idx', 'parent_plan_id', unique=False),
    )

    def __repr__(self):
        """Представляет объект Plan в виде строки для удобства отладки."""
        return (f"<Plan("
                f"id={self.id}, "
                f"enterprise={self.enterprise}, "
                f"barcode={self.barcode}, "
                f"name={self.name}, "
                f"description={self.description}, "
                f"Designation={self.designation}, "
                f"List={self.index_list}, "
                f"ListCount={self.list_count}, "
                f"ParentPlan_id={self.parent_plan_id}"
                f")>")

# Внешние ключи и связи
# tools = relationship('Tools', back_populates='Plans')  # Убрали comment
# stories = relationship("History", back_populates="Plans")
