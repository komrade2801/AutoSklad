"""
Этот модуль содержит определение класса TableHelp, который представляет
таблицу "Help" в базе данных. Класс позволяет сохранять текстовые сообщения
и сопутствующую информацию о дате с использованием SQLAlchemy.
"""

from sqlalchemy import Column, Integer, String, DateTime
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Help(Base, Model):
    __tablename__ = "Help"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)  # Столбец id с первичным ключом
    text = Column(String(450), nullable=True)  # Столбец text с типом VARCHAR(450), который может быть пустым
    data = Column(DateTime, nullable=True)  # Столбец data с типом DATETIME, который также может быть пустым

    def __repr__(self):
        """Представляет объект в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"text={self.text}, "
                f"data={self.data}"
                f")>")
