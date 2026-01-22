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
        # --- Если инициализация БД, просто вызываем метод без логики синхра ---
        if dbSync.init_db:
            table_name  = getattr(self.model, "__tablename__", self.model.__name__)
            method_name = func.__name__
            # print(f"[{threading.current_thread().name}][decorators][wraps] "       f"обработали БЕЗ синхронизации. func: {method_name}, table: {table_name}, "       f"args: {args}, kwargs: {kwargs}")
            # если данные пришли в record["kwargs"], распакуем их
            if "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
                kwargs = kwargs["kwargs"]
            __id = kwargs.get('id') or kwargs.get('index')
            kwargs['index'] = __id
            return func(self, *args, **kwargs)
        # -----------------------------------------------------
        
        # --- Если sync_context=True, НЕ создаем локальную команду (применяем команду из sync) ---
        sync_context = kwargs.pop('sync_context', False)
        if sync_context:
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
            print(f"[{threading.current_thread().name}][decorators][wraps] Запустили синхронизацию. func: {method_name}, table: {table_name}, args: {args}, kwargs: {kwargs}")
            result = func(self, *args, **kwargs)
        except Exception as e:
            print(f"[{threading.current_thread().name}][decorators][wraps] Ошибка вызова func: {e}. func: {method_name}, table: {table_name}, args: {args}, kwargs: {kwargs}")
            raise

        # Кладём «локальную» команду в очередь на отправку серверу
        queue_in = INBOUND_QUEUES.get(device_id)
        if queue_in:
            queue_in.put({
                "type":      "local",
                "table":     table_name,
                "operation": method_name,
                "data":      kwargs,    # ровно те ключи, что пришли в функцию
            })

        return result

    return wrapper