"""
Этот модуль содержит определение класса TableHistory, который представляет
таблицу "History" в базе данных. Класс предназначен для хранения истории
действий пользователей с инструментами, включая идентификаторы пользователей и
их роли, а также дату и время действий.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# from typing import TYPE_CHECKING
# if 'Tools' not in Base.metadata.tables:
#     from DB.Models.Tools import Tools
# # if TYPE_CHECKING:
# if 'Role' not in Base.metadata.tables:
#     from DB.Models.Role import Role
# # if TYPE_CHECKING:
# if 'User' not in Base.metadata.tables:
#     from DB.Models.User import User

# print("History")


class History(Base, Model):
    __tablename__ = 'History'  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='Уникальный идентификатор записи истории (первичный ключ)')
    datetime = Column(DateTime, nullable=True, comment='Дата и время события в истории')
    status = Column(Integer, nullable=True, comment='Статус действия в истории (например, выполнено/не выполнено)')
    description = Column(String(450), nullable=True, comment='Описание или дополнительные комментарии для записи истории')
    user_id = Column(Integer, ForeignKey('User.id'), nullable=False, comment='Идентификатор пользователя, связанного с событием')
    user_role_id = Column(Integer, ForeignKey('Role.id'), nullable=False, comment='Идентификатор роли пользователя, участвующего в событии')
    tools_id = Column(Integer, ForeignKey('Tools.id'), nullable=False, comment='Идентификатор инструмента, связанного с событием')

    @property
    def tools(self):
        if 'Tools' not in Base.metadata.tables:
            from DB.Models.Tools import Tools
        else:
            Tools = Base.metadata.tables['Tools'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Tools, back_populates='Stories')

    @property
    def plans(self):
        if 'Plans' not in Base.metadata.tables:
            from DB.Models.Plan import Plan
        else:
            Plan = Base.metadata.tables['Plans'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Plan, back_populates='Stories')

    @property
    def roles(self):
        if 'Roles' not in Base.metadata.tables:
            from DB.Models.Role import Role
        else:
            Role = Base.metadata.tables['Roles'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Role, back_populates='Stories')

    @property
    def users(self):
        if 'Users' not in Base.metadata.tables:
            from DB.Models.User import User
        else:
            User = Base.metadata.tables['Users'].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(User, back_populates='Stories')

    def __repr__(self):
        """Представляет объект History в виде строки для удобства отладки."""
        return (f"<History("
                f"id={self.id}, "
                f"datetime={self.datetime}, "
                f"Status={self.status}, "
                f"description={self.description}"
                f"user_id={self.user_id}, "
                f"user_role_id={self.user_role_id}, "
                f"tools_id={self.tools_id}, "
                f")>")


# Plan_id = Column(Integer, ForeignKey('Plan.id'), nullable=True,
#                  comment='Идентификатор чертежа, связанного с событием')

# # Индексы
# __table_args__ = (
#     Index('idx_history_user', 'user_id', unique=False),
#     Index('idx_history_role', 'user_role_id', unique=False),
#     Index('idx_history_tools', 'tools_id', unique=False),
#     Index('idx_history_plan', 'Plan_id', unique=False),
#     Index('idx_history_datetime', 'datetime', unique=False),
# )


# tools = relationship('Tools', back_populates='Stories')
# role = relationship('Role', back_populates='Stories')
# plans = relationship('Plan', back_populates='Stories')
# users = relationship('User', back_populates='Stories')
