# client_ws.py
import asyncio
import json
import os
import hashlib
import time
from typing import Any, Dict
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

AES_KEY = b"16byteslongkey!!"

class WSClient:
    def __init__(self, uri: str, device: int):
        self.uri = f"{uri}/sync/ws?device={device}"
        self.aes_key = AES_KEY
        self.ws = None

    async def connect(self):
        self.ws = await websockets.connect(self.uri)

    async def send(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        # сериализуем и шифруем
        data = json.dumps(msg).encode("utf-8")
        iv = os.urandom(16)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        payload = iv + cipher.encrypt(pad(data, AES.block_size))
        await self.ws.send(payload)

        # ждём ответ (bytes)
        raw = await self.ws.recv()
        iv2, ct2 = raw[:16], raw[16:]
        cipher2 = AES.new(self.aes_key, AES.MODE_CBC, iv2)
        plain = unpad(cipher2.decrypt(ct2), AES.block_size)
        return json.loads(plain.decode("utf-8"))

    async def handshake(self, schema: dict) -> dict:
        return await self.send({"type": "handshake", "payload": schema})

    async def push(self, commands: list, schema_hash: str) -> dict:
        return await self.send({
            "type": "push",
            "payload": commands,
            "hash": schema_hash
        })

    async def pull(self, since: str) -> dict:
        return await self.send({
            "type": "pull",
            "payload": {"since": since},
            "hash": ""
        })

    async def close(self):
        await self.ws.close()

# пример использования
async def main():
    client = WSClient("ws://192.168.101.154:8765", device=1)

    while True:
        try:
            await client.connect()
            break
        except:
            print("удалённый компьютер не ответил")
            time.sleep(10)


    # handshake
    schema = {"foo": "bar"}
    resp = await client.handshake(schema)
    print("Handshake:", resp)

    # push
    resp2 = await client.push([{"cmd":1}], "hash123")
    print("Push:", resp2)

    # pull
    resp3 = await client.pull("2025-05-20T00:00:00Z")
    print("Pull:", resp3)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
