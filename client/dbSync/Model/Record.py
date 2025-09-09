# dbSync/Model/Record.py

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship

from dbSync.Model.base import sync_base


# 3. Модель Record — хранит данные команд (JSON) и время последнего изменения
class Record(sync_base):
    __tablename__ = "Record"

    id = Column(Integer, primary_key=True)
    command_id = Column(Integer, ForeignKey("Command.id", ondelete="CASCADE"), nullable=False )
    data_json = Column(Text, nullable=False)  # сериализованные данные для CREATE/UPDATE
    last_modified = Column(DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    command = relationship("Command", back_populates="records")
