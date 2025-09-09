from __future__ import annotations
import hashlib
import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError
from typing import List  # , Optional, Dict, Any
from fastapi.responses import Response
from fastapi import HTTPException, Request, Query, FastAPI
from fastapi.concurrency import run_in_threadpool
from queue import Queue, Empty
from typing import Dict, Any, Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from requests import HTTPError
from starlette.responses import JSONResponse

# from anyio import to_thread  # для запуска синхронного get() в фоне

from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES
from dbSync.Logic_v2.JSONSchemaValidator import JSONSchemaValidator
logger = logging.getLogger(__name__)

log = logging.getLogger("sync.handshake")
sync_router = FastAPI(debug=True)

# Создаём единственный валидатор при импорте модуля
json_validator = JSONSchemaValidator()
cfg = json.loads((Path(__file__).parent.parent.parent / "config.json").read_text(encoding="utf-8"))


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

# ----------------
# Pydantic-модели
# ----------------
class CommandItem(BaseModel):
    id: str
    table: str
    operation: str
    data: Dict[str, Any]

# class PushPayload(BaseModel):
#     schema_hash: str
#     commands: List[CommandItem]
#
# class PushResponse(BaseModel):
#     statuses: List[Dict[str, Any]]


# ----------------
# Заглушки для AES-декодера и валидатора
# ----------------
class AESDecryptor:
    def __init__(self, aes_key: bytes):
        if not aes_key:
            raise ValueError("Для расшифровки необходимо предоставить ключ AES.")
        self.aes_key = aes_key

    def decrypt(self, data: bytes) -> bytes:
        """
        Расшифровывает данные, закодированные TransportService._encrypt:
          16 байт IV + ciphertext (с паддингом).
        Возвращает оригинальный plaintext (без паддинга).
        """
        # 1) Извлекаем первые 16 байт как IV
        if len(data) < 16:
            raise ValueError("Данные слишком короткие, чтобы содержать действительный IV и зашифрованный текст..")
        iv = data[:16]
        ciphertext = data[16:]
        # 2) Создаём AES-CBC-дешифратор
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        padded_plaintext = cipher.decrypt(ciphertext)
        # 3) Убираем PKCS#7/PKCS#5 паддинг
        try:
            plaintext = unpad(padded_plaintext, AES.block_size)
        except ValueError as e:
            raise ValueError(f"Ошибка распаковки AES: {e}")
        return plaintext



@sync_router.post("/push", response_model=PushResponse)
async def api_sync_push(device: int, request: Request):
    """
    Универсальный эндпоинт /sync/push?device=<int>, который:
      • Принимает чистый JSON либо зашифрованные байты (AES).
      • Пытается сначала json.loads(raw), иначе AES‐decrypt → json.loads.
      • Валидирует через JSONSchemaValidator(schema_name='push_commands').
      • Кладёт команды в очередь, ждёт ответ и возвращает его.
    """

    print(f"[{threading.current_thread().name}][router] /push?device={device} @ {datetime.now()}")

    # 1. Считываем тело
    raw_body = await request.body()
    print(f"[{threading.current_thread().name}][router] длина необработанных байтов={len(raw_body)} @ {datetime.now()}")

    # 2. Парсим JSON или AES→JSON
    parsed = None
    try:
        parsed = json.loads(raw_body.decode("utf-8"))
        print(f"[{threading.current_thread().name}][router] Простой анализ JSON: {parsed} @ {datetime.now()}")
    except Exception:
        try:
            aes_key = cfg["server"]["aes"].encode("utf-8")
            decrypted = AESDecryptor(aes_key).decrypt(raw_body)
            print(f"[{threading.current_thread().name}][router] Расшифрованная длина в AES={len(decrypted)} @ {datetime.now()}")
            parsed = json.loads(decrypted.decode("utf-8"))
            print(f"[{threading.current_thread().name}][router] JSON после AES: {parsed} @ {datetime.now()}")
        except Exception as ex:
            print(f"[{threading.current_thread().name}][router] Ошибка анализа (JSON/AES): {ex} @ {datetime.now()}")
            raise HTTPException(400, "Невозможно проанализировать тело как JSON или расшифровать AES")

    # 3. Схематическая валидация
    try:
        schemas = json_validator.available_schemas()
        print(f"[{threading.current_thread().name}][json_validator] schemas: {schemas}")
        json_validator.validate(parsed, "push_commands")
        print(f"[{threading.current_thread().name}][router] JSONSchemaValidator OK for 'push_commands' @ {datetime.now()}")
    except ValidationError as ve:
        print(f"[{threading.current_thread().name}][router] JSONSchema провалена: {ve} @ {datetime.now()}")
        raise HTTPException(422, f"Wrong PUSH payload (schema): {ve}")
    except RuntimeError as re:
        print(f"[{threading.current_thread().name}][router] Ошибка схемы: {re} @ {datetime.now()}")
        raise HTTPException(500, f"Ошибка схемы: {re}")

    # 4. Pydantic-парсинг
    try:
        payload = PushPayload(**parsed)
        print(f"[{threading.current_thread().name}][router] Pydantic OK: schema_hash={payload.schema_hash}, commands={len(payload.commands)} @ {datetime.now()}")
    except ValidationError as ve:
        print(f"[{threading.current_thread().name}][router] Pydantic failed: {ve} @ {datetime.now()}")
        raise HTTPException(422, f"Wrong PUSH payload: {ve}")

    # 5. Кладём в очередь фонового runner-а
    queue_in = INBOUND_QUEUES.get(device)
    print(f"[{threading.current_thread().name}][router] queue lookup device={device} → {queue_in} @ {datetime.now()}")
    if not queue_in:
        print(f"[{threading.current_thread().name}][router] Нет потока синхронизации для устройства={device} @ {datetime.now()}")
        raise HTTPException(404, f"Нет потока синхронизации для устройства {device}")

    reply_queue: Queue = Queue()
    queue_in.put({
        "type": "push",
        "payload": payload.commands,
        "hash": payload.schema_hash,
        "reply_queue": reply_queue
    })
    print(f"[{threading.current_thread().name}][router] Поставленная в очередь задача для устройства={device} @ {datetime.now()}")

    # 6. Ждём исключительно process_push (до 10 сек)
    try:
        print(f"[{threading.current_thread().name}][router] Waiting for process_push (10s) @ {datetime.now()}")
        statuses = await run_in_threadpool(lambda: reply_queue.get(timeout=10))
        print(f"[{threading.current_thread().name}][router] Получил статусы: {statuses} @ {datetime.now()}")
    except Empty:
        print(f"[{threading.current_thread().name}][router] process_push timeout @ {datetime.now()}")
        raise HTTPException(504, "Время обработки push-запроса истекло")

    # 7. Мгновенный ответ клиенту
    return JSONResponse(content={"statuses": statuses})


@sync_router.get("/pull", response_model=PullResponseModel)
def api_sync_pull(device: int, since: str = ""):
    print(f'[ПОТОК][{threading.current_thread().name}][router] Берем очередь фонового потока для {device} ')
    queue_in = INBOUND_QUEUES.get(device)
    if not queue_in:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Нет очереди')
        raise HTTPException(404, f"Нет потока синхронизации для устройства {device}")
    reply_queue = Queue()
    print(f'[ПОТОК][{threading.current_thread().name}][router] Отправляем задачу в очередь фонового потока для {device}. since={since}. [{datetime.now()}]')
    queue_in.put({
        "type": "pull",
        "device": device,
        "since": since,
        "hash": "",
        "reply_queue": reply_queue
    })

    try:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Ждём ответа {device}. [{datetime.now()}]')
        response = reply_queue.get(timeout=10)
        print(f'[ПОТОК][{threading.current_thread().name}][router] ответ получен')
    except Empty:
        print(f'[ПОТОК][{threading.current_thread().name}][router] пустая очередь')
        return PullResponseModel(schema_hash="", commands=[])

    if isinstance(response, dict) and response.get("error"):
        print(f'[ПОТОК][{threading.current_thread().name}][router] error: {response["error"]}. [{datetime.now()}]')
        raise HTTPException(500, response["error"])

    return PullResponseModel(**response)


@sync_router.post("/handshake")
async def api_sync_handshake(
        request: Request,
        device: int = Query(..., description="Device ID"),
) -> Response:
    """
    Асинхронный endpoint для Handshake с дешифрованием тела.
    Клиент шлет AES(CBC+PKCS7)-зашифрованный JSON, мы его расшифровываем,
    кладем задачу в очередь фонового потока и ждем результата,
    затем шифруем ответ тем же ключом и возвращаем байты.
    """
    print(f'[ПОТОК][{threading.current_thread().name}][router] Берем очередь фонового потока для {device} . [{datetime.now()}]')
    queue_in = INBOUND_QUEUES.get(device)
    if not queue_in:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Нет очереди. [{datetime.now()}]')
        raise HTTPException(404, f"Нет потока синхронизации для устройства {device}")

    # 1) Считываем тело запроса
    raw_body = await request.body()
    if not raw_body:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Пустой запрос. [{datetime.now()}]')
        raise HTTPException(400, "Пустое тело запроса")

    # 2) Дешифруем AES-CBC + PKCS7
    try:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Дешифруем AES-CBC + PKCS7. [{datetime.now()}]')
        iv = raw_body[:16]                                           # CHANGED: сохранили IV из тела
        ciphertext = raw_body[16:]                                   # CHANGED: отдельно взяли ciphertext
        aes_key = cfg["server"]["aes"].encode("utf-8")               # CHANGED: получили ключ
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)  # CHANGED: расшифровка ciphertext
    except Exception:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Ошибка дешифровки. [{datetime.now()}]')
        log.exception("Failed to decrypt handshake payload")
        raise HTTPException(400, "Неверно зашифровано payload")

    # 3) Парсим JSON
    try:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Парсим JSON. [{datetime.now()}]')
        src_schema = json.loads(decrypted.decode("utf-8"))
        if not isinstance(src_schema, dict):
            raise ValueError("Схема должна быть объектом JSON")
    except Exception:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Ошибка парсинга JSON. [{datetime.now()}]')
        log.exception("Не удалось проанализировать схему JSON")
        raise HTTPException(400, "Неверный формат схемы JSON")

    # 4) Считаем хеш и кладем задачу в очередь
    print(f'[ПОТОК][{threading.current_thread().name}][router] Считаем хеш и кладем задачу в очередь [{datetime.now()}]')
    schema_bytes = json.dumps(src_schema, sort_keys=True).encode("utf-8")
    client_schema_hash = hashlib.sha256(schema_bytes).hexdigest()

    reply_queue: Queue = Queue()
    print(f'[ПОТОК][{threading.current_thread().name}][router] Кладем задачу в очередь фонового потока. [{datetime.now()}]')
    queue_in.put({
        "type": "handshake",
        "payload": src_schema,
        "hash": client_schema_hash,
        "reply_queue": reply_queue
    })

    print(f'[ПОТОК][{threading.current_thread().name}][router] Задача кладена в очередь фонового потока. [{datetime.now()}]')

    # 5) Ждем ответа из фонового потока
    try:
        result = reply_queue.get(timeout=10)
        print(f'[ПОТОК][{threading.current_thread().name}][router] Ответ получен [{datetime.now()}]')
    except Empty:
        print(f'[ПОТОК][{threading.current_thread().name}][router] Ответ не получен [{datetime.now()}]')
        raise HTTPException(504, "Время обработки рукопожатия истекло")

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(500, result["error"])

    # 6) Шифруем результат и возвращаем клиенту
    print(f'[ПОТОК][{threading.current_thread().name}][router] Шифруем результат и отдаем клиенту [{datetime.now()}]')
    plaintext = json.dumps(result).encode("utf-8")
    iv2 = os.urandom(16)
    aes_key = cfg["server"]["aes"].encode("utf-8")  # используем тот же ключ
    cipher2 = AES.new(aes_key, AES.MODE_CBC, iv2)
    ciphertext2 = iv2 + cipher2.encrypt(pad(plaintext, AES.block_size))
    print(f'[ПОТОК][{threading.current_thread().name}][router] Ответ отправлен клиенту [{datetime.now()}]')
    return Response(
        content=ciphertext2,
        media_type="application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )