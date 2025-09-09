import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class Error(Base, Model):
    """Модель для хранения информации об ошибках в системе."""
    __tablename__ = "Error"  # Имя таблицы в базе данных
    __table_kwargs__ = {"extend_existing": True}  # Указываем аргументы таблицы отдельно

    # Поля таблицы
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment="Уникальный идентификатор ошибки (первичный ключ)")
    error_type = Column(String(100), nullable=False, comment="Тип ошибки (например, Timeout, Device Error и др.)")
    message = Column(String(500), nullable=True, comment="Подробное сообщение об ошибке")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False,
                       comment="Время возникновения ошибки")

    # Индексы
    __table_args__ = (
        Index("idx_error_type", "error_type", unique=False),  # Индекс для поиска по типу ошибки
        Index("idx_timestamp", "timestamp", unique=False),    # Индекс для сортировки по времени возникновения
    )

    def __repr__(self):
        """Представляет объект Error в виде строки для удобства отладки."""
        return (f"<{self.__tablename__}("
                f"id={self.id}, "
                f"error_type={self.error_type}, "
                f"message={self.message}, "
                f"timestamp={self.timestamp}"
                f")>")
