from sqlalchemy import Boolean, Column, Integer, String

from DB.Data.base import Base
from DB.Models.BaseModel import Model


class DeviceConfig(Base, Model):
    """
    Конфигурация устройства (уровень подключения и общих политик работы).
    Ожидается одна активная запись на устройство.
    """

    __tablename__ = "DeviceConfig"
    __table_kwargs__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(64), nullable=False, default="main_device")
    protocol = Column(String(32), nullable=False, default="legacy")
    serial_port = Column(String(64), nullable=True)
    baudrate = Column(Integer, nullable=False, default=9600)
    ack_timeout_ms = Column(Integer, nullable=False, default=2000)
    done_timeout_ms = Column(Integer, nullable=False, default=90000)
    require_zero_on_start = Column(Boolean, nullable=False, default=True)
    enabled = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return (
            f"<DeviceConfig(id={self.id}, name={self.name}, protocol={self.protocol}, "
            f"serial_port={self.serial_port}, baudrate={self.baudrate}, enabled={self.enabled})>"
        )
