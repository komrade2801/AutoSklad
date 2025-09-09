"""
Этот модуль содержит определение класса TableIdentification, который представляет
таблицу "Identification" в базе данных. Класс предназначен для хранения информации о
идентификации пользователей, включая временные метки, статусы и связь с таблицей пользователей.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Identification(Base, Model):
    """Модель для представления данных об идентификации пользователя."""
    __tablename__ = "Identification"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор записи")
    datetime = Column(DateTime, nullable=True, comment="Дата и время идентификации")
    status = Column(Integer, nullable=True, comment="Статус идентификации (например, успешная/неуспешная)")
    description = Column(String(450), nullable=True, comment="Дополнительное описание или комментарий к идентификации")
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False, comment="Идентификатор пользователя (внешний ключ)")

    @property
    def users(self):
        if "Users" not in Base.metadata.tables:
            from DB.Models.User import User
        else:
            User = Base.metadata.tables["Users"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(User, back_populates="Identifications")

    # Индексы и настройки таблицы
    __table_args__ = (
        Index("idx_identification_user", "user_id", unique=False),  # Индексы
        Index("idx_identification_datetime", "datetime", unique=False),
        Index("idx_identification_status", "status", unique=False),
    )

    def __repr__(self):
        """Представляет объект Identification в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"datetime={self.datetime}, "
                f"status={self.status}, "
                f"description={self.description}"
                f"user_id={self.user_id}, "
                f")>")
