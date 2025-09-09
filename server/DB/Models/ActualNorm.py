from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class ActualNorm(Base, Model):
    __tablename__ = "ActualNorm"
    __table_kwargs__ = {"extend_existing": True}
    __table_args__ = (
        Index("fk_ActualNorm_User1_idx", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="Уникальный идентификатор квоты")
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False, comment="Внешний ключ на таблицу User")
    day = Column(DateTime, nullable=True, comment="Дата")

    @property
    def Device_(self):
        # Отложенный импорт модели Device.
        from DB.Models.Device import Device
        # Связь через промежуточную таблицу ActualNorm_has_Device.
        return relationship(Device, secondary="ActualNormHasDevice", back_populates="ActualNorm")

    @property
    def User_(self):
        from DB.Models.User import User
        return relationship(User, back_populates="ActualNorm")

    @property
    def ToolsNorm(self):
        from DB.Models.ToolsNorm import ToolsNorm
        return relationship(ToolsNorm, back_populates="ActualNorm_")

    def __repr__(self):
        return (f"<ActualNorm("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"day={self.day}"
                f")>")

