"""
Этот модуль содержит определение класса TableRole, который представляет
таблицу "Role" в базе данных. Класс предназначен для хранения информации
о ролях пользователей в системе, включая название роли и связи с правами
доступа и пользователями.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# if "Rights" not in Base.metadata.tables:
#     from DB.Models.Rights import Rights
# if "History" not in Base.metadata.tables:
#     from DB.Models.History import History
# if "Tools" not in Base.metadata.tables:
#     from DB.Models.Tools import Tools

#  print("Role")


class Role(Base, Model):
    """Модель для представления ролей в системе."""
    __tablename__ = "Role"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор роли (первичный ключ)")
    name = Column(String(45), nullable=True, comment="Название роли")  # Название роли
    description = Column(String(450), nullable=True, comment="Описание роли")  # Дополнительное поле для описания роли
    parent_role_id = Column(Integer, ForeignKey("Role.id"), nullable=True, comment="Внешний ключ на родительскую роль для иерархии ролей") # Внешние ключи и связи

    parent_role = relationship("Role", remote_side=[id], backref="child_roles")  # Рекурсивная связь для иерархии ролей

    @property
    def rights(self):
        if "Rights" not in Base.metadata.tables:
            from DB.Models.Rights import Rights
        else:
            Rights = Base.metadata.tables["Rights"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Rights, back_populates="Roles")

    @property
    def users(self):
        if "Users" not in Base.metadata.tables:
            from DB.Models.User import User
        else:
            User = Base.metadata.tables["Users"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(User, back_populates="Roles")

    @property
    def stories(self):
        if "Stories" not in Base.metadata.tables:
            from DB.Models.History import History
        else:
            History = Base.metadata.tables["Stories"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(History, back_populates="Roles")

    # Индексы
    __table_args__ = (
        Index("idx_role_name", "name", unique=False),  # Индекс для быстрого доступа по названию роли
        Index("fk_role_parent_idx", "parent_role_id", unique=False),  # Индекс для быстрого доступа к родительской роли
    )

    def __repr__(self):
        """Представляет объект Role в виде строки для отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id},"
                f"name={self.name}, "
                f"description={self.description}, "
                f"parent_role_id={self.parent_role_id}"
                f")>")
