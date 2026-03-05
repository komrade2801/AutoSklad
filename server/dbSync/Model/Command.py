# dbSync/Model/Command.py
from sqlalchemy import Column, Integer, String, DateTime, func, CheckConstraint
from sqlalchemy.orm import relationship

from dbSync.Model.base import sync_base


# 2. Модель Command — хранит команды синхронизации
class Command(sync_base):
    __tablename__ = "Command"

    id = Column(Integer, primary_key=True)
    table_name = Column(String, nullable=False)  # имя таблицы, к которой относится команда
    operation = Column(String, nullable=False)   # ADD, UPDATE или DELETE
    record_id = Column(Integer)                  # ID затронутой записи
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    device_number = Column(Integer, nullable=False)  # номер вендинга

    # связь с записями Record и статусами CommandStatus
    records = relationship(
        "Record",
        back_populates="command",
        cascade="all, delete-orphan"
    )
    statuses = relationship(
        "CommandStatus",
        back_populates="command",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "operation IN ('ADD','UPDATE','DELETE')",
            name="chk_command_operation"
        ),
    )
