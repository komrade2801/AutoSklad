# sync_config.py
import json
from pathlib import Path

class SyncConfig:
    def __init__(self, path: Path=Path(__file__).parent.parent / "config.json"):

        cfg = json.loads(path.read_text(encoding="utf-8"))
        srv = cfg["server"]

        # device_id
        self.device_id = cfg["signature"]["serial_number"]

        # host: обязательно с http:// и портом
        ip, port = srv["ip"], srv["port"]
        self.host = f"http://{ip}"
        self.ip = f"http://{ip}"
        self.port =port

        # token
        self.token = srv["token"]

        # secret — raw bytes, точь-в-точь как в первом проекте
        # если там просто бинарные данные, лучше хранить их в JSON в base64
        # но можно и так:
        self.secret = srv["secret"].encode("latin1")

        # aes — ровно 16 байт
        aes_str = srv["aes"]
        if len(aes_str) != 16:
            raise ValueError(f"AES key must be 16 chars, got {len(aes_str)}")
        self.aes = aes_str.encode("utf-8")

        # таймауты
        self.sender_timeout = int(srv["sender_timeout"])
        self.receiver_timeout = int(srv["receiver_timeout"])
        self.push_http_timeout = int(srv.get("push_http_timeout", 120))
