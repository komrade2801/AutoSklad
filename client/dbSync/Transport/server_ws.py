import asyncio
import json
import os
import hashlib
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

import websockets
from websockets.asyncio.server import WebSocketServerProtocol
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES

logger = logging.getLogger("sync.ws")

class WebSocketTransport:
    """
    Универсальный WebSocket-транспорт для полнодуплексного обмена:
      • В режиме server: слушает подключения, расшифровывает входящие
        сообщения, кладёт их в INBOUND_QUEUES, ждёт ответа из очереди,
        шифрует и отсылает обратно.
      • В режиме client: подключается к ws-серверу, шифрует любые
        словари/payload’ы, посылает и ждёт зашифрованный ответ.
    """

    def __init__(
        self,
        aes_key: bytes,
        mode: str,
        *,
        host: str = "0.0.0.0",
        port: int = 8765,
        uri: Optional[str] = None,
        device_id: Optional[int] = None,
    ):
        self.aes_key = aes_key
        self.mode = mode
        self.host = host
        self.port = port
        self.uri = uri
        self.device_id = device_id
        self.server: Optional[websockets.server.Serve] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    def _encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(pad(data, AES.block_size))

    def _decrypt(self, raw: bytes) -> bytes:
        iv, ct = raw[:16], raw[16:]
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size)

    async def _handler(self, ws: WebSocketServerProtocol, path: str):
        try:
            parsed = urlparse(path)
            query = parse_qs(parsed.query)

            device = query.get("device", [None])[0]
            if not device or not device.isdigit():
                await ws.close(code=1008)
                logger.error("Неверный или отсутствующий device ID в пути: %r", path)
                return

            device = int(device)
            queue_in = INBOUND_QUEUES.get(device)

            if not queue_in:
                await ws.close(code=1013)
                logger.error("Нет очереди для устройства %d", device)
                return

            logger.info("Устройство %d подключено", device)

            async for raw in ws:
                try:
                    plain = self._decrypt(raw)
                except Exception as e:
                    logger.error("Ошибка дешифрования от устройства %d: %s", device, e)
                    continue

                try:
                    msg = json.loads(plain.decode("utf-8"))
                except json.JSONDecodeError:
                    logger.error("Невалидный JSON от устройства %d", device)
                    continue

                h = hashlib.sha256(plain).hexdigest()
                reply_q = asyncio.Queue()

                queue_in.put({
                    "type": msg.get("type", "handshake"),
                    "payload": msg.get("payload", msg),
                    "hash": h,
                    "reply_queue": reply_q
                })

                try:
                    result = await asyncio.wait_for(reply_q.get(), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning("Таймаут ожидания от устройства %d", device)
                    continue

                resp_plain = json.dumps(result).encode("utf-8")
                await ws.send(self._encrypt(resp_plain))

        except websockets.ConnectionClosed:
            logger.info("Устройство %d отключено", device)

    async def start_server(self):
        async def handler(ws: WebSocketServerProtocol, path: str):
            await self._handler(ws, path)

        self.server = await websockets.serve(
            handler, self.host, self.port
        )
        logger.info("WS сервер запущен на %s:%d", self.host, self.port)

    async def connect(self):
        assert self.uri and self.device_id is not None
        url = f"{self.uri}/sync/ws?device={self.device_id}"
        self.ws = await websockets.connect(url)
        logger.info("Клиент WS подключён к %s", url)

    async def send(self, msg: Dict[str, Any]) -> Any:
        assert self.ws
        data = json.dumps(msg).encode("utf-8")
        await self.ws.send(self._encrypt(data))
        raw = await self.ws.recv()
        plain = self._decrypt(raw)
        return json.loads(plain.decode("utf-8"))

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def handshake(self, schema: Dict[str, Any]) -> Any:
        return await self.send({"type": "handshake", "payload": schema})

    async def push(self, commands: list, schema_hash: str) -> Any:
        return await self.send({
            "type": "push", "payload": commands, "hash": schema_hash
        })

    async def pull(self, since: str) -> Any:
        return await self.send({
            "type": "pull", "payload": {"since": since}, "hash": ""
        })

# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def run():
        transport = WebSocketTransport(
            aes_key=b"16byteslongkey!!",
            mode="server",
            host="192.168.0.10",
            port=8765
        )
        await transport.start_server()

        client = WebSocketTransport(
            aes_key=b"16byteslongkey!!",
            mode="client",
            uri="ws://192.168.0.10:8765",
            device_id=1
        )
        await client.connect()

        resp = await client.handshake({"foo": "bar"})
        print("Handshake response:", resp)

        resp2 = await client.push([{"cmd": 1}], "deadbeef")
        print("Push response:", resp2)

        resp3 = await client.pull("2025-05-20T00:00:00Z")
        print("Pull response:", resp3)

        await client.close()
        await asyncio.Future()

    asyncio.run(run())