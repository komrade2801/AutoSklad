import logging
import threading
import traceback
import urllib
from datetime import datetime
from urllib.parse import urlencode

import requests
import hmac
import hashlib
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from typing import Optional, Dict, Any

# from aiohttp import payload_type

from .JSONSchemaValidator import JSONSchemaValidator

logger = logging.getLogger(__name__)


class TransportService:
    """
    Сервис транспортного обмена между локальной системой и удалённым сервером.

    Отвечает за:
    - Отправку и получение HTTP(S)-запросов.
    - Авторизацию через JWT.
    - Подпись и проверку целостности данных с использованием HMAC.
    - Шифрование и дешифрование данных с использованием AES.
    - Валидацию JSON-данных по схемам с использованием JSONSchemaValidator.

    Используется в классе SyncProcessor для:
    - Отправки команд на сервер (send_push).
    - Получения команд с сервера (send_pull).
    - Инициализации обмена через отправку схемы (send_schema).

    Параметры:
    - base_url (str): Базовый URL сервера.
    - jwt_token (Optional[str]): JWT-токен для авторизации.
    - hmac_secret (Optional[bytes]): Секретный ключ для HMAC-подписи.
    - aes_key (Optional[bytes]): Ключ для AES-шифрования (16/24/32 байта).
    """

    def __init__(
            self,
            base_url: str,
            jwt_token: Optional[str] = None,
            hmac_secret: Optional[bytes] = None,
            aes_key: Optional[bytes] = None,
            validator=JSONSchemaValidator(),
            device_id=None,
            port="",
            push_http_timeout: int = 120
        ):
        self.port = port
        self.device_id = device_id
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.hmac_secret = hmac_secret
        self.aes_key = aes_key
        self.validator = validator
        self.push_http_timeout = push_http_timeout

    def _get_headers(self) -> Dict[str, str]:
        """
        Формирует HTTP-заголовки для запроса.

        Возвращает:
            dict: Словарь с заголовками.
        """
        headers = {'Content-Type': 'application/json'}
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        return headers

    def _sign_hmac(self, payload: bytes) -> str:
        """
        Создаёт HMAC-подпись для переданных данных.

        Параметры:
            payload (bytes): Данные для подписи.

        Возвращает:
            str: HMAC-подпись в шестнадцатеричном формате.
        """
        if not self.hmac_secret:
            raise ValueError("HMAC secret is not set.")
        signature = hmac.new(self.hmac_secret, payload, hashlib.sha256).hexdigest()
        return signature

    def _encrypt(self, plaintext: bytes) -> bytes:
        """
        Шифрует данные с использованием AES в режиме CBC.

        Параметры:
            plaintext (bytes): Открытые данные.

        Возвращает:
            bytes: IV (16 байт) + зашифрованные данные.
        """
        if not self.aes_key:
            raise ValueError("AES key is not set.")
        iv = os.urandom(16)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
        return iv + ciphertext

    def _decrypt(self, ciphertext: bytes) -> bytes:
        """
        Расшифровывает данные, зашифрованные методом _encrypt.

        Параметры:
            ciphertext (bytes): IV (16 байт) + зашифрованные данные.

        Возвращает:
            bytes: Расшифрованные данные.
        """
        logger.debug("[TransportService][_decrypt] Вызов дешифрования (ключ не логируется).")
        if not self.aes_key:
            raise ValueError("AES key is not set.")
        iv = ciphertext[:16]
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext[16:]), AES.block_size)
        return plaintext

    def send_schema(self, endpoint: str, schema_json: Dict[str, Any], device: int) -> Dict[str, Any]:
        """
        Отправляет JSON-схему на сервер и получает ответ.

        Параметры:
            endpoint (str): Путь к API-методу.
            schema_json (dict): JSON-схема для отправки.

        Возвращает:
            dict: Ответ от сервера.
        """

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
            logger.info("[TransportService][send_schema] Отправка схемы.")

        except requests.RequestException as e:
            logger.exception("[TransportService][send_schema] Ошибка при отправке схемы: %s", e)
            raise

        data = resp.content
        if self.aes_key:
            data = self._decrypt(data)

        result = json.loads(data)

        # 2) Проверяем ответ по новой схеме handshake_response
        self.validator.validate(result, 'handshake_response')
        logger.debug("[TransportService][send_schema] Проверка схемы.")
        return result

    def send_push(self, endpoint: str, payload: dict[str, any]) -> dict[str, any]:
        """
        Отправляет пакет команд на сервер, сохраняя всю логику шифрования,
        подписи и валидации ответа, но при этом позволяет «подхватить» device_id
        из переданного payload, если self.device_id == None.

        :param endpoint: путь к API-методу (например, "/sync/push")
        :param payload:  словарь с ключами: "device", "schema_hash", "commands" и т.п.
        :return:         распарсенный и валидированный JSON-ответ сервера
        """
        # ——————————————————————————————————————————————————————————————————————
        # 1) Определяем, какой device_id использовать в query:
        #    - если self.device_id не None, берём его
        #    - иначе пытаемся взять из payload["device"]
        #
        logger.debug("[TransportService][send_push] Шаг 1: проверяем device_id.")
        device_id = self.device_id
        if device_id is None:
            logger.debug("[TransportService][send_push] device_id равен None, берём из payload.")
            if "device" not in payload:
                raise ValueError("Neither self.device_id nor payload['device'] is set")
            device_id = payload["device"]
            if device_id is None:
                raise ValueError("payload['device'] is None")
        logger.debug("[TransportService][send_push] Используем device_id = %s.", device_id)

        # ——————————————————————————————————————————————————————————————————————
        # 2) Сериализуем и шифруем тело
        logger.debug("[TransportService][send_push] Шаг 2: сериализуем payload.")
        body = json.dumps(payload, default=str).encode("utf-8")
        if self.aes_key:
            logger.debug("[TransportService][send_push] Шифруем тело AES.")
            body = self._encrypt(body)
        logger.debug("[TransportService][send_push] Тело готово к отправке.")

        # ——————————————————————————————————————————————————————————————————————
        # 3) Готовим заголовки, HMAC-подпись, если нужно
        logger.debug("[TransportService][send_push] Шаг 3: формируем заголовки.")
        headers = self._get_headers()
        if self.hmac_secret:
            logger.debug("[TransportService][send_push] Добавляем HMAC-подпись.")
            headers["X-Signature"] = self._sign_hmac(body)
        logger.debug("[TransportService][send_push] Заголовки сформированы.")

        # ——————————————————————————————————————————————————————————————————————
        # 4) Формируем полный URL
        logger.debug("[TransportService][send_push] Шаг 4: формируем URL.")
        url = f"{self.base_url}:{self.port}{endpoint}?device={device_id}"
        logger.debug("[TransportService][send_push] URL: %s", url)

        # ——————————————————————————————————————————————————————————————————————
        # 5) Делаем HTTP-запрос (POST)
        logger.debug("[TransportService][send_push] Шаг 5: POST (timeout=%ss).", self.push_http_timeout)
        resp = requests.post(url, data=body, headers=headers, timeout=self.push_http_timeout)
        try:
            resp.raise_for_status()
        except Exception:
            logger.error("[TransportService][send_push] Ошибка HTTP: %s / %s", resp.status_code, resp.text[:200] if resp.text else "")
            raise

        logger.info("[TransportService][send_push] Ответ получен с кодом %s.", resp.status_code)

        # ——————————————————————————————————————————————————————————————————————
        # 6) Получаем ответ, расшифровываем (если нужно) и валидируем JSON
        logger.debug("[TransportService][send_push] Шаг 6: обрабатываем тело ответа.")
        content = resp.content
        if self.aes_key:
            logger.debug("[TransportService][send_push] Дешифруем ответ AES.")
            try:
                content = self._decrypt(content)
            except ValueError:
                logger.debug("[TransportService][send_push] Не удалось дешифровать, считаем чистый JSON.")
                pass

        result = json.loads(content)
        logger.debug("[TransportService][send_push] Валидация ответа.")
        self.validator.validate(result, "push_response")

        logger.info("[TransportService][send_push] Успешно завершили send_push.")
        return result

    def send_pull(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запрашивает новые команды с сервера.

        Параметры:
            endpoint (str): Путь к API-методу.
            params (dict): Параметры запроса.

        Возвращает:
            dict: Ответ от сервера.
        """

        url = f"{self.base_url}:{self.port}{endpoint}"
        headers = self._get_headers()

        try:
            resp = requests.get(url, params=params, headers=headers)
            resp.raise_for_status()
            logger.info("[TransportService][send_pull] Запрос команд.")
        except requests.RequestException as e:
            logger.exception("[TransportService][send_pull] Ошибка при получении данных: %s", e)
            raise

        content = resp.content
        if self.aes_key:
            try:
                content = self._decrypt(content)
                logger.debug("[TransportService][send_pull] Декодирование.")
            except ValueError:  # или более узкий Crypto.Util.Padding.PaddingError
                logger.debug("[TransportService][send_pull] Декодирование.")
                # значит пришёл просто JSON, оставляем content как есть
                pass

        data = json.loads(content)
        self.validator.validate(data, 'pull_response')
        logger.debug("[TransportService][send_pull] Получение команд (data keys: %s).", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
        return data

#  Список изменений в обновлённой версии класса
# Безопасность:
# Заменено использование фиксированного IV (b'\x00' * 16) на случайно генерируемый IV с использованием os.urandom(16).
# Добавлена проверка наличия ключей aes_key и hmac_secret перед их использованием.
# Stack Overflow
# Логирование:
# Добавлены логгеры для отслеживания ошибок при отправке и получении данных.
# Документация:
# Добавлены подробные докстринги для класса и всех методов, описывающие их назначение, параметры и возвращаемые значения.
#  Связь с другими классами
# SyncProcessor:
# Использует TransportService для обмена данными с сервером.
# Методы send_push, send_pull и send_schema вызываются из SyncProcessor для отправки и получения данных.
# JSONSchemaValidator:
# Используется для валидации входящих и исходящих JSON-данных по предопределённым схемам.
#  Примеры потоков вызовов
# plaintext
# Копировать
# Редактировать
# SyncProcessor
#     ├── send_push(endpoint, payload)
#     │     └── TransportService.send_push(endpoint, payload)
#     │           ├── validate(payload, 'push_commands')
#     │           └── send_schema(endpoint, payload)
#     │                 ├── validate(schema_json, 'handshake_schema')
#     │                 ├── _encrypt(body)
#     │                 ├── _sign_hmac(body)
#     │                 └── requests.post(...)
#     │                       └── _decrypt(resp.content)
#     │                             └── validate(result, 'handshake_schema')
#     └── send_pull(endpoint, params)
#           └── TransportService.send_pull(endpoint, params)
#                 ├── requests.get(...)
#                 └── _decrypt(resp.content)
#                       └── validate(result, 'pull_response')
#  Предложения по улучшению класса
# Повторные попытки при ошибках (Retry Logic):
# Добавить механизм повторных попыток при сетевых сбоях с использованием экспоненциальной задержки.
# Можно использовать библиотеку tenacity для реализации этой функциональности.
# Асинхронность:
# Переписать методы на асинхронные с использованием aiohttp для улучшения производительности при большом количестве запросов.
# Инкапсуляция криптографических операций:
# Вынести методы _encrypt, _decrypt и _sign_hmac в отдельный класс CryptoHelper для улучшения читаемости и повторного использования кода.
# Гибкость валидации схем:
# Передавать схему в метод validate как аргумент, а не использовать жёстко заданные имена схем.
# Интеграция с системами мониторинга:
# Добавить метрики для отправки в Prometheus, такие как время выполнения методов, количество успеш
