from typing import Optional

from sqlalchemy.orm import Session

from DB.Engine.BaseCRUD import BaseCRUD
from DB.Models.HardwareConfig import HardwareConfig


class EngineHardwareConfig(BaseCRUD):
    def __init__(self, session: Session):
        super().__init__(session, HardwareConfig)

    def add_hardware_config(
        self,
        *,
        device_config_id: int,
        x_axis_motor: int = 1,
        z_axis_motor: int = 3,
        push_motor: int = 5,
        led_default: int = 1,
        lock_ms_default: int = 15000,
        sol_s_default: int = 15,
        push_down_default: int = 900,
        push_up_default: int = 0,
        park_m1_default: int = 0,
        park_m2_default: int = 0,
        park_m3_default: int = 0,
        park_m4_default: int = 0,
        park_m5_default: int = 0,
        speed_x: Optional[int] = None,
        speed_z: Optional[int] = None,
        speed_push: Optional[int] = None,
        boost_x: Optional[int] = None,
        boost_z: Optional[int] = None,
        boost_push: Optional[int] = None,
    ) -> bool:
        return self.add(
            device_config_id=device_config_id,
            x_axis_motor=x_axis_motor,
            z_axis_motor=z_axis_motor,
            push_motor=push_motor,
            led_default=led_default,
            lock_ms_default=lock_ms_default,
            sol_s_default=sol_s_default,
            push_down_default=push_down_default,
            push_up_default=push_up_default,
            park_m1_default=park_m1_default,
            park_m2_default=park_m2_default,
            park_m3_default=park_m3_default,
            park_m4_default=park_m4_default,
            park_m5_default=park_m5_default,
            speed_x=speed_x,
            speed_z=speed_z,
            speed_push=speed_push,
            boost_x=boost_x,
            boost_z=boost_z,
            boost_push=boost_push,
        )

    def get_by_device(self, device_config_id: int) -> Optional[HardwareConfig]:
        return self.session.query(self.model).filter_by(device_config_id=device_config_id).first()

    def update_park_defaults(
        self,
        hw_config_id: int,
        *,
        park_m1: int,
        park_m2: int,
        park_m3: int,
        park_m4: int,
        park_m5: int,
    ) -> bool:
        return self.update(
            index=hw_config_id,
            park_m1_default=park_m1,
            park_m2_default=park_m2,
            park_m3_default=park_m3,
            park_m4_default=park_m4,
            park_m5_default=park_m5,
        )

    def update_sol_s_default(self, hw_config_id: int, *, sol_s: int) -> bool:
        return self.update(index=hw_config_id, sol_s_default=sol_s)

