from __future__ import annotations
import hashlib
import json
import logging
import os
import threading
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any, Optional
from fastapi.responses import Response
from fastapi import HTTPException, Request, Query, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from queue import Queue, Empty
from starlette.responses import JSONResponse

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES
from dbSync.Logic_v2.JSONSchemaValidator import JSONSchemaValidator
from options import AES_KEY

logger = logging.getLogger(__name__)
log = logging.getLogger("sync.handshake")
sync_router = FastAPI(debug=True)

json_validator = JSONSchemaValidator()
wait_background_answer = 50


# --- Pydantic-модели ---
class PushPayload(BaseModel):
    device: int
    schema_hash: str
    commands: List[Dict[str, Any]]


class StatusEntry(BaseModel):
    id: str
    status: str
    error: Optional[str] = None


class PushResponse(BaseModel):
    statuses: List[StatusEntry]


class PullResponseModel(BaseModel):
    schema_hash: str
    commands: List[Dict[str, Any]]


class CommandItem(BaseModel):
    id: str
    table: str
    operation: str
    data: Dict[str, Any]


class AESDecryptor:
    def __init__(self, aes_key: bytes):
        if not aes_key:
            raise ValueError("AES Для расшифровки необходимо предоставить ключ.")
        self.aes_key = aes_key

    def decrypt(self, data: bytes) -> bytes:
        if len(data) < 16:
            raise ValueError("Данные слишком короткие, чтобы содержать действительный IV и зашифрованный текст..")
        iv = data[:16]
        ciphertext = data[16:]
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        padded_plaintext = cipher.decrypt(ciphertext)
        try:
            plaintext = unpad(padded_plaintext, AES.block_size)
        except ValueError as e:
            raise ValueError(f"AES ошибка распаковки: {e}")
        return plaintext


# --- Общие функции обработки запросов ---
async def process_push_request(device: int, raw_body: bytes) -> Dict[str, Any]:
    """Обрабатывает логику push-запроса."""
    parsed = None
    try:
        parsed = json.loads(raw_body.decode("utf-8"))
    except Exception:
        try:
            decrypted = AESDecryptor(AES_KEY).decrypt(raw_body)
            parsed = json.loads(decrypted.decode("utf-8"))
        except Exception:
            raise HTTPException(400, "Невозможно проанализировать тело как JSON или расшифровать AES")

    try:
        json_validator.validate(parsed, "push_commands")
    except ValidationError as ve:
        raise HTTPException(422, f"Неправильный PUSH payload (schema): {ve}")
    except RuntimeError as re:
        raise HTTPException(500, f"Ошибка схемы: {re}")

    try:
        payload = PushPayload(**parsed)
    except ValidationError as ve:
        raise HTTPException(422, f"Неправильная PUSH payload: {ve}")

    queue_in = INBOUND_QUEUES.get(device)
    if not queue_in:
        raise HTTPException(404, f"Нет потока синхронизации для устройства {device}")

    reply_queue: Queue = Queue()
    queue_in.put({
        "type": "push",
        "payload": payload.commands,
        "hash": payload.schema_hash,
        "reply_queue": reply_queue
    })

    try:
        statuses = await run_in_threadpool(lambda: reply_queue.get(timeout=wait_background_answer))
        return {"statuses": statuses}
    except Empty:
        raise HTTPException(504, "Время обработки push-запроса истекло")


def process_pull_request(device: int, since: str) -> Dict[str, Any]:
    """Обрабатывает логику pull-запроса."""
    queue_in = INBOUND_QUEUES.get(device)
    if not queue_in:
        raise HTTPException(404, f"No sync thread for device {device}")

    reply_queue = Queue()
    queue_in.put({
        "type": "pull",
        "device": device,
        "since": since,
        "hash": "",
        "reply_queue": reply_queue
    })

    try:
        response = reply_queue.get(timeout=wait_background_answer)
    except Empty:
        return PullResponseModel(schema_hash="", commands=[]).dict()

    if isinstance(response, dict) and response.get("error"):
        raise HTTPException(500, response["error"])

    return PullResponseModel(**response).dict()


async def process_handshake_request(device: int, raw_body: bytes) -> bytes:
    """Обрабатывает логику handshake-запроса."""
    queue_in = INBOUND_QUEUES.get(device)
    if not queue_in:
        raise HTTPException(404, f"Нет потока синхронизации для устройства {device}")

    if not raw_body:
        raise HTTPException(400, "Пустое тело запроса")

    try:
        iv = raw_body[:16]
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(raw_body[16:]), AES.block_size)
    except Exception:
        log.exception("Ошибка дешифровки")
        raise HTTPException(400, "Ошибка дешифровки")

    try:
        src_schema = json.loads(decrypted.decode("utf-8"))
        if not isinstance(src_schema, dict):
            raise ValueError("Схема должна быть объектом JSON")
    except Exception:
        log.exception("Неверный формат схемы JSON")
        raise HTTPException(400, "Неверный формат схемы JSON")

    schema_bytes = json.dumps(src_schema, sort_keys=True).encode("utf-8")
    client_schema_hash = hashlib.sha256(schema_bytes).hexdigest()

    reply_queue: Queue = Queue()
    queue_in.put({
        "type": "handshake",
        "payload": src_schema,
        "hash": client_schema_hash,
        "reply_queue": reply_queue
    })

    try:
        result = await run_in_threadpool(lambda: reply_queue.get(timeout=wait_background_answer))
    except Empty:
        raise HTTPException(504, "Время обработки рукопожатия истекло")

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(500, result["error"])

    plaintext = json.dumps(result).encode("utf-8")
    iv2 = os.urandom(16)
    cipher2 = AES.new(AES_KEY, AES.MODE_CBC, iv2)
    ciphertext = iv2 + cipher2.encrypt(pad(plaintext, AES.block_size))

    return ciphertext


# --- HTTP-эндпоинты (теперь вызывают общие функции) ---
@sync_router.post("/push", response_model=PushResponse)
async def api_sync_push(device: int, request: Request):
    raw_body = await request.body()
    result = await process_push_request(device, raw_body)
    return JSONResponse(content=result)


@sync_router.get("/pull", response_model=PullResponseModel)
def api_sync_pull(device: int, since: str = ""):
    result = process_pull_request(device, since)
    return PullResponseModel(**result)


@sync_router.post("/handshake")
async def api_sync_handshake(request: Request, device: int = Query(..., description="Device ID")) -> Response:
    raw_body = await request.body()
    ciphertext = await process_handshake_request(device, raw_body)
    return Response(
        content=ciphertext,
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


# --- WebSocket-эндпоинт ---
active_connections: Dict[int, WebSocket] = {}


@sync_router.websocket("/ws/sync/{device_id}")
async def websocket_sync_endpoint(websocket: WebSocket, device_id: int):
    await websocket.accept()
    active_connections[device_id] = websocket
    log.info(f"[websocket] New connection from device {device_id}")

    try:
        while True:
            raw_body = await websocket.receive_bytes()
            log.info(f"[websocket] Received message from device {device_id}")

            # Логика дешифрования и определения типа запроса
            try:
                decrypted_bytes = AESDecryptor(AES_KEY).decrypt(raw_body)
                message = json.loads(decrypted_bytes.decode("utf-8"))
                command_type = message.get("type")
            except Exception as e:
                log.error(f"[websocket] Failed to decrypt/parse message: {e}")
                error_response = json.dumps({"error": "Failed to decrypt/parse message"}).encode("utf-8")
                # Шифруем ошибку перед отправкой
                iv_err = os.urandom(16)
                cipher_err = AES.new(AES_KEY, AES.MODE_CBC, iv_err)
                encrypted_err = iv_err + cipher_err.encrypt(pad(error_response, AES.block_size))
                await websocket.send_bytes(encrypted_err)
                continue

            response_data = None
            if command_type == "push":
                # Передаём payload, а не весь raw_body, так как он уже расшифрован
                response_data = await process_push_request(device_id, json.dumps(message).encode("utf-8"))
            elif command_type == "pull":
                since = message.get("since", "")
                response_data = process_pull_request(device_id, since)
            elif command_type == "handshake":
                response_data_raw = await process_handshake_request(device_id, raw_body)
                await websocket.send_bytes(response_data_raw)
                continue  # Handshake уже отправляет зашифрованный ответ, поэтому пропускаем шифрование ниже
            else:
                response_data = {"error": "Unknown command type"}

            # Формируем и шифруем ответ для WebSocket
            if response_data:
                response_data["type"] = f"{command_type}_response"
                plaintext = json.dumps(response_data).encode("utf-8")
                iv_resp = os.urandom(16)
                cipher_resp = AES.new(AES_KEY, AES.MODE_CBC, iv_resp)
                ciphertext = iv_resp + cipher_resp.encrypt(pad(plaintext, AES.block_size))
                await websocket.send_bytes(ciphertext)

    except WebSocketDisconnect:
        log.info(f"[websocket] Connection closed for device {device_id}")
        if device_id in active_connections:
            del active_connections[device_id]
    except Exception as e:
        log.error(f"[websocket] Error in connection for device {device_id}: {e}")
        if device_id in active_connections:
            del active_connections[device_id]