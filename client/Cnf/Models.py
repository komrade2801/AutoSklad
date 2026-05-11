from pathlib import Path
from typing import Optional, List, Dict
from pydantic import BaseModel, ValidationError, validator

# Для работы с IPv4-адресами
try:
    from pydantic import IPv4Address
except ImportError:
    from pydantic.networks import IPv4Address


class CellsConfig(BaseModel):
    length: int = 0
    columns: int = 0
    rows: int = 0


class SignatureConfig(BaseModel):
    serial_number: int = 0
    cells: CellsConfig = CellsConfig()


class NetworkConfig(BaseModel):
    ip: IPv4Address
    port: int = 8080
    subnet_mask: Optional[IPv4Address] = None
    gateway: Optional[IPv4Address] = None
    dns: Optional[IPv4Address] = None


class SerialConfig(BaseModel):
    port: str = "COM30"
    baudrate: int = 9600


class BarcodeConfig(BaseModel):
    port: str = "COM1"
    baudrate: int = 9600


class LockConfig(BaseModel):
    load_locked: bool = False
    drop_locked: bool = False


class LogConfig(BaseModel):
    critical_errors: List[Dict] = []


class ServerConfig(BaseModel):
    ip: IPv4Address
    port: int
    token: str
    secret: str
    aes: str
    sender_timeout: int
    receiver_timeout: int

    @validator("aes")
    def check_aes_length(cls, v: str) -> str:
        if len(v) != 16:
            raise ValueError(f"AES key must be 16 chars, got {len(v)}")
        return v


class KeyConfig(BaseModel):
    aes: Optional[str] = None


class DevConfig(BaseModel):
    ttyUSB: Optional[str] = None
    serial: Optional[str] = None
    hal_uart: Optional[str] = None
    barcode_uart: Optional[str] = None
    barcode_serial: Optional[str] = None


class AppConfig(BaseModel):
    signature: SignatureConfig = SignatureConfig()
    server: ServerConfig
    network: NetworkConfig = NetworkConfig(ip="127.0.0.1")
    serial: SerialConfig = SerialConfig()
    barcode: BarcodeConfig = BarcodeConfig()
    key: KeyConfig = KeyConfig()
    dev: DevConfig = DevConfig()
    locks: LockConfig = LockConfig()
    logs: LogConfig = LogConfig()

    class Config:
        # игнорируем в JSON поля, не описанные в моделях
        extra = "ignore"


# Пример чтения и валидации:
if __name__ == "__main__":
    import json

    cfg_path = Path(__file__).parent / "config.json"
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    try:
        cfg = AppConfig.model_validate(raw)
    except ValidationError as e:
        print("Ошибка валидации конфига:", e)
        raise SystemExit(1)

    # Проверяем, что всё загружено как надо:
    print(cfg.model_dump_json(indent=2, exclude_none=True))
