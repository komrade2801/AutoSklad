import threading
import json
from functools import wraps
import logging

import dbSync
from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES
from dbSync.Logic_v2.DataTransformer import DataTransformer

logger = logging.getLogger(__name__)
log = logging.getLogger("sync.decorator")

# Для каждого device храним (last_payload_key, last_result)
# _state: dict[int, tuple[str, any]] = {}
_state = {}
_lock = threading.Lock()

# создайте и настройте глобальный трансформер где-нибудь в инициализации приложения
_global_transformer = DataTransformer()  # <-- зарегистрируйте в нём ваши правила


def get_global_transformer() -> DataTransformer:
    return _global_transformer


def sync_aware(func):
    """
    Декоратор для CRUD-методов:
      – вычисляет ключ payload_key (на основе payload['id'] или всего payload JSON)
      – если payload_key == предыдущему для этого device_id:
          • НЕ вызывает func
          • сразу возвращает last_result
      – иначе:
          • валидирует payload
          • вызывает func → получает result
          • запоминает (payload_key, result)
          • кладёт команду в очередь
          • возвращает result
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        table_name = getattr(self.model, "__tablename__", self.model.__name__)
        method_name = func.__name__
        device_id = getattr(self, "device_id", 1)

        if getattr(dbSync, "init_db", False):
            print(f'[ПОТОК][{threading.current_thread().name}][decorators][wraps] '
                  f'обработали БЕЗ синхронизации. func: {method_name}, table: {table_name}, '
                  f'args: {args}, kwargs: {kwargs}')
            return func(self, *args, **kwargs)

        # Сборка payload
        if kwargs:
            payload = dict(kwargs)
        else:
            try:
                cols = [c.name for c in self.model.__table__.columns]
                payload = {col: val for col, val in zip(cols, args)}
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][decorators][wraps] '
                      f'Ошибка payload сборки: {e}. func: {method_name}, table: {table_name}, '
                      f'args: {args}, kwargs: {kwargs}')
                payload = {}

        record_id = payload.get("id") or payload.get("index") or payload.get("number")
        payload_key = f"id:{record_id}" if record_id is not None else json.dumps(payload, sort_keys=True)

        dedup_key = (table_name, method_name, payload_key)

        with _lock:
            device_state = _state.get(device_id, {})
            if dedup_key in device_state:
                print(f'[ПОТОК][{threading.current_thread().name}][decorators][wraps] '
                      f'Вышли без исполнения операции. func: {method_name}, table: {table_name}, '
                      f'args: {args}, kwargs: {kwargs}')
                return device_state[dedup_key]

        # Валидация
        transformer = get_global_transformer()
        if not transformer.validate(table_name, payload):
            raise ValueError(f"Validation failed for table '{table_name}' with payload: {payload}")

        try:
            print(f'[ПОТОК][{threading.current_thread().name}][decorators][wraps] '
                  f'Запустили синхронизацию. func: {method_name}, table: {table_name}, '
                  f'args: {args}, kwargs: {kwargs}')
            result = func(self, *args, **kwargs)
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][decorators][wraps] '
                  f'Ошибка вызова func: {e}. func: {method_name}, table: {table_name}, '
                  f'args: {args}, kwargs: {kwargs}')
            raise

        with _lock:
            if device_id not in _state:
                _state[device_id] = {}
            _state[device_id][dedup_key] = result

        queue_in = INBOUND_QUEUES.get(device_id)
        if queue_in:
            queue_in.put({
                "type": "local",
                "table": table_name,
                "operation": method_name,
                "data": payload,
            })

        return result

    return wrapper