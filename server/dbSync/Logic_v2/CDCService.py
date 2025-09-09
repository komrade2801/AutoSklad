import traceback
from typing import Callable, Dict, List, Any, TypedDict, Optional
import threading
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


# from SyncProcessor import SyncProcessor

class ChangeEvent(TypedDict):
    """
    Описывает единичное изменение в локальной БД, предназначенное для синхронизации.

    Атрибуты:
        table (str):
            Имя таблицы, где произошло изменение.
        operation (str):
            Тип операции: "insert", "update" или "delete".
        record_id (int):
            Первичный ключ изменённой записи.
        data (Dict[str, Any]):
            Полезная нагрузка — новые или затронутые поля в локальном формате.
        timestamp (str):
            Метка времени события в формате ISO 8601 с часовым поясом.
    """

    table: str
    operation: str
    record_id: int
    data: Dict[str, Any]
    timestamp: str

class CDCService:
    """
    Сервис отслеживания изменений (Change Data Capture) в локальной БД и рассылки их зарегистрированным слушателям.

    Место в архитектуре:
        • Находится в логическом слое приложения, между ORM и SyncProcessor.
        • Используется декораторами @sync_aware или триггерами на уровне модели/БД.
        • Не хранит состояния записей — только ведёт карту слушателей и рассылку.

    Зависимости:
        :listeners: Dict[str, List[Callable[[ChangeEvent], None]]]
            Словарь списков callback-функций, сгруппированных по имени таблицы.
        :lock: threading.Lock
            Мьютекс для потокобезопасного доступа к `listeners`.
        SyncProcessor (косвенно):
            Через CommandSender преобразует ChangeEvent в JSON и посылает в SyncProcessor.push().

    Основные функции:
        1. register_listener(table_name, callback):
           Регистрирует callback — функцию, принимающую ChangeEvent.
        2. emit_change_event(event):
           Вызывает все callback для event.table в отдельном потоке,
           чтобы не блокировать основной поток приложения.
        3. clear_listeners(table_name=None):
           Очищает всех слушателей для указанной таблицы или всех сразу.

    Протокол вызовов (Sequence Diagram, упрощённо):
        ORM Model    --> CDCService: emit_change_event(ChangeEvent)
        CDCService   --> threading.Thread: start(_dispatch(event))
        Thread       --> CDCService._dispatch:
            for listener in listeners[event.table]:
                listener(event)
        listener     --> CommandSender: enqueue(event)
        CommandSender--> SyncProcessor.push(json_commands)

    Пример использования:
        cdc = CDCService()
        cdc.register_listener("users", on_user_change)
        @sync_aware("users")
        def create_user_record(...):
            # внутри ORM-триггера создаётся ChangeEvent и
            cdc.emit_change_event(event)
    """

    def __init__(self) -> None:
        """
        Инициализация CDCService.

        Инициализирует пустой словарь listeners и потокобезопасный lock.
        """
        self.listeners: Dict[str, List[Callable[[ChangeEvent], None]]] = {}
        self.lock = threading.RLock()

    def register_listener(self, table_name: str, callback: Callable[[ChangeEvent], None]) -> None:
        """
        Подписаться на события заданной таблицы.

        :param table_name: Имя таблицы, за изменения в которой слушатель будет уведомлён.
        :param callback: Функция-обработчик, принимающая один аргумент типа ChangeEvent.
        """
        with self.lock:
            self.listeners.setdefault(table_name, []).append(callback)
        print(f'[ПОТОК][{threading.current_thread().name}][CDCService][register_listener] - listener registered for table: {table_name}', flush=True)

    def emit_change_event(self, event: ChangeEvent) -> None:
        """
        Создаёт фоновый поток для рассылки события слушателям.

        :param event: ChangeEvent — описание произошедшего изменения.
        :raises ValueError: если у event.operation не один из "insert", "update", "delete".
        """
        print(f'[ПОТОК][{threading.current_thread().name}][CDCService][emit_change_event][INFO] - command_id: {event}. [{datetime.now()}]')
        op = event["operation"].lower()
        if op not in ("insert", "update", "delete"):
            raise ValueError(f"Unsupported operation '{event['operation']}' in ChangeEvent")
        # Дата-время в ISO, если передана иначе — нормализуем
        try:
            # попытаемся распарсить, если строка
            datetime.fromisoformat(event["timestamp"])
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][CDCService][emit_change_event][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
            event["timestamp"] = datetime.utcnow().isoformat()

        # Запускаем рассылку в фоне, чтобы не замедлять транзакции ORM
        print(f'[ПОТОК][{threading.current_thread().name}][CDCService][emit_change_event] Запускаем рассылку в фоне, чтобы не замедлять транзакции ORM. [{datetime.now()}]')
        threading.Thread(target=self._dispatch, args=(event,), daemon=True).start()

    def _dispatch(self, event: ChangeEvent) -> None:
        """
        Фактическая рассылка события слушателям в пределах одной таблицы.

        :param event: ChangeEvent
        """
        print(f'[ПОТОК][{threading.current_thread().name}][CDCService][_dispatch][INFO] - command_id: {event}. [{datetime.now()}]')
        with self.lock:
            listeners = list(self.listeners.get(event["table"], []))
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                # Логируем и продолжаем оповещать других слушателей
                # (предполагается внешний логгер в замыкании listener)
                print(f'[ПОТОК][{threading.current_thread().name}][CDCService][_dispatch][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. [{datetime.now()}]')
                print(f"CDCService listener error: {e}", flush=True)

    def clear_listeners(self, table_name: Optional[str] = None) -> None:
        """
        Очищает подписчиков.

        :param table_name: Если указан, очищает только для этой таблицы.
                           Иначе — удаляет всех слушателей для всех таблиц.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][CDCService][clear_listeners][INFO] - [{datetime.now()}]')
        with self.lock:
            if table_name:
                self.listeners.pop(table_name, None)
            else:
                self.listeners.clear()

# -----------------------------------------------------------------------------
# Список изменений в обновлённой версии класса CDCService:
# 1. TypedDict ChangeEvent вместо простого класса для строгой аннотации полей.
# 2. Проверка корректности поля `operation` и нормализация регистра.
# 3. Нормализация / проверка timestamp через datetime.fromisoformat.
# 4. Потокобезопасность: добавлен threading.Lock для защиты self.listeners.
# 5. Асинхронная рассылка: запускаем _dispatch в отдельном daemon-потоке.
# 6. Новый метод clear_listeners для управления подписками.
# 7. Подробные докстринги на класс и все методы с описанием архитектурного контекста.
#
# Прочая важная информация:
# • CDCService не зависит от конкретного механизма БД — получает события извне.
# • CommandSender и SyncProcessor используют ChangeEvent для формирования JSON-команд.
# • Обработчики слушателей могут быть связаны с очередями (RabbitMQ, Kafka) или локальными накопителями.
#
# Предложения по улучшению:
# - Интеграция с библиотекой pydantic для валидации ChangeEvent «из коробки».
# - Метрики: счётчики с Prometheus (events_emitted_total, listener_errors_total).
# - Возможность приоритизации слушателей (очередь с приоритетами).
# - Замена logger.() на централизованный логгер (DiagnosticLogger или встроенный logging).
# - Тесты: unit–тесты для register_listener, emit_change_event, clear_listeners, ошибки в callback.
# - Расширение API: добавить unsubscribe_listener(table_name, callback).
# -----------------------------------------------------------------------------
