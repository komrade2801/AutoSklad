from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from DB.Data.base import Base
from DB.Models.BaseModel import Model
from datetime import datetime


class Settings(Base, Model):
    """Модель для хранения настроек сервера"""
    __tablename__ = "Settings"
    __table_args__ = (
        Index("key_UNIQUE", "key", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True)  # Уникальный идентификатор настройки
    key = Column(String(100), unique=True, nullable=False)  # Ключ настройки
    value = Column(Text, nullable=False)  # Значение настройки в строковом формате
    value_type = Column(String(20), default='str', nullable=False)  # Тип значения: 'str', 'int', 'bool', 'json'
    category = Column(String(50), default='general', nullable=False)  # Категория настройки для группировки в UI
    description = Column(Text)  # Описание настройки для администраторов
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Время последнего обновления
    updated_by = Column(Integer, comment="User ID who last updated")  # ID пользователя, обновившего настройку
    is_sensitive = Column(Boolean, default=False)  # Флаг чувствительной информации (маскируется в UI)
    requires_restart = Column(Boolean, default=True)  # Требуется ли перезапуск сервера для применения
    validation_rules = Column(Text)  # JSON правила валидации значения

    def __repr__(self):
        return f"<Settings(key={self.key}, value_type={self.value_type}, category={self.category})>"
