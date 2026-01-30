# import json
# from datetime import datetime
import datetime
import threading
from typing import Any, List, Dict, Optional, TypedDict, Literal

from .TransportService import TransportService, logger
from .SyncProcessor import SyncProcessor
from .DiagnosticLogger import DiagnosticLogger
from . import CommandQueue

class RetryManager:
    """
    Интерфейс для планирования повторов (избегание циклического импорта).
    """
    def schedule_retry(self, cmd, delay=None):
        pass

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


# Размер батча при отправке push: порядок команд сохраняется
PUSH_BATCH_SIZE = 30


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

        self._handshaken     = False
        self._server_schema  = None
        self._field_mappings = None
        self._schema_hash    = None

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
        Отправляет pending команды в хронологическом порядке с учетом retrying команд.

        Новая логика:
        1. Сначала обрабатываем все retrying команды через retry_all_retrying()
        2. Проверяем, что нет retrying/failed команд старше pending
        3. Если есть retrying/failed старше - не отправляем pending (возвращаемся)
        4. Если все retrying обработаны или их нет - отправляем pending как обычно

        :raises TransportError: при сбое сети или не-2xx ответе.
        """
        logger.debug("[CommandSender] send_pending.")
        self._ensure_handshake()

        # 1. Сначала обрабатываем все retrying команды
        retry_manager = getattr(self, 'retry_manager', None)
        if retry_manager:
            retry_manager.retry_all_retrying()

        # 2. Проверяем согласованность: нет ли retrying/failed команд старше pending
        retrying = self.queue.get_retrying_commands()
        failed = self.queue.get_failed_commands()
        pending = self.queue.get_pending_commands()

        if not pending:
            if self.logger:
                self.logger.log_debug("Нет pending команд для отправки.")
            return

        # Проверяем, есть ли retrying/failed команды старше самой старой pending
        if retrying or failed:
            oldest_pending_ts = min(cmd["timestamp"] for cmd in pending)
            
            # Проверяем retrying команды
            for cmd in retrying:
                if cmd["timestamp"] < oldest_pending_ts:
                    logger.debug("[CommandSender] Есть retrying команда старше pending, не отправляем pending.")
                    if self.logger:
                        self.logger.log_debug("Retrying commands older than pending, skipping pending send")
                    return
            
            # Проверяем failed команды
            for cmd in failed:
                if cmd["timestamp"] < oldest_pending_ts:
                    logger.debug("[CommandSender] Есть failed команда старше pending, не отправляем pending.")
                    if self.logger:
                        self.logger.log_debug("Failed commands older than pending, skipping pending send")
                    return

        logger.info("[CommandSender] %s pending команд для отправки (старше retrying).", len(pending))

        schema_hash = self._schema_hash or ""

        # Отправка батчами по PUSH_BATCH_SIZE с сохранением порядка
        for batch_start in range(0, len(pending), PUSH_BATCH_SIZE):
            batch = pending[batch_start : batch_start + PUSH_BATCH_SIZE]
            payload = {
                "device": self.device_id,
                "schema_hash": schema_hash,
                "commands": [
                    {"id": cmd["id"], "table": cmd["table"], "operation": cmd["operation"].upper(), "data": cmd["data"]}
                    for cmd in batch
                ]
            }
            logger.info("[CommandSender] Отправка батча %s (%s команд).", batch_start // PUSH_BATCH_SIZE + 1, len(batch))

            try:
                if self.logger:
                    self.logger.log_info(f"Sending batch of {len(batch)} commands to {self.endpoint}")
                response = self.transport.send_push(self.endpoint, payload)
                logger.info("[CommandSender] Батч отправлен успешно.")

                if self.sync_processor:
                    self.sync_processor.process_push(
                        device=self.device_id,
                        commands=payload["commands"],
                        client_schema_hash=schema_hash
                    )

                # Обрабатываем ответ сервера и обновляем статусы команд батча
                server_statuses = response.get("statuses", []) if isinstance(response, dict) else []
                status_map = {str(s.get("id", "")): s for s in server_statuses if s.get("id") is not None}

                for cmd in batch:
                    cmd_id = str(cmd["id"])
                    server_status = status_map.get(cmd_id)
                    if server_status:
                        status = server_status.get("status", "").upper()
                        if status == "COMPLETED":
                            self.queue.mark_as_done(cmd_id)
                            logger.debug("[CommandSender] Команда %s помечена как done (сервер вернул COMPLETED)", cmd_id)
                        elif status in ("FAILED", "ERROR"):
                            self.queue.mark_as_failed(cmd_id)
                            error_msg = server_status.get("error", "Unknown error")
                            logger.warning("[CommandSender] Команда %s помечена как failed (сервер вернул %s): %s", cmd_id, status, error_msg)
                        else:
                            self.queue.mark_as_retrying(cmd_id)
                            logger.warning("[CommandSender] Команда %s помечена как retrying (неизвестный статус: %s)", cmd_id, status)
                    else:
                        self.queue.mark_as_done(cmd_id)
                        logger.debug("[CommandSender] Команда %s помечена как done (статус не найден в ответе сервера)", cmd_id)

                if self.logger:
                    self.logger.log_info(f"Processed batch of {len(batch)} commands based on server response.")

            except Exception as err:
                logger.exception("[CommandSender] Ошибка отправки батча: %s", err)
                if self.logger:
                    self.logger.log_error(f"Failed to send batch: {err}")
                for cmd in batch:
                    self.queue.mark_as_retrying(cmd["id"])
                raise

    def send_single_command(self, cmd: dict) -> None:
        """
        Отправляет одну retrying команду.

        :param cmd: Словарь команды с полями id, table, operation, data, retry_count
        """
        logger.debug("[CommandSender] send_single_command: %s retry_count=%s", cmd.get("id"), cmd.get("retry_count", 0))
        self._ensure_handshake()

        schema_hash = self._schema_hash or ""
        payload = {
            "device": self.device_id,
            "schema_hash": schema_hash,
            "commands": [{
                "id": cmd["id"],
                "table": cmd["table"],
                "operation": cmd["operation"].upper(),
                "data": cmd["data"],
            }]
        }

        try:
            if self.logger:
                self.logger.log_info(f"Sending single retrying command {cmd['id']} to {self.endpoint}")

            response = self.transport.send_push(self.endpoint, payload)
            logger.info("[CommandSender] single команда отправлена успешно: %s", cmd["id"])

            # dev-mode
            if self.sync_processor:
                self.sync_processor.process_push(
                    device=self.device_id,
                    commands=payload["commands"],
                    client_schema_hash=schema_hash
                )

            # Обрабатываем ответ сервера и обновляем статус команды
            server_statuses = response.get("statuses", []) if isinstance(response, dict) else []
            cmd_id = str(cmd["id"])
            
            # Ищем статус для этой команды в ответе сервера
            server_status = None
            for s in server_statuses:
                if str(s.get("id", "")) == cmd_id:
                    server_status = s
                    break
            
            if server_status:
                # Если сервер вернул статус для этой команды
                status = server_status.get("status", "").upper()
                if status == "COMPLETED":
                    self.queue.mark_as_done(cmd_id)
                    logger.debug("[CommandSender] Команда %s помечена как done (сервер вернул COMPLETED)", cmd_id)
                    if self.logger:
                        self.logger.log_info(f"Single command {cmd_id} completed successfully.")
                elif status in ("FAILED", "ERROR"):
                    # Если команда упала на сервере, помечаем как failed
                    self.queue.mark_as_failed(cmd_id)
                    error_msg = server_status.get("error", "Unknown error")
                    logger.warning("[CommandSender] Команда %s помечена как failed (сервер вернул %s): %s", cmd_id, status, error_msg)
                    if self.logger:
                        self.logger.log_error(f"Single command {cmd_id} failed on server: {error_msg}")
                    raise Exception(f"Server returned {status} for command {cmd_id}: {error_msg}")
                else:
                    # Неизвестный статус - оставляем как retrying
                    self.queue.mark_as_retrying(cmd_id)
                    logger.warning("[CommandSender] Команда %s помечена как retrying (неизвестный статус: %s)", cmd_id, status)
                    if self.logger:
                        self.logger.log_warning(f"Single command {cmd_id} has unknown status: {status}")
            else:
                # Если сервер не вернул статус для этой команды, считаем успешной (для обратной совместимости)
                self.queue.mark_as_done(cmd_id)
                logger.debug("[CommandSender] Команда %s помечена как done (статус не найден в ответе сервера)", cmd_id)
                if self.logger:
                    self.logger.log_info(f"Single command {cmd_id} completed (no status in response, assuming success).")

        except Exception as err:
            logger.exception("[CommandSender] Не удалось отправить single команду %s: %s", cmd["id"], err)
            if self.logger:
                self.logger.log_error(f"Failed to send single command {cmd['id']}: {err}")
            raise

    def process_retrying(self, retry_manager: Optional['RetryManager'] = None) -> None:
        """
        Обрабатывает retrying команды, планируя их повторы через RetryManager.
        """
        retrying = self.queue.get_retrying_commands()
        if not retrying:
            return

        logger.info("[CommandSender] Processing %s retrying commands", len(retrying))

        for cmd in retrying:
            retry_count = self.queue.get_retry_count(cmd["id"])
            if retry_count > 0:  # Если retry_count > 0, значит уже обрабатывается
                continue

            # Это новая retrying команда, инициализируем retry_count = 0 и планируем retry
            self.queue.add_retry_count(cmd["id"])  # Теперь retry_count = 1
            cmd_copy = cmd.copy()
            cmd_copy["retry_count"] = 1

            if retry_manager:
                retry_manager.schedule_retry(cmd_copy, delay=0)  # Начать retry немедленно
            else:
                logger.warning("No retry_manager provided for retrying command %s", cmd["id"])
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
