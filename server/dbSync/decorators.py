import threading
import json
import traceback
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
        # Ключ очереди в INBOUND_QUEUES — всегда int (main.py: start_sync(dev.number)); нормализуем для надёжного поиска
        device_id   = getattr(self, "device_id", 1)
        queue_key   = int(device_id) if device_id is not None else 1
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
            print(f"[{threading.current_thread().name}][decorators][wraps] Запустили синхронизацию. func: {method_name}, table: {table_name}, "
                  f"device_id={device_id}, record_id={record_id}, args: {args}, kwargs: {kwargs}")
            result = func(self, *args, **kwargs)
            print(f"[{threading.current_thread().name}][decorators][wraps] CRUD-метод выполнен успешно. func: {method_name}, table: {table_name}, "
                  f"device_id={device_id}, record_id={record_id}")
        except Exception as e:
            print(f"[{threading.current_thread().name}][decorators][wraps][ERROR] Ошибка вызова func: {e}. func: {method_name}, table: {table_name}, "
                  f"device_id={device_id}, record_id={record_id}, args: {args}, kwargs: {kwargs}")
            logger.error(
                f"Error calling CRUD method {table_name}.{method_name}(record_id={record_id}). "
                f"device_id={device_id}, error: {e}, traceback: {traceback.format_exc()}"
            )
            raise

        # Кладём «локальную» команду в очередь на отправку (ключ — queue_key, int)
        queue_in = INBOUND_QUEUES.get(queue_key)
        if not queue_in and INBOUND_QUEUES:
            # Fallback: если очередь по device не найдена (другой тип ключа и т.д.), используем первую доступную
            queue_in = next(iter(INBOUND_QUEUES.values()))
            print(f"[{threading.current_thread().name}][decorators][wraps] Очередь по queue_key={queue_key} не найдена, использована первая доступная. "
                  f"available_keys={list(INBOUND_QUEUES.keys())}")
        if queue_in:
            try:
                queue_in.put({
                    "type":      "local",
                    "table":     table_name,
                    "operation": method_name,
                    "data":      kwargs,    # ровно те ключи, что пришли в функцию
                })
                print(f"[{threading.current_thread().name}][decorators][wraps] "
                      f"Команда добавлена в очередь. table={table_name}, operation={method_name}, "
                      f"device_id={device_id}, record_id={record_id}")
            except Exception as e:
                # ⚠️ КРИТИЧЕСКОЕ ЛОГИРОВАНИЕ - команда не была создана!
                error_msg = (
                    f"ОШИБКА ПРИ ДОБАВЛЕНИИ В ОЧЕРЕДЬ! Команда НЕ создана. "
                    f"table={table_name}, operation={method_name}, device_id={device_id}, "
                    f"record_id={record_id}, error={e}"
                )
                print(f"[{threading.current_thread().name}][decorators][wraps][ERROR] {error_msg}")
                logger.error(
                    f"Failed to put command in queue for device_id={device_id}. "
                    f"Command NOT created: {table_name}.{method_name}(record_id={record_id}). "
                    f"Error: {e}, traceback: {traceback.format_exc()}"
                )
        else:
            # ⚠️ КРИТИЧЕСКОЕ ЛОГИРОВАНИЕ (очереди нет вообще или fallback не сработал)
            error_msg = (
                f"ОЧЕРЕДЬ НЕ НАЙДЕНА! Команда НЕ создана. "
                f"table={table_name}, operation={method_name}, queue_key={queue_key}, "
                f"record_id={record_id}, available_devices={list(INBOUND_QUEUES.keys())}"
            )
            print(f"[{threading.current_thread().name}][decorators][wraps][ERROR] {error_msg}")
            logger.error(
                f"INBOUND_QUEUE missing for queue_key={queue_key}. "
                f"Command NOT created: {table_name}.{method_name}(record_id={record_id}). "
                f"Available devices: {list(INBOUND_QUEUES.keys())}"
            )

        return result

    return wrapper