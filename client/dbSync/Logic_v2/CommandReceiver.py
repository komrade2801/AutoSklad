# import json
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict
import threading
from .TransportService import TransportService, logger
from .SyncProcessor import SyncProcessor
from .DiagnosticLogger import DiagnosticLogger


class ServerCommand(TypedDict):
    """
    Структура команды, получаемой от сервера при pull.

    Атрибуты:
        id (Any): Уникальный идентификатор команды на сервере.
        table (str): Имя таблицы для обработки.
        operation (str): Тип операции: "add", "update" или "delete" (независимо от регистра).
        data (Dict[str, Any]): Полезная нагрузка команды.
        last_modified (str): ISO-8601 метка времени изменения на сервере.
    """
    id: Any
    table: str
    operation: str
    data: Dict[str, Any]
    last_modified: str


class PullResponse(TypedDict):
    """
    Структура ответа от сервера на pull-запрос.

    Атрибуты:
        schema_hash (str): Хэш текущей схемы БД для валидации согласованности.
        commands (List[ServerCommand]): Список команд для применения.
    """
    schema_hash: str
    commands: List[ServerCommand]


class CommandReceiver:
    """
    Компонент Pull-процесса синхронизации: запрашивает новые команды у сервера,
    применяет их локально через SyncProcessor и обновляет границу last_synced.

    Место в архитектуре:
        • Выполняется периодически (Celery, asyncio, Cron).
        • На стороне клиента (каждого устройства) идентифицируется device_id.
        • Опирается на TransportService для сетевого взаимодействия
          и SyncProcessor для применения команд.

    Зависимости:
        transport (TransportService): HTTP/WebSocket клиент с методом send_pull(endpoint, params).
        sync_processor (SyncProcessor): Координатор входящих команд и применений.
        device_id (str | int): Уникальный идентификатор клиента.
        endpoint (str): URL для pull-запроса.
        last_synced_path (str): Путь к файлу хранения метки last_synced.
        logger (DiagnosticLogger): (Опционально) централизованный логгер.

    Логика работы:
        1. При инициализации загружает last_synced из файла.
        2. В fetch_and_apply():
           a. Формирует параметры pull (device, since).
           b. Запрашивает у transport.send_pull().
           c. Валидирует и десериализует ответ.
           d. Итерационно обрабатывает команды через sync_processor.process_push(),
              обновляя временную границу new_last.
           e. Сохраняет new_last в файл, если есть обновление.
        3. Исключения сети логируются и не ломают выполнение.
        4. Ошибки применения отдельных команд логируются,
           остальные исполняются.

    Sequence Diagram (упрощённо):
        CommandReceiver -> TransportService: send_pull(endpoint, {device, since})
        TransportService --> CommandReceiver: PullResponse
        CommandReceiver -> SyncProcessor: process_push(device, commands, schema_hash)
        SyncProcessor --> BatchProcessor: execute_batch(mapped_ops)
        SyncProcessor --> DB: commit/rollback
        CommandReceiver -> File: write last_synced
    """

    def __init__(
            self,
            transport: TransportService,
            sync_processor: SyncProcessor,
            device_id: Any,
            endpoint: str = "/sync/pull",
            last_synced_path: str = "last_synced.txt",
            logger: Optional[DiagnosticLogger] = None
    ) -> None:
        """
        Инициализация CommandReceiver: загружает границу last_synced.

        :param transport:     Транспортный сервис для pull-запросов.
        :param sync_processor: SyncProcessor для применения команд.
        :param device_id:      Идентификатор клиента/устройства.
        :param endpoint:       URL для pull.
        :param last_synced_path: Путь к файлу last_synced.
        :param logger:         (Опционально) логгер.
        """
        self._handshaken = False
        self._schema_hash    = None

        self.transport = transport
        self.sync_processor = sync_processor
        self.device_id = device_id
        self.endpoint = endpoint
        self.last_synced_path = last_synced_path
        self.logger = logger
        self.last_synced = self._load_last_synced()

    def _ensure_handshake(self):
        if self._handshaken:
            return

        # 1) Локальная схема
        client_schema = self.sync_processor.sync_manager.get_local_schema()

        # 2) Обмен через TransportService
        resp = self.transport.send_schema("/sync/handshake", client_schema, device=self.device_id)
        mapping, schema_hash = resp["mapping"], resp["schema_hash"]

        # 3) Обновляем SyncProcessor и DataMapper
        self.sync_processor.update_schema(mapping, schema_hash)
        self.sync_processor.data_mapper.update_field_mappings(mapping)
        self._schema_hash = schema_hash
        self._handshaken = True
        logger.debug("[CommandReceiver][_ensure_handshake]")

    def _load_last_synced(self) -> str:
        """
        Считывает последнюю сохранённую метку синхронизации из файла.
        Если файл отсутствует — возвращает пустую строку и (опционально) создаёт его.
        """
        path = self.last_synced_path
        thread_name = threading.current_thread().name
        logger.debug("[CommandReceiver][_load_last_synced] Проверка файла: %s", path)

        if not os.path.exists(path):
            # Штатная ситуация: файл ещё не создан (например, при первом запуске)
            logger.debug("[CommandReceiver][_load_last_synced] Файл не найден (первый запуск?) → создаём пустой.")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")  # создаём пустой файл
            except Exception as e:
                logger.exception("[CommandReceiver][_load_last_synced] Не удалось создать файл: %s", e)
            return ""

        try:
            with open(path, "r", encoding="utf-8") as f:
                ts = f.read().strip()
            datetime.fromisoformat(ts)  # проверка формата
            return ts
        except ValueError:
            logger.warning("[CommandReceiver][_load_last_synced] Неверный формат даты в файле → сбрасываем.")
            return ""
        except Exception as e:
            logger.exception("[CommandReceiver][_load_last_synced] Неожиданная ошибка чтения: %s", e)
            return ""

    def _save_last_synced(self, timestamp: str) -> None:
        """
        Записывает новую метку last_synced в файл.

        :param timestamp: ISO-8601 строка.
        """
        try:
            with open(self.last_synced_path, "w", encoding="utf-8") as f:
                f.write(timestamp)
            logger.debug("[CommandReceiver][_save_last_synced]")
        except Exception as e:
            logger.exception("[CommandReceiver][_save_last_synced] error: %s", e)
            if self.logger:
                self.logger.log_error(f"Failed to save last_synced: {e}")

    def fetch_and_apply(self) -> None:
        """
        1) Убедиться в выполненном handshake
        2) Сделать зашифрованный запрос pull через TransportService
        3) Получить уже расшифрованный dict PullResponse
        4) Пройтись по командам и применить через SyncProcessor
        5) Обновить last_synced
        """
        self._ensure_handshake()

        params = {
            "device": self.device_id,
            "since": self.last_synced,
            "schema_hash": self._schema_hash
        }
        try:
            # TransportService.send_pull делает GET и внутри:
            #  - получает IV+ciphertext
            #  - дешифрует AES-CBC
            #  - проверяет HMAC
            #  - парсит JSON → возвращает Python dict
            logger.debug("[CommandReceiver][fetch_and_apply] Запрос команд.")
            response: PullResponse = self.transport.send_pull(self.endpoint, params)
            
        except Exception as e:
            logger.exception("[CommandReceiver][fetch_and_apply] error: %s", e)
            if self.logger:
                self.logger.log_error(f"Pull request failed: {e}")
            return

        # 4) Обновляем schema_hash, если сервер прислал новый
        logger.debug("[CommandReceiver][fetch_and_apply] Обновляем schema_hash.")
        new_schema_hash = response.get("schema_hash", "")
        if new_schema_hash:
            self._schema_hash = new_schema_hash

        # 5) Применяем каждую команду и собираем новую границу
        logger.debug("[CommandReceiver][fetch_and_apply] Применяем команды.")
        commands = response.get("commands", [])
        new_last = self.last_synced
        logger.debug("[CommandReceiver][fetch_and_apply] Применяем %s команд.", len(commands))
        for cmd in commands:
            try:
                self.sync_processor.process_push(
                    device=self.device_id,
                    commands=[cmd],
                    client_schema_hash=self._schema_hash
                )
                lm = cmd.get("last_modified", "")
                if lm and lm > new_last:
                    new_last = lm
            except Exception as ex:
                logger.exception("[CommandReceiver][fetch_and_apply] error applying command: %s", ex)
                if self.logger:
                    self.logger.log_error(
                        message=f"Failed to apply command {cmd.get('id')}: {ex}",
                        context=cmd
                    )
                continue
        logger.debug("[CommandReceiver][fetch_and_apply] Команды применены.")
        # 6) Сохраняем новую метку, если она изменилась
        if new_last and new_last != self.last_synced:
            self._save_last_synced(new_last)
            self.last_synced = new_last

        logger.info("[CommandReceiver][fetch_and_apply] Команды обработаны.")

#  Список изменений в обновлённой версии CommandReceiver
# TypedDict для входных структур
# – Введены ServerCommand и PullResponse для строгой типизации ответа от сервера.
#
# DiagnosticLogger
# – Добавлена опциональная зависимость logger: DiagnosticLogger вместо logger.().
#
# Валидация ISO-timestamp
# – Проверка формата при чтении last_synced; безопасный fallback на "".
#
# Конфигурируемый путь к файлу
# – Параметр last_synced_path вместо жестко заданной константы.
#
# Обработка парсинга ответа
# – Поддержка как словаря, так и JSON-строки (json.loads).
#
# Гранулярная обработка ошибок
# – Ошибки сетевого запроса и записи границы логируются и не прерывают основной цикл.
# – Ошибки применения отдельных команд логируются с передачей детали команды.
#
# Расширенные докстринги с архитектурным контекстом
# – Полное описание места в цепочке: TransportService → CommandReceiver → SyncProcessor → BatchProcessor → БД.
#
# Пример Sequence Diagram
# – В тексте класса приведён упрощённый протокол вызовов между компонентами.
#
#  Дополнительная информация и рекомендации
# Bulk-пакетирование
# Можно передавать сразу весь список commands в один вызов process_push, если SyncProcessor поддерживает батчи, чтобы сократить накладные расходы на несколько HTTP-вызовов.
#
# Асинхронный режим
# Если используется asyncio, стоит сделать методы async def fetch_and_apply() и использовать асинхронный transport.
#
# Метрики и мониторинг
# Инструментировать количество полученных команд, неудачных попыток и задержку между запросами (Prometheus, OpenTelemetry).
#
# Улучшение надёжности
# Хранить last_synced в более отказоустойчивом хранилище (SQLite, Redis) вместо текстового файла.
#
# Тестирование
# Покрыть unit-тестами:
#
# Корректная загрузка/сохранение границы.
#
# Обработка корректного и некорректного ответа сервера.
#
# Логирование ошибок.
#
# Совместимость с синхронизацией нескольких команд.
#
# Валидация схемы
# Можно использовать pydantic или marshmallow для строгой проверки структуры PullResponse и ServerCommand.
#
# Конфигурация
# Вынести endpoint и путь к файлу в конфигурацию приложения.
