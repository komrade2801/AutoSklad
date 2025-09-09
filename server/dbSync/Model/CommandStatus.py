# dbSync/Model/CommandStatus.py
from sqlalchemy import Column, Integer, ForeignKey, String, func, DateTime, CheckConstraint
from sqlalchemy.orm import relationship

from dbSync.Model.base import sync_base
from dbSync.constants import CommandStatusEnum


# 4. Модель CommandStatus — хранит статусы выполнения команд
class CommandStatus(sync_base):
    __tablename__ = "CommandStatus"

    id = Column(Integer, primary_key=True)
    command_id = Column(Integer, ForeignKey("Command.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # PENDING, IN_PROGRESS, COMPLETED или FAILED
    updated_at = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    command = relationship("Command", back_populates="statuses")

    __table_args__ = (
        CheckConstraint(
            f"status IN ({','.join(repr(s) for s in CommandStatusEnum.values())})",
            name="chk_commandstatus_status"
        ),
    )
