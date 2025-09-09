# import json
# from datetime import datetime
import datetime
import threading
from typing import Any, List, Dict, Optional, TypedDict, Literal

from .DataTransformer import DataTransformer
from dbSync.Transport.TransportService import TransportService
from .SyncProcessor import SyncProcessor
from .DiagnosticLogger import DiagnosticLogger
from . import CommandQueue


class PendingCommand(CommandQueue.Command, total=False):
    """
    Расширяет структуру Command из CommandQueue, добавляя опциональные поля для отправки.

    Атрибуты:
        schema_hash (str): Хэш схемы БД клиента для согласования с сервером.
    """
    schema_hash: str


class PushPayload(TypedDict):
    """
    Контракт запроса на push к серверу.

    Атрибуты:
        device (Any): Идентификатор клиента/устройства.
        schema_hash (str): Хэш схемы, подтверждающий согласованность.
        commands (List[Dict[str, Any]]): Список команд в формате ServerCommand.
    """
    device: Any
    schema_hash: str
    commands: List[Dict[str, Any]]


class ServerCommand(TypedDict):
    """
    Структура одиночной команды в push-запросе.

    Атрибуты:
        id (str): UUID локальной команды.
        table (str): Имя таблицы.
        operation (Literal['INSERT','UPDATE','DELETE']): Тип операции.
        data (Dict[str, Any]): Полезная нагрузка.
        last_modified (str): Момент локального изменения в ISO-формате UTC.
    """
    id: str
    table: str
    operation: Literal['INSERT', 'UPDATE', 'DELETE']
    data: Dict[str, Any]
    last_modified: str


class CommandSender:
    """
    Компонент Push-процесса синхронизации.

    Назначение:
        - Забирает из локальной CommandQueue все команды со статусом 'pending'.
        - Формирует единый payload для сервера и отправляет через TransportService.send_push().
        - По результатам ответа обновляет статусы команд (done/failed).
        - В dev-режиме (если передан SyncProcessor) эмулирует server-side обработку.

    Место в архитектуре:
        CommandQueue → CommandSender → TransportService → SyncProcessor (сервер)

    Зависимости:
        :transport: TransportService — отправка HTTP/WebSocket.
        :queue: CommandQueue — локальное хранилище команд.
        :device_id: Any — уникальный идентификатор устройства.
        :endpoint: str — URL для push.
        :sync_processor: Optional[SyncProcessor] — для эмуляции server-side.
        :logger: Optional[DiagnosticLogger] — централизованное логирование.

    Логика работы send_pending():
        1. get_pending_commands()
        2. Сбор и нормализация {operation.upper(), last_modified}
        3. Отправка send_push(endpoint, payload)
        4. При success:
           - mark_as_done() для каждой команды.
        5. При failure:
           - mark_as_failed() для каждой команды.
        6. (Dev) эмуляция через sync_processor.process_push().

    Sequence Diagram:
        CommandSender -> CommandQueue: get_pending_commands()
        CommandSender -> TransportService: send_push(endpoint, payload)
        alt dev_mode
            CommandSender -> SyncProcessor: process_push(device, commands, schema_hash)
        end
        TransportService --> CommandSender: response
        CommandSender -> CommandQueue: mark_as_done()/mark_as_failed()
    """

    def __init__(
            self,
            transport: TransportService,
            queue: CommandQueue,
            device_id: Any,
            endpoint: str = "/sync/push",
            sync_processor: Optional[SyncProcessor] = None,
            logger: Optional[DiagnosticLogger] = None,
    ) -> None:
        self.transport = transport
        self.queue = queue
        self.device_id = device_id
        self.endpoint = endpoint
        self.sync_processor = sync_processor
        self.logger = logger

        self._handshaken = False
        self._server_schema = None
        self._field_mappings = None
        self._schema_hash = None

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

    def send_pending(self) -> None:
        """
        Отправляет все pending-команды одним batch-запросом.
        Здесь мы дополнительно обогащаем каждую команду через DataTransformer.
        """
        print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] send_pending. {datetime.datetime.now()}')
        self._ensure_handshake()

        pending = self.queue.get_pending_commands()
        if not pending:
            if self.logger:
                self.logger.log_debug("Нет ожидающих отправки команд.")
            return

        print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] {pending} ожидающие команды. {datetime.datetime.now()}')

        # --- Готовим payload ---
        schema_hash = self._schema_hash or ""
        payload: PushPayload = {
            "device": self.device_id,
            "schema_hash": schema_hash,
            "commands": []
        }

        # Получаем DataTransformer из SyncProcessor
        transformer: DataTransformer = self.sync_processor.data_transformer

        for cmd in pending:
            raw_data = cmd["data"]

            if cmd['table'] == "Cell":
                pass

            # обогащаем «сырые» данные:
            enriched_data = transformer.postprocess(cmd["table"], raw_data)

            payload["commands"].append(ServerCommand(
                id=cmd["id"],
                table=cmd["table"],
                operation=cmd["operation"].upper(),
                data=enriched_data,
                last_modified=""  # если не нужен — можно оставить пустым
            ))

        print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] payload: {payload}. {datetime.datetime.now()}')

        try:
            if self.logger:
                self.logger.log_info(f"Sending {len(pending)} commands to {self.endpoint}")
            # отправляем на реальный сервер
            response = self.transport.send_push(self.endpoint, payload)
            print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] response: {response}. {datetime.datetime.now()}')

            # в dev-режиме прогоняем через SyncProcessor (эмуляция)
            if self.sync_processor:
                self.sync_processor.process_push(
                    device=self.device_id,
                    commands=payload["commands"],
                    client_schema_hash=schema_hash
                )

            # отмечаем всё как сделанное
            for cmd in pending:
                self.queue.mark_as_done(cmd["id"])
            if self.logger:
                self.logger.log_info("All pending commands marked as done.")

        except Exception as err:
            print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] Не удалось отправить команды: {err}')
            if self.logger:
                self.logger.log_error(f"Failed to send commands: {err}")
            for cmd in pending:
                self.queue.mark_as_failed(cmd["id"])
            raise
    # def send_pending(self) -> None:
    #     """
    #     Отправляет все pending-команды одним batch-запросом.
    #
    #     :raises TransportError: при сбое сети или не-2xx ответе.
    #     """
    #     print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] send_pending. Текущее время: {datetime.datetime.now()}')
    #     self._ensure_handshake()
    #
    #     pending = self.queue.get_pending_commands()
    #     if not pending:
    #         if self.logger:
    #             print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] Нет ожидающих отправки команд. Текущее время: {datetime.datetime.now()}')
    #             self.logger.log_debug("Нет ожидающих отправки команд.")
    #             pass
    #         return
    #     print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] {len(pending)} pending commands to send. Текущее время: {datetime.datetime.now()}')
    #
    #     # берём хэш из handshake, а не из команд
    #     schema_hash = self._schema_hash or ""
    #     payload = {
    #         "device": self.device_id,
    #         "schema_hash": schema_hash,
    #         "commands": []
    #     }
    #     print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] schema_hash: {schema_hash}. Текущее время: {datetime.datetime.now()}')
    #     for cmd in pending:
    #         payload["commands"].append({
    #             "id": cmd["id"],
    #             "table": cmd["table"],
    #             "operation": cmd["operation"].upper(),
    #             "data": cmd["data"],
    #             # last_modified в push обычно не нужен; сервер сам проставит
    #         })
    #     print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] payload: {payload}. Текущее время: {datetime.datetime.now()}')
    #
    #     try:
    #         if self.logger:
    #             self.logger.log_info(f"Sending {len(pending)} commands to {self.endpoint}")
    #         # можно добавить schema_hash в query, если сервер требует
    #         response = self.transport.send_push(self.endpoint, payload)
    #         print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] response: {response}. Текущее время: {datetime.datetime.now()}')
    #
    #         # dev-mode
    #         if self.sync_processor:
    #             self.sync_processor.process_push(
    #                 device=self.device_id,
    #                 commands=payload["commands"],
    #                 client_schema_hash=schema_hash
    #             )
    #         print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] Все команды отправлены. Текущее время: {datetime.datetime.now()}')
    #         for cmd in pending:
    #             self.queue.mark_as_done(cmd["id"])
    #         if self.logger:
    #             self.logger.log_info("All pending commands marked as done.")
    #
    #     except Exception as err:
    #         print(f'[ПОТОК][{threading.current_thread().name}][CommandSender] Не удалось отправить команды: {err} Текущее время: {datetime.datetime.now()}')
    #
    #         if self.logger:
    #             self.logger.log_error(f"Failed to send commands: {err}")
    #         for cmd in pending:
    #             self.queue.mark_as_failed(cmd["id"])
    #         raise

# -----------------------------------------------------------------------------
# Изменения в CommandSender:
# 1. TypedDict: PendingCommand, ServerCommand, PushPayload для строгой валидации.
# 2. Добавлен DiagnosticLogger вместо logger.().
# 3. Метод send_pending() вместо send_pending_commands() для единообразия.
# 4. Поддержка опционального sync_processor для dev-mode.
# 5. Подробные докстринги с архитектурным контекстом и Sequence Diagram.
# 6. Нормализация operation через .upper(), timestamp fallback.
# 7. Логирование этапов: debug/info/error.

# Прочая информация и рекомендации:
# - Bulk vs per-command retry: сейчас batch atomic; можно добавить per-command retry logic.
# - Использовать asyncio/async def для асинхронных transport.
# - Метрики: счётчики отправленных, неудачных, latency.
# - Хранение schema_hash в поле команды лучше переносить в CommandQueue при вставке.
# - Unit-тесты на успешный и фейловый сценарии.
# - Возможная оптимизация: gzip-сжатие payload, batch size limit.
# - Рассмотреть формат protobuf/avro для payload вместо JSON для экономии трафика.
# -----------------------------------------------------------------------------
# Полностью переработанный класс CommandSender с детальными докстрингами, строгой типизацией, логированием и архитектурным контекстом. Ниже кратко резюмирую:
#
# TypedDict: PendingCommand, ServerCommand и PushPayload для валидации.
#
# Логирование: через DiagnosticLogger, вместо logger..
#
# Метод: send_pending() с этапами сборки, отправки, эмуляции, обновления статусов.
#
# Dev-mode: поддержка эмуляции server-side.
#
# Докстринги: описывают расположение в цепочке CommandQueue → CommandSender → TransportService → SyncProcessor.
#
# Рекомендации: bulk-retry, асинхронность, метрики, тесты, оптимизация трафика.
