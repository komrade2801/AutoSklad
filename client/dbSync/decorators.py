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

# создайте и настройте глобальный трансформер где-нибудь в инициализации приложения
_global_transformer = DataTransformer()  # <-- зарегистрируйте в нём ваши правила


def get_global_transformer() -> DataTransformer:
    return _global_transformer



def sync_aware(func):
    """
    Декоратор для CRUD-методов:
      – валидирует payload через DataTransformer
      – вызывает func → получает result
      – кладёт команду в очередь для синхронизации
      – возвращает result
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # --- Если в текущем потоке применяется sync или инициализация БД — без постановки в очередь ---
        if dbSync.is_skip_sync_enqueue():
            table_name  = getattr(self.model, "__tablename__", self.model.__name__)
            method_name = func.__name__
            logger.debug("[decorators][wraps] обработали БЕЗ синхронизации. func: %s, table: %s, args: %s, kwargs: %s", method_name, table_name, args, kwargs)
            return func(self, *args, **kwargs)
        # -----------------------------------------------------
        
        # --- Если sync_context=True, НЕ создаем локальную команду (применяем команду из sync) ---
        sync_context = kwargs.pop('sync_context', False)
        if sync_context:
            table_name  = getattr(self.model, "__tablename__", self.model.__name__)
            method_name = func.__name__
            logger.debug("[decorators][wraps] обработали БЕЗ синхронизации (sync_context). func: %s, table: %s", method_name, table_name)
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

        # если данные пришли в record["kwargs"], распакуем их
        if "kwargs" in payload and isinstance(payload["kwargs"], dict):
            payload = payload["kwargs"]

        # Проверяем наличие id или index
        record_id = payload.get("id") or payload.get("index")
        if not record_id:
            raise ValueError("record must be have id or index provided and cannot be None or empty.")

        # Валидация данных через трансформер
        transformer = get_global_transformer()
        if not transformer.validate(table_name, kwargs):
            raise ValueError(f"Validation failed for table '{table_name}' with payload: {kwargs}")

        # Вызываем CRUD-метод
        try:
            logger.debug("[decorators][wraps] Запустили синхронизацию. func: %s, table: %s", method_name, table_name)
            result = func(self, *args, **kwargs)
        except Exception as e:
            logger.exception("[decorators][wraps] Ошибка вызова func: %s. func: %s, table: %s", e, method_name, table_name)
            raise

        # Кладём «локальную» команду в очередь на отправку серверу
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