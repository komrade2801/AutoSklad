from typing import Optional

from sqlalchemy.orm import Session

from DB.Engine.BaseCRUD import BaseCRUD
from DB.Models.DeviceConfig import DeviceConfig


class EngineDeviceConfig(BaseCRUD):
    def __init__(self, session: Session):
        super().__init__(session, DeviceConfig)

    def add_device_config(
        self,
        *,
        name: str = "main_device",
        protocol: str = "legacy",
        serial_port: Optional[str] = None,
        baudrate: int = 9600,
        ack_timeout_ms: int = 2000,
        done_timeout_ms: int = 90000,
        require_zero_on_start: bool = True,
        enabled: bool = True,
    ) -> bool:
        return self.add(
            name=name,
            protocol=protocol,
            serial_port=serial_port,
            baudrate=baudrate,
            ack_timeout_ms=ack_timeout_ms,
            done_timeout_ms=done_timeout_ms,
            require_zero_on_start=require_zero_on_start,
            enabled=enabled,
        )

    def get_active(self) -> Optional[DeviceConfig]:
        return self.session.query(self.model).filter_by(enabled=True).order_by(self.model.id.asc()).first()

