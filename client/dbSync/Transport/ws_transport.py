# ws_transport.py

import asyncio
import json
import os
import hashlib
import logging
from typing import Any, Dict, Optional

import websockets
# from websockets import WebSocketServerProtocol
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES
# Используйте полное имя
WebSocketServerProtocol = websockets.WebSocketServerProtocol
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

    # -------------------
    # Общие крипто-утилиты
    # -------------------
    def _encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(16)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(pad(data, AES.block_size))

    def _decrypt(self, raw: bytes) -> bytes:
        iv, ct = raw[:16], raw[16:]
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size)

    # -----------------------
    # Методы для server-режима
    # -----------------------
    async def _handler(self, ws: WebSocketServerProtocol, path: str):
        """
        Серверный хэндлер: принимает `ws` и `path`, например:
        path == "/sync/ws?device=1"
        """
        # достаём device_id из query-string path
        try:
            _, qs = path.split("?", 1)
            params = dict(pair.split("=", 1) for pair in qs.split("&"))
            device = int(params["device"])
            queue_in = INBOUND_QUEUES[device]
        except Exception:
            logger.error("Не могу разобрать path=%r", path)
            await ws.close(code=1008)
            return

        logger.info("Device %d connected", device)

        try:
            async for raw in ws:
                # 1) дешифруем
                try:
                    plain = self._decrypt(raw)
                except Exception:
                    logger.error("Не смогли расшифровать от %d", device)
                    continue

                msg = json.loads(plain.decode("utf-8"))
                # 2) хешируем для sync-процессора
                h = hashlib.sha256(plain).hexdigest()
                # 3) ставим в очередь runner-а
                reply_q: asyncio.Queue = asyncio.Queue()


                queue_in.put({
                    "type":    msg.get("type", "handshake"),
                    "payload": msg.get("payload", msg),
                    "hash":    h,
                    "reply_queue": reply_q
                })

                # 4) ждём ответ (10 сек)
                try:
                    result = await asyncio.wait_for(reply_q.get(), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning("Timeout ожидания от %d", device)
                    continue

                # 5) шифруем и отправляем обратно
                resp_plain = json.dumps(result).encode("utf-8")
                await ws.send(self._encrypt(resp_plain))

        except websockets.ConnectionClosed:
            logger.info("Device %d disconnected", device)

    async def start_server(self):
        """
        Запустить WebSocket-сервер.
        """

        self.server = await websockets.serve(
            self._handler, self.host, self.port
        )
        logger.info("WS server running on %s:%d", self.host, self.port)

    # ------------------------
    # Методы для client-режима
    # ------------------------
    async def connect(self):
        """
        Подключиться к ws://<uri>/sync/ws?device=<device_id>
        """
        assert self.uri and self.device_id is not None
        url = f"{self.uri}/sync/ws?device={self.device_id}"
        self.ws = await websockets.connect(url)
        logger.info("WS client connected to %s", url)

    async def send(self, msg: Dict[str, Any]) -> Any:
        """
        Универсальный обмен: шифруем msg → отправляем → ждём ответ → дешифруем → возвращаем dict.
        """
        assert self.ws
        data = json.dumps(msg).encode("utf-8")
        await self.ws.send(self._encrypt(data))
        raw = await self.ws.recv()
        plain = self._decrypt(raw)
        return json.loads(plain.decode("utf-8"))

    async def close(self):
        if self.ws:
            await self.ws.close()

    # Удобные оболочки
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


# -------------------------
# Пример использования
# -------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def run():
        # 1) запускаем сервер
        transport = WebSocketTransport(
            aes_key=b"16byteslongkey!!",
            mode="server",
            host="192.168.0.10",
            port=8765
        )
        await transport.start_server()

        # 2) и клиента сразу же
        client = WebSocketTransport(
            aes_key=b"16byteslongkey!!",
            mode="client",
            uri="ws://192.168.0.10:8765",
            device_id=1
        )
        await client.connect()

        # handshake
        resp = await client.handshake({"foo": "bar"})
        print("Handshake response:", resp)

        # push
        resp2 = await client.push([{"cmd": 1}], "deadbeef")
        print("Push response:", resp2)

        # pull
        resp3 = await client.pull("2025-05-20T00:00:00Z")
        print("Pull response:", resp3)

        await client.close()

        # держим сервер живым
        await asyncio.Future()

    asyncio.run(run())
