from pydantic import BaseModel, ValidationError, validator
try:
    from pydantic import IPv4Address
except ImportError:
    from pydantic.networks import IPv4Address

class CellsConfig(BaseModel):
    length: int = 0
    columns: int = 0
    rows: int = 0

# Новая модель для описания сигнатуры приложения
class SignatureConfig(BaseModel):
    serial_number: int = 0
    cells: CellsConfig = CellsConfig()

class NetworkConfig(BaseModel):
    ip: IPv4Address
    port: int = 8080

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
    critical_errors: list = []

class AppConfig(BaseModel):
    # Поле signature теперь соответствует структуре в config.json
    signature: SignatureConfig = SignatureConfig()
    network: NetworkConfig = NetworkConfig(ip="127.0.0.1")
    serial: SerialConfig = SerialConfig()
    barcode: BarcodeConfig = BarcodeConfig()
    locks: LockConfig = LockConfig()
    logs: LogConfig = LogConfig()