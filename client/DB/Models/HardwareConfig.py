from sqlalchemy import Column, ForeignKey, Integer

from DB.Data.base import Base
from DB.Models.BaseModel import Model


class HardwareConfig(Base, Model):
    """
    Параметры кинематики и дефолтного сценария выдачи для конкретного устройства.
    """

    __tablename__ = "HardwareConfig"
    __table_kwargs__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    device_config_id = Column(Integer, ForeignKey("DeviceConfig.id"), nullable=False)

    # Маппинг осей/моторов
    x_axis_motor = Column(Integer, nullable=False, default=1)
    z_axis_motor = Column(Integer, nullable=False, default=3)
    push_motor = Column(Integer, nullable=False, default=5)

    # Дефолты сценария выдачи
    led_default = Column(Integer, nullable=False, default=1)
    lock_ms_default = Column(Integer, nullable=False, default=15000)
    push_down_default = Column(Integer, nullable=False, default=900)
    push_up_default = Column(Integer, nullable=False, default=0)
    park_m1_default = Column(Integer, nullable=False, default=0)
    park_m2_default = Column(Integer, nullable=False, default=0)
    park_m3_default = Column(Integer, nullable=False, default=0)
    park_m4_default = Column(Integer, nullable=False, default=0)
    park_m5_default = Column(Integer, nullable=False, default=0)

    # Параметры для инженерного меню
    speed_x = Column(Integer, nullable=True)
    speed_z = Column(Integer, nullable=True)
    speed_push = Column(Integer, nullable=True)
    boost_x = Column(Integer, nullable=True)
    boost_z = Column(Integer, nullable=True)
    boost_push = Column(Integer, nullable=True)

    def __repr__(self):
        return (
            f"<HardwareConfig(id={self.id}, device_config_id={self.device_config_id}, "
            f"x_axis_motor={self.x_axis_motor}, z_axis_motor={self.z_axis_motor}, "
            f"push_motor={self.push_motor})>"
        )
