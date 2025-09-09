"""
Этот модуль содержит определение класса TableRights, который представляет
таблицу "Rights" в базе данных. Класс предназначен для хранения прав
доступа пользователей, ассоциированных с ролями, включая название прав,
идентификатор роли и состояние (разрешение или запрет).
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


# if "Role" not in Base.metadata.tables:
#     from DB.Models.Role import Role

#  print("Rights")


class Rights(Base, Model):
    """Модель для представления прав доступа в системе."""
    __tablename__ = "Rights"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор записи о правах доступа")
    name = Column(String(45), nullable=False, comment="Название права доступа")  # Название права
    description = Column(String(450), nullable=True, comment="Описание права доступа")  # Описание права
    role_id = Column(Integer, ForeignKey("Role.id"), nullable=False, comment="Внешний ключ на таблицу Role") # Внешние ключи и связи
    page_id = Column(Integer, ForeignKey("Page.id"), nullable=False, comment="Внешний ключ на таблицу Page" )

    @property
    def roles(self):
        if "Roles" not in Base.metadata.tables:
            from DB.Models.Role import Role
        else:
            Role = Base.metadata.tables["Roles"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Role, back_populates="Rights")

    @property
    def pages(self):
        if "Page" not in Base.metadata.tables:
            from DB.Models.Page import Page
        else:
            Page = Base.metadata.tables["Page"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Page, back_populates="Rights")

    def __repr__(self):
        """Представляет объект Rights в виде строки для отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"Name={self.name}, "
                f"description={self.description}"
                f"role_id={self.role_id}, "
                f"page_id={self.page_id}, "
                f")>")
