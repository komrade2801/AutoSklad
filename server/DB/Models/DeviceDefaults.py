from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from DB.Data.base import Base
from DB.Models.BaseModel import Model
from datetime import datetime


class DeviceDefaults(Base, Model):
    """Модель для хранения шаблонов конфигураций устройств"""
    __tablename__ = "DeviceDefaults"
    __table_args__ = (
        Index("template_name_UNIQUE", "template_name", unique=True),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True)  # Уникальный идентификатор шаблона
    template_name = Column(String(100), unique=True, nullable=False)  # Имя шаблона конфигурации
    config_type = Column(String(50), default='device_config', nullable=False)  # Тип конфигурации (device_config, etc.)
    config_json = Column(Text, nullable=False)  # JSON строка с полной конфигурацией устройства
    description = Column(Text)  # Описание шаблона для администраторов
    is_active = Column(Boolean, default=True)  # Активен ли шаблон для использования
    created_at = Column(DateTime, default=datetime.utcnow)  # Время создания шаблона

    def __repr__(self):
        return f"<DeviceDefaults(template_name={self.template_name}, config_type={self.config_type}, active={self.is_active})>"
