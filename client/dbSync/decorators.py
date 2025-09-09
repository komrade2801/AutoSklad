import threading
import json
from functools import wraps
import logging
import inspect
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
        # --- Если инициализация БД, просто вызываем метод без логики синхра ---
        if dbSync.init_db:
            table_name  = getattr(self.model, "__tablename__", self.model.__name__)
            method_name = func.__name__
            print(f"[{threading.current_thread().name}][decorators][wraps] "
                  f"обработали БЕЗ синхронизации. func: {method_name}, table: {table_name}, "
                  f"args: {args}, kwargs: {kwargs}")
            return func(self, *args, **kwargs)
        # -----------------------------------------------------

        table_name  = getattr(self.model, "__tablename__", self.model.__name__)
        method_name = func.__name__
        device_id   = getattr(self, "device_id", 1)

        # 1) Собираем все реальные аргументы (включая self) через inspect
        # sig   = inspect.signature(func)
        # bound = sig.bind(self, *args, **kwargs)
        #
        # # 2) Строим payload без self
        # payload = {
        #     name: val
        #     for name, val in bound.arguments.items()
        #     if name != "self"
        # }

        # sig = inspect.signature(func)
        # bound = sig.bind(self, *args, **kwargs)  # ← обязательно передаём self первым
        # full_args = bound.arguments  # OrderedDict([('self',…),('index',4),('name','…'),…])
        # payload = {k: v
        #            for k,
        #            v in full_args.items()
        #            if k != 'self'
        # }
        sig = inspect.signature(func)
        bound = sig.bind(self, *args, **kwargs)
        payload = {
            name: val
            for name, val in bound.arguments.items()
            if name != "self"
        }
        # 3) Считаем ключ дедупликации

        # если данные пришли в record["kwargs"], распакуем их
        if "kwargs" in payload and isinstance(payload["kwargs"], dict):
            payload = payload["kwargs"]

        record_id   = payload.get("id") or payload.get("index") or payload.get('args')[0]

        # __id = payload.get('id') or payload.get('index')
        if not record_id:
            raise ValueError("record must be have id or index provided and cannot be None or empty.")


        payload_key = f"id:{record_id}" if record_id is not None else json.dumps(payload, sort_keys=True)
        dedup_key   = (table_name, method_name, payload_key)

        # 4) Если уже выполняли эту операцию — выйдем сразу
        with _lock:
            device_state = _state.get(device_id, {})
            if dedup_key in device_state:
                print(f"[{threading.current_thread().name}][decorators][wraps] "
                      f"Вышли без исполнения операции. func: {method_name}, table: {table_name}, "
                      f"args: {args}, kwargs: {kwargs}")
                return device_state[dedup_key]

        # 5) Валидация данных через трансформер
        transformer = get_global_transformer()
        if not transformer.validate(table_name, kwargs):
            raise ValueError(f"Validation failed for table '{table_name}' with payload: {kwargs}")

        # 6) Собственно вызываем CRUD-метод
        try:
            print(f"[{threading.current_thread().name}][decorators][wraps] "
                  f"Запустили синхронизацию. func: {method_name}, table: {table_name}, "
                  f"args: {args}, kwargs: {kwargs}")
            result = func(self, *args, **kwargs)
        except Exception as e:
            print(f"[{threading.current_thread().name}][decorators][wraps] "
                  f"Ошибка вызова func: {e}. func: {method_name}, table: {table_name}, "
                  f"args: {args}, kwargs: {kwargs}")
            raise

        # 7) Сохраняем результат для дедупликации
        with _lock:
            _state.setdefault(device_id, {})[dedup_key] = result

        # 8) Кладём «локальную» команду в очередь на отправку серверу
        queue_in = INBOUND_QUEUES.get(device_id)

        from datetime import datetime
        data = {}
        for k, v in kwargs.items():
            if hasattr(v, "to_dict"):
                data[k] = v.to_dict()
            elif isinstance(v, datetime):
                data[k] = v.isoformat()
            else:
                data[k] = v

        if queue_in:
            queue_in.put({
                "type":      "local",
                "table":     table_name,
                "operation": method_name,
                "data":      data,    # ровно те ключи, что пришли в функцию
            })

        return result

    return wrapper

# import threading
# import json
# from functools import wraps
# import logging
# import inspect
# import dbSync
# from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES
# from dbSync.Logic_v2.DataTransformer import DataTransformer
#
# logger = logging.getLogger(__name__)
# log = logging.getLogger("sync.decorator")
#
# # Для каждого device храним (last_payload_key, last_result)
# # _state: dict[int, tuple[str, any]] = {}
# _state = {}
# _lock = threading.Lock()
#
# # создайте и настройте глобальный трансформер где-нибудь в инициализации приложения
# _global_transformer = DataTransformer()  # <-- зарегистрируйте в нём ваши правила
#
#
# def get_global_transformer() -> DataTransformer:
#     return _global_transformer
#
#
#
# def sync_aware(func):
#     """
#     Декоратор для CRUD-методов:
#       – вычисляет ключ payload_key (на основе payload['id'] или всего payload JSON)
#       – если payload_key == предыдущему для этого device_id:
#           • НЕ вызывает func
#           • сразу возвращает last_result
#       – иначе:
#           • валидирует payload
#           • вызывает func → получает result
#           • запоминает (payload_key, result)
#           • кладёт команду в очередь
#           • возвращает result
#     """
#     @wraps(func)
#     def wrapper(self, *args, **kwargs):
#         # --- Если инициализация БД, просто вызываем метод без логики синхра ---
#         if getattr(dbSync, "init_db", False):
#             table_name  = getattr(self.model, "__tablename__", self.model.__name__)
#             method_name = func.__name__
#             print(f"[{threading.current_thread().name}][decorators][wraps] "
#                   f"обработали БЕЗ синхронизации. func: {method_name}, table: {table_name}, "
#                   f"args: {args}, kwargs: {kwargs}")
#             return func(self, *args, **kwargs)
#         # -----------------------------------------------------
#
#         table_name  = getattr(self.model, "__tablename__", self.model.__name__)
#         method_name = func.__name__
#         device_id   = getattr(self, "device_id", 1)
#
#         # 1) Собираем все реальные аргументы (включая self) через inspect
#         sig = inspect.signature(func)
#         bound = sig.bind(self, *args, **kwargs)  # ← обязательно передаём self первым
#         full_args = bound.arguments  # OrderedDict([('self',…),('index',4),('name','…'),…])
#         payload = {k: v
#                    for k,
#                    v in full_args.items()
#                    if k != 'self'
#         }
#
#         # 2) Строим payload без self
#         # payload = {
#         #     name: val
#         #     for name, val in bound.arguments.items()
#         #     if name != "self"
#         # }
#
#         # 3) Считаем ключ дедупликации
#         record_id   = payload.get("id") or payload.get("index") or payload.get("number")
#         payload_key = f"id:{record_id}" if record_id is not None else json.dumps(payload, sort_keys=True)
#         dedup_key   = (table_name, method_name, payload_key)
#
#         # 4) Если уже выполняли эту операцию — выйдем сразу
#         with _lock:
#             device_state = _state.get(device_id, {})
#             if dedup_key in device_state:
#                 print(f"[{threading.current_thread().name}][decorators][wraps] "
#                       f"Вышли без исполнения операции. func: {method_name}, table: {table_name}, "
#                       f"args: {args}, kwargs: {kwargs}")
#                 return device_state[dedup_key]
#
#         # 5) Валидация данных через трансформер
#         transformer = get_global_transformer()
#         if not transformer.validate(table_name, payload):
#             raise ValueError(f"Validation failed for table '{table_name}' with payload: {payload}")
#
#         # 6) Собственно вызываем CRUD-метод
#         try:
#             print(f"[{threading.current_thread().name}][decorators][wraps] "
#                   f"Запустили синхронизацию. func: {method_name}, table: {table_name}, "
#                   f"args: {args}, kwargs: {kwargs}")
#             result = func(self, *args, **kwargs)
#         except Exception as e:
#             print(f"[{threading.current_thread().name}][decorators][wraps] "
#                   f"Ошибка вызова func: {e}. func: {method_name}, table: {table_name}, "
#                   f"args: {args}, kwargs: {kwargs}")
#             raise
#
#         # 7) Сохраняем результат для дедупликации
#         with _lock:
#             _state.setdefault(device_id, {})[dedup_key] = result
#
#         # 8) Кладём «локальную» команду в очередь на отправку серверу
#         queue_in = INBOUND_QUEUES.get(device_id)
#         if queue_in:
#             queue_in.put({
#                 "type":      "local",
#                 "table":     table_name,
#                 "operation": method_name,
#                 "data":      payload,    # ровно те ключи, что пришли в функцию
#             })
#
#         return result
#
#     return wrapper