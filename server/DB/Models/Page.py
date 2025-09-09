"""
Этот модуль содержит определение класса Page, который представляет
таблицу "Page" в базе данных. Класс предназначен для хранения
информации о страницах шаблонов, включая имя файла и описание.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Page(Base, Model):
    """Модель для представления страниц шаблонов в системе."""
    __tablename__ = "Page"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Если таблица уже есть, просто расширяем

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, comment="Уникальный идентификатор страницы")
    name = Column(String(45), nullable=True, comment="Имя HTML-файла страницы (например, screen_2_mass_load.html)")
    description = Column(String(150), nullable=True, comment="Описание или заголовок страницы")

    # Связь с правами (если в системе есть модель Rights)
    @property
    def rights(self):
        """
        Отношение к записям Rights, где Page.id используется как внешний ключ.
        """
        # Динамически импортируем класс, чтобы избежать циклических зависимостей
        if "Rights" not in Base.metadata.tables:
            from DB.Models.Rights import Rights
        else:
            Rights = Base.metadata.tables["Rights"].class_
        return relationship(Rights, back_populates="Page")

    def __repr__(self):
        """Представляет объект Page в виде строки для отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"name={self.name}, "
                f"description={self.description}"
                f")>")
