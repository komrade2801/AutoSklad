import logging
import threading
# import traceback
# import urllib
from datetime import datetime
from urllib.error import HTTPError
# from urllib.parse import urlencode

import requests
import hmac
import hashlib
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from typing import Optional, Dict, Any

from urllib3.exceptions import MaxRetryError, NewConnectionError

# from aiohttp import payload_type

from dbSync.Logic_v2.JSONSchemaValidator import JSONSchemaValidator

try:
    from options import PUSH_HTTP_TIMEOUT
except ImportError:
    PUSH_HTTP_TIMEOUT = 120

logger = logging.getLogger(__name__)


def serializer(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")


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
            Port=""
    ):
        self.port = Port
        self.device_id = device_id
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.hmac_secret = hmac_secret
        self.aes_key = aes_key
        self.validator = validator

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
        print(f'[ПОТОК][{threading.current_thread().name}][TransportService][_decrypt] секретный ключ: {self.aes_key}[{datetime.now()}]')
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

        resp = None

        try:
            resp = requests.post(url, data=body, headers=headers)
            resp.raise_for_status()

            print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_schema] Отправка схемы. [{datetime.now()}]')

            data = resp.content

            if self.aes_key:
                data = self._decrypt(data)

            result = json.loads(data)

            # 2) Проверяем ответ по новой схеме handshake_response
            self.validator.validate(result, 'handshake_response')
            print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_schema] Проверка схемы. [{datetime.now()}]')
            return result

        except requests.RequestException as e:
            print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_schema] Ошибка при отправке схемы. [{datetime.now()}]')
            print(f"Ошибка при отправке схемы: {e}")
            return {"mapping": "", "schema_hash": ""}

        except ConnectionError as ce:
            logger.error(f"Connection refused when calling {url}: {ce}")
            # Тут можно либо пробросить дальше, либо вернуть заглушку:
            raise RuntimeError(f"Не могу подключиться к серверу синхронизации ({url})")

        except HTTPError as he:
            logger.error(f"HTTP error {resp.status_code} at {url}: {he}")
            raise

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
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шаг 1: проверяем device_id. [{datetime.now()}]")  # лог текущего этапа и потока :contentReference[oaicite:2]{index=2}
        device_id = self.device_id
        if device_id is None:
            # Попробуем подпхватить его из тела
            print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] device_id равен None, пытаемся взять из payload. [{datetime.now()}]")  # лог попытки получить device_id из payload :contentReference[oaicite:3]{index=3}
            if "device" not in payload:
                raise ValueError("Neither self.device_id nor payload['device'] is set")
            device_id = payload["device"]
            if device_id is None:
                raise ValueError("payload['device'] is None")
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Используем device_id = {device_id}. [{datetime.now()}]")  # лог окончательного выбора device_id :contentReference[oaicite:4]{index=4}

        # ——————————————————————————————————————————————————————————————————————
        # 2) Сериализуем и шифруем тело
        ...# printf"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шаг 2: сериализуем payload. [{datetime.now()}]")  # начало сериализации :contentReference[oaicite:5]{index=5}
        body = json.dumps(payload, default=serializer).encode("utf-8")
        if self.aes_key:
            print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шифруем тело AES. [{datetime.now()}]")  # лог выполнения AES-шифрования :contentReference[oaicite:6]{index=6}
            body = self._encrypt(body)
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Тело готово к отправке (после шифрования, если применимо). [{datetime.now()}]")  # тело после шифрования :contentReference[oaicite:7]{index=7}

        # ——————————————————————————————————————————————————————————————————————
        # 3) Готовим заголовки, HMAC-подпись, если нужно
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шаг 3: формируем заголовки. [{datetime.now()}]")  # начало формирования заголовков :contentReference[oaicite:8]{index=8}
        headers = self._get_headers()
        if self.hmac_secret:
            print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Добавляем HMAC-подпись. [{datetime.now()}]")  # лог добавления подписи :contentReference[oaicite:9]{index=9}
            headers["X-Signature"] = self._sign_hmac(body)
        print( f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Заголовки сформированы: {headers}. [{datetime.now()}]")  # лог итоговых заголовков :contentReference[oaicite:10]{index=10}

        # ——————————————————————————————————————————————————————————————————————
        # 4) Формируем полный URL с query-параметром device=<число>
        #    endpoint уже должен начинаться с "/", например "/sync/push"
        print(  f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шаг 4: формируем URL. [{datetime.now()}]" )  # лог начала формирования URL :contentReference[oaicite:11]{index=11}
        url = f"{self.base_url}:{self.port}{endpoint}?device={device_id}"
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] URL для запроса: {url}. [{datetime.now()}]")  # лог итогового URL :contentReference[oaicite:12]{index=12}

        # ——————————————————————————————————————————————————————————————————————
        # 5) Делаем HTTP-запрос (POST) с увеличенным таймаутом для больших батчей
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шаг 5: отправляем POST-запрос (timeout={PUSH_HTTP_TIMEOUT}s). [{datetime.now()}]")  # лог отправки запроса :contentReference[oaicite:13]{index=13}
        resp = requests.post(url, data=body, headers=headers, timeout=PUSH_HTTP_TIMEOUT)
        try:
            resp.raise_for_status()
        except Exception:
            print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Ошибка HTTP: {resp.status_code} / {resp.text}. [{datetime.now()}]")  # лог HTTP-ошибки и тело ответа :contentReference[oaicite:14]{index=14}
            raise

        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Ответ получен с кодом {resp.status_code}. [{datetime.now()}]")  # лог успешного ответа :contentReference[oaicite:15]{index=15}

        # ——————————————————————————————————————————————————————————————————————
        # 6) Получаем ответ, расшифровываем (если нужно) и валидируем JSON
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Шаг 6: получаем и обрабатываем тело ответа. [{datetime.now()}]")  # лог начала обработки ответа :contentReference[oaicite:16]{index=16}
        content = resp.content
        if self.aes_key:
            print(f'[…] Дешифруем ответ AES. [{datetime.now()}]')
            try:
                content = self._decrypt(content)
            except ValueError:
                # Если первые 16 байт — не IV, значит это просто JSON
                print(f'[…] Не получилось дешифровать, считаем, что это чистый JSON. [{datetime.now()}]')
                # content остаётся как есть

        result = json.loads(content)
        # Проверяем схему ответа (например, "push_response")
        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Выполняем валидацию ответа. [{datetime.now()}]")  # лог валидации JSON :contentReference[oaicite:18]{index=18}
        self.validator.validate(result, "push_response")

        print(f"[ПОТОК][{threading.current_thread().name}][TransportService][send_push] Успешно завершили send_push. [{datetime.now()}]")  # завершающий лог метода :contentReference[oaicite:19]{index=19}
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
            print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_pull] Запрос команд. [{datetime.now()}]')
        except requests.RequestException as e:
            print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_pull] Ошибка при получении данных. [{datetime.now()}]')
            # print(f"Ошибка при получении данных: {e}, подробнее: {traceback.format_exc()}")
            raise
        except ConnectionError as ce:
            logger.error(f"[TransportService] Connection refused при GET {url}?{params}: {ce}")
            # Преобразуем в своё исключение или возвращаем заглушку
            raise RuntimeError(f"Сервер синхронизации недоступен ({self.base_url}:{self.port})")
        except HTTPError as he:
            logger.error(f"[TransportService] HTTP {resp.status_code} при GET {url}: {he}")
            raise

        content = resp.content
        if self.aes_key:
            try:
                content = self._decrypt(content)
                print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_pull] Декодирование. [{datetime.now()}]')
            except ValueError:  # или более узкий Crypto.Util.Padding.PaddingError
                print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_pull] Декодирование. [{datetime.now()}]')
                # значит пришёл просто JSON, оставляем content как есть
                pass

        data = json.loads(content)
        self.validator.validate(data, 'pull_response')
        print(f'[ПОТОК][{threading.current_thread().name}][TransportService][send_pull] Получение команд {data}. [{datetime.now()}]')
        return data
