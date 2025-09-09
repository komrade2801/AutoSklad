import logging
import threading
import json
import os
import hmac
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

import requests
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.error import HTTPError
from urllib3.exceptions import MaxRetryError, NewConnectionError

from dbSync.Logic_v2.JSONSchemaValidator import JSONSchemaValidator

logger = logging.getLogger(__name__)


def serializer(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")


class TransportService:
    def __init__(
            self,
            base_url: str,
            jwt_token: Optional[str] = None,
            hmac_secret: Optional[bytes] = None,
            aes_key: Optional[bytes] = None,
            validator=JSONSchemaValidator(),
            device_id=None,
            port="",
            # Добавляем новый параметр для выбора протокола
            protocol: str = "http"
    ):
        self.port = port
        self.device_id = device_id
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.hmac_secret = hmac_secret
        self.aes_key = aes_key
        self.validator = validator

        # Новый атрибут для хранения активного WebSocket-соединения
        self.websocket = None

        # Новый атрибут для выбора протокола: 'http' или 'ws'
        self.protocol = protocol.lower()
        if self.protocol not in ["http", "ws"]:
            raise ValueError("Unsupported protocol. Use 'http' or 'ws'.")

    # Остальные методы (_get_headers, _sign_hmac, _encrypt, _decrypt) остаются без изменений

    # --- Новые методы для работы с WebSocket ---
    async def connect(self):
        """Устанавливает WebSocket-соединение с сервером."""
        if self.protocol != "ws":
            return

        ws_url = f"ws://{self.base_url}:{self.port}/ws/sync/{self.device_id}"
        logger.info(f"Connecting to WebSocket at {ws_url}")

        try:
            self.websocket = await websockets.connect(ws_url)
            logger.info(f"WebSocket connection established for device {self.device_id}")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.websocket = None
            raise

    async def disconnect(self):
        """Закрывает WebSocket-соединение."""
        if self.websocket:
            await self.websocket.close()
            logger.info(f"WebSocket connection closed for device {self.device_id}")
            self.websocket = None

    async def _send_and_receive_ws(self, command_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправляет команду по WebSocket и ждёт ответ.
        Этот метод будет использоваться внутренне для всех операций.
        """
        if not self.websocket:
            await self.connect()

        full_payload = {"type": command_type, "payload": payload}
        body = json.dumps(full_payload).encode("utf-8")

        if self.aes_key:
            body = self._encrypt(body)

        try:
            await self.websocket.send(body)
            # Ждём ответ
            response_content = await self.websocket.recv()

            # Ответ приходит в байтах, возможно, зашифрованный
            if self.aes_key:
                response_content = self._decrypt(response_content)

            response = json.loads(response_content)

            if "error" in response:
                raise RuntimeError(f"Server error: {response['error']}")

            return response["payload"]  # Возвращаем только полезную нагрузку

        except Exception as e:
            logger.error(f"Error during WebSocket communication: {e}")
            # В случае ошибки, закрываем соединение и пробрасываем исключение
            await self.disconnect()
            raise

    # --- Модифицированные методы для переключения между HTTP и WS ---
    def send_schema(self, endpoint: str, schema_json: Dict[str, Any], device: int) -> Dict[str, Any]:
        """
        Отправляет JSON-схему на сервер, используя HTTP или WebSocket.
        """
        if self.protocol == "http":
            # Ваша существующая HTTP-логика
            ...

        elif self.protocol == "ws":
            # Новая логика для WebSocket
            ...
            # Пока оставим handshake через HTTP, так как это разовая операция.
            # Если нужно, можно переписать и её, но это требует немного другой
            # логики с ожиданием ответа.

        # Логика handshake через HTTP, как у вас было.
        # Мы решили, что пока это разовый запрос и можно оставить так.
        ...
        self.validator.validate(schema_json, 'handshake_request')
        url = f"{self.base_url}:{self.port}{endpoint}?device={device}"
        body = json.dumps(schema_json).encode('utf-8')
        if self.aes_key:
            body = self._encrypt(body)
        headers = self._get_headers()
        if self.hmac_secret:
            headers['X-Signature'] = self._sign_hmac(body)

        try:
            resp = requests.post(url, data=body, headers=headers)
            resp.raise_for_status()
            data = resp.content
            if self.aes_key:
                data = self._decrypt(data)
            result = json.loads(data)
            self.validator.validate(result, 'handshake_response')
            return result
        except requests.RequestException as e:
            logger.error(f"Error sending handshake via HTTP: {e}")
            return {"mapping": "", "schema_hash": ""}

    def send_push(self, endpoint: str, payload: dict[str, any]) -> dict[str, any]:
        """
        Отправляет пакет команд на сервер, используя HTTP или WebSocket.
        """
        device_id = self.device_id
        if device_id is None:
            if "device" not in payload:
                raise ValueError("Neither self.device_id nor payload['device'] is set")
            device_id = payload["device"]
            if device_id is None:
                raise ValueError("payload['device'] is None")

        if self.protocol == "http":
            # Ваша существующая HTTP-логика send_push
            body = json.dumps(payload, default=serializer).encode("utf-8")
            if self.aes_key:
                body = self._encrypt(body)
            headers = self._get_headers()
            if self.hmac_secret:
                headers["X-Signature"] = self._sign_hmac(body)
            url = f"{self.base_url}:{self.port}{endpoint}?device={device_id}"

            resp = requests.post(url, data=body, headers=headers)
            resp.raise_for_status()

            content = resp.content
            if self.aes_key:
                try:
                    content = self._decrypt(content)
                except ValueError:
                    pass

            result = json.loads(content)
            self.validator.validate(result, "push_response")
            return result

        elif self.protocol == "ws":
            # НОВАЯ WebSocket-логика send_push
            # Мы можем использовать async/await, если обернуть этот метод
            # в синхронный декоратор или использовать run_in_threadpool.
            # Для простоты, пока будем считать, что это вызывается из async-контекста.
            return self._send_and_receive_ws("push", payload)

    def send_pull(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запрашивает новые команды с сервера, используя HTTP или WebSocket.
        """
        if self.protocol == "http":
            # Ваша существующая HTTP-логика send_pull
            url = f"{self.base_url}:{self.port}{endpoint}"
            headers = self._get_headers()

            resp = requests.get(url, params=params, headers=headers)
            resp.raise_for_status()

            content = resp.content
            if self.aes_key:
                try:
                    content = self._decrypt(content)
                except ValueError:
                    pass

            data = json.loads(content)
            self.validator.validate(data, 'pull_response')
            return data

        elif self.protocol == "ws":
            # НОВАЯ WebSocket-логика send_pull
            return self._send_and_receive_ws("pull", params)