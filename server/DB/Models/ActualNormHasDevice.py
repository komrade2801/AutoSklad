from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DB.Data.base import Base
from DB.Models.BaseModel import Model


class ActualNormHasDevice(Base, Model):
    __tablename__ = "ActualNormHasDevice"

    actual_norm_id = Column(Integer, ForeignKey("ActualNorm.id"), primary_key=True)
    device_id = Column(Integer, ForeignKey("Device.id"), primary_key=True)

    @property
    def quota(self):
        if "ActualNorm" not in Base.metadata.tables:
            from DB.Models.ActualNorm import ActualNorm
        else:
            ActualNorm = Base.metadata.tables["ActualNorm"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(ActualNorm, back_populates="Devices")

    @property
    def devices(self):
        if "Devices" not in Base.metadata.tables:
            from DB.Models.Device import Device
        else:
            Device = Base.metadata.tables["Devices"].class_  # Получаем класс таблицы, если он уже зарегистрирован.
        return relationship(Device, back_populates="ActualNorm")

    def __repr__(self):
        return (f"<{self.__tablename__}("
                f"actual_norm_id={self.actual_norm_id}, "
                f"device_id={self.device_id}"
                f")>")


# from sqlalchemy import Column, ForeignKeyConstraint, Index, Integer, Table
# from DB.Data.base import Base
#
#
# t_Quota_has_Device = Table(
#     "Quota_has_Device", Base.metadata,
#     Column("Quota_id", Integer, primary_key=True, nullable=False),
#     Column("device_id", Integer, primary_key=True, nullable=False),
#     ForeignKeyConstraint(["device_id"], ["Device.id"], name="fk_Quota_has_Device_Device1"),
#     ForeignKeyConstraint(["Quota_id"], ["Quota.id"], name="fk_Quota_has_Device_Quota1"),
#     Index("fk_Quota_has_Device_Device1_idx", "device_id"),
#     Index("fk_Quota_has_Device_Quota1_idx", "Quota_id"),
#     extend_existing=True
# )