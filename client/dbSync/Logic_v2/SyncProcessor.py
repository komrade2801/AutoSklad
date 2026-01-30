from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import time
import threading
import traceback

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from DB.Data.db_depends import get_db
from DB.Data.sqlite_db import SessionLocal
# Sync layer components
from .SchemaCache import SchemaCache
from .SchemaAnalyzer import SchemaAnalyzer
from .MappingConfigurator import MappingConfigurator
from .DataMapper import DataMapper
from .DataTransformer import DataTransformer
from .ConflictManager import ConflictManager
# from .BatchProcessor import BatchProcessor
from .SyncMonitor import SyncMonitor
from .RetryManager import RetryManager, RetryCommand
from .JSONSchemaValidator import JSONSchemaValidator
from .DiagnosticLogger import DiagnosticLogger
from dbSync.Engines.CommandEngine import CommandCRUD, RecordCRUD
from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD
from dbSync.Engines.SyncConfigEngine import SyncConfigCRUD
from .SyncManager import SyncManager
import logging
logger = logging.getLogger(__name__)


class SyncProcessor:
    """
    Центральный координатор двухсторонней синхронизации между устройством (клиентом) и сервером.

    Архитектурное место:
      • Логический слой синхронизации (Logiс Layer).
      • Вызывается из CommandSender/CommandReceiver (push/pull).
      • Делегирует работу по каждому этапу специализированным компонентам:
          - SchemaCache, SchemaAnalyzer — handshake (согласование схем).
          - JSONSchemaValidator                  — валидация входящих/исходящих сообщений.
          - DataMapper, DataTransformer         — преобразование данных в обе стороны.
          - ConflictManager                      — обнаружение и разрешение конфликтов.
          - BatchProcessor, SyncManager          — атомарное применение CRUD-операций.
          - RetryManager                         — планирование повторных попыток.
          - SyncMonitor                          — сбор метрик успеха/ошибок.
          - DiagnosticLogger                     — подробное логирование.
          - CommandCRUD, RecordCRUD, CommandStatusCRUD, SyncConfigCRUD — доступ к БД.

    Основные этапы синхронизации:
      1. **handshake** (`process_schema`)
         - Клиент и сервер согласовывают структуру данных (mapping).
      2. **pull** (`prepare_pull`)
         - Сервер подготавливает набор команд и изменений для клиента.
      3. **push** (`process_push`)
         - Клиент отправляет на сервер локальные изменения; сервер их применяет.

    Поток вызовов (упрощённо):
        CommandSender -> SyncProcessor.process_schema()
        SyncProcessor -> JSONSchemaValidator -> SchemaAnalyzer/SchemaCache
        SyncProcessor -> SyncMonitor/DiagnosticLogger

        CommandReceiver -> SyncProcessor.prepare_pull()
        SyncProcessor -> CommandCRUD, RecordCRUD -> DataMapper -> DataTransformer
        SyncProcessor -> JSONSchemaValidator -> SyncMonitor/DiagnosticLogger

        CommandSender -> SyncProcessor.process_push()
        SyncProcessor -> DataTransformer -> ConflictManager -> BatchProcessor -> SyncManager
        SyncProcessor -> RetryManager -> SyncMonitor/DiagnosticLogger

    Зависимости:
      - `schema_cache: SchemaCache`
      - `schema_analyzer: SchemaAnalyzer`
      - `mapping_config: MappingConfigurator`
      - `data_mapper: DataMapper`
      - `data_transformer: DataTransformer`
      - `conflict_manager: ConflictManager`
      - `batch_processor: BatchProcessor`
      - CRUD-слои: `cmd_crud`, `record_crud`, `status_crud`, `sync_config_crud`
      - `sync_manager: SyncManager`
      - `retry_manager: RetryManager`
      - `json_validator: JSONSchemaValidator`
      - `sync_monitor: SyncMonitor`
      - `diagnostic_logger: DiagnosticLogger`
      - `db_session: Session`

    Входящие/исходящие данные:
      - **process_schema**
        Принимает: `src_schema: Dict[table,fields]`, `client_schema_hash: str`
        Возвращает: `{ mapping: Dict[...], schema_hash: str }`
      - **prepare_pull**
        Принимает: `device: int`, `since: ISO timestamp`, `client_schema_hash: str`
        Возвращает: `{ schema_hash: str, commands: List[{id,table,operation,data,last_modified}] }`
      - **process_push**
        Принимает: `device: int`, `commands: List[{...}]`, `client_schema_hash: str`
        Возвращает: `List[{id, status, error?}]`

    Исключения:
      - Все методы оборачивают внутренние ошибки и логируют трассировки через DiagnosticLogger, а также учитывают их в SyncMonitor.

    Блокировка:
      - Для защиты кэша и доступа к схеме используется единый `threading.Lock()`.

    Метрики:
      - `sync_monitor.record_success(duration)`
      - `sync_monitor.record_failure(duration)`

    Повторные попытки:
      - Неудачные операции push планируются через `retry_manager.schedule_retry()`

    """

    def __init__(
            self,
            queue,
            sender,
            schema_cache,
            schema_analyzer,
            mapping_config,
            data_mapper: DataMapper,
            data_transformer: DataTransformer,
            conflict_manager,
            batch_processor,
            cmd_crud,  # не используем здесь, но оставляем для совместимости
            record_crud,
            status_crud,
            sync_config_crud,
            diagnostic_logger: DiagnosticLogger,
            sync_monitor: SyncMonitor,
            retry_manager,
            json_validator: JSONSchemaValidator,
            sync_manager,
            server_schema: Dict[str, Dict[str, Any]],
            sync_session,  # передаётся обычная сессия для инициализации фабрики
            retry_attempts: int = 3,
            retry_delay: int = 60,
            emulate_server: bool = False,
            work_session=None
    ) -> None:
        """
        Инициализация SyncProcessor со всеми необходимыми зависимостями.

        :param schema_cache:      Кэш маппингов схем (SchemaCache).
        :param schema_analyzer:   Генератор маппингов (SchemaAnalyzer).
        :param mapping_config:    Ручная конфигурация при конфликтах (MappingConfigurator).
        :param data_mapper:       Преобразование полей JSON ↔ model (DataMapper).
        :param data_transformer:  Бизнес-правила пред/пост обработки (DataTransformer).
        :param conflict_manager:  Обнаружение/разрешение конфликтов (ConflictManager).
        :param batch_processor:   Атомарное выполнение CRUD (BatchProcessor).
        :param cmd_crud:          CRUD для команд (CommandCRUD).
        :param record_crud:       CRUD для записей (RecordCRUD).
        :param status_crud:       CRUD для статусов (CommandStatusCRUD).
        :param sync_config_crud:  CRUD включённых таблиц (SyncConfigCRUD).
        :param diagnostic_logger: Логгер с трассировками (DiagnosticLogger).
        :param sync_monitor:      Мониторинг успехов/неудач (SyncMonitor).
        :param retry_manager:     Планировщик повторов (RetryManager).
        :param json_validator:    Валидация по JSON-Схемам (JSONSchemaValidator).
        :param server_schema:     Определение текущей серверной схемы.
        :param sync_session:        SQLAlchemy Session для транзакций.
        :param retry_attempts:    Число попыток для неудач (по умолчанию 3).
        :param retry_delay:       Задержка между попытками в секундах (по умолчанию 60).
        :param emulate_server:    Флаг dev-режима эмуляции server-side.
        """
        # Основные компоненты
        # вместо единой сессии заводим фабрику сессий
        # 1) заводим фабрику новых сессий на основе переданной сессии

        work_engine = work_session.get_bind()
        self.work_session = sessionmaker(bind=work_engine)()
        sync_engine = sync_session.get_bind()
        self.sync_session = sessionmaker(bind=sync_engine)()

        # 2) отдельный лок для работы с кэшем схем
        self._schema_lock = threading.RLock()
        db: Session = Depends(get_db)
        # 3) дальше всё как прежде, но без единого db_session
        self.queue = queue
        self.sender = sender
        self.schema_cache = schema_cache
        self.schema_analyzer = schema_analyzer
        self.mapping_config = mapping_config
        self.data_mapper = data_mapper
        self.data_transformer = data_transformer
        self.conflict_manager = conflict_manager
        self.batch_processor = batch_processor
        self.cmd_crud = cmd_crud
        self.record_crud = record_crud
        self.status_crud = status_crud
        self.sync_config_crud = sync_config_crud

        self.diagnostic_logger = diagnostic_logger
        self.sync_monitor = sync_monitor
        self.retry_manager = retry_manager
        self.json_validator = json_validator

        self.sync_manager = sync_manager
        self.server_schema = server_schema
        self.current_schema_hash = None

        # старую сессию более не используем
        self.db_session = None
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.emulate_server = emulate_server

        logger.info("[SyncProcessor] Инициализирован.")

    def update_schema(self,
                      field_mappings: Dict[str, Dict[str, str]],
                      schema_hash: str) -> None:
        """
        Обновляет внутренний хэш и, при желании, серверную схему
        (если вы хотите менять server_schema на основании mapping).
        """
        try:
            self.current_schema_hash = schema_hash
            # Если вы хотите, чтобы SyncProcessor использовал mapping как
            # "новый" server_schema (например, bidirectional),
            # можете раскомментировать:
            self.server_schema = {
                table: {dst: src for src, dst in tbl_map.items()}
                for table, tbl_map in field_mappings.items()
            }
            logger.info("[SyncProcessor] Обновлены маппинги.")
        except Exception:
            logger.debug("[SyncProcessor] Список пуст.")

    def process_schema(
            self,
            src_schema: Dict[str, Dict[str, Any]],
            client_schema_hash: str
    ) -> Dict[str, Union[str, Dict[str, Dict[str, str]]]]:
        """
        Handshake: согласование схемы клиента и сервера.

        1. Валидация входящей схемы JSON
        2. Попытка взять mapping из cache по hash
        3. При отсутствии — генерируем новый mapping через SchemaAnalyzer
        4. Сохраняем mapping в cache
        5. Валидация исходящего payload
        6. Возвращаем mapping и хэш

        :param src_schema:           Клиентская схема {table: {field: type}}
        :param client_schema_hash:   SHA256-хэш схемы
        :return: {'mapping': {...}, 'schema_hash': client_schema_hash}
        :raises: Exception при любой ошибке, все детали логируются
        """
        start = time.time()
        try:
            self.diagnostic_logger.log_info("Handshake start", {"hash": client_schema_hash})
            # <<< ЗДЕСЬ>>
            # валидируем именно запрос от клиента
            self.json_validator.validate(src_schema, "handshake_request")

            with self._schema_lock:
                mapping = self.schema_cache.get(client_schema_hash)
                if mapping is None:
                    mapping = self.schema_analyzer.generate_mapping(src_schema, self.server_schema)
                    self.schema_cache.set(client_schema_hash, mapping)

            response = {"mapping": mapping, "schema_hash": client_schema_hash}
            self.json_validator.validate(response, "handshake_response")

            self.sync_monitor.record_success(time.time() - start)
            self.diagnostic_logger.log_info("Handshake completed", {"tables": list(mapping.keys())})
            logger.info("[SyncProcessor] Handshake completed.")
            return response

        except Exception as ex:
            logger.warning("[SyncProcessor] Handshake failed.")
            self.diagnostic_logger.log_error("Handshake failed", {
                "error": str(ex),
                "traceback": traceback.format_exc()
            })
            self.sync_monitor.record_failure(time.time() - start)
            raise

    def prepare_pull(
            self,
            device: int,
            since: str,
            client_schema_hash: str
    ) -> Dict[str, Any]:
        start = time.time()
        sync_session = None
        try:
            self.diagnostic_logger.log_info("Pull start", {"device": device, "since": since})

            # 1) Кратковременная блокировка только для схемы
            # with self._schema_lock:
            mapping = self._get_mapping(client_schema_hash)

            # 2) Новая сессия и CRUD
            sync_session = self.sync_session
            cmd_crud = CommandCRUD(session=sync_session)
            record_crud = RecordCRUD(session=sync_session)

            commands: List[Dict[str, Any]] = []
            # 3) Транзакция только для запросов в БД
            with cmd_crud.transaction(), record_crud.transaction():
                pending = cmd_crud.get_pending_for_device(device)
                records = record_crud.get_bulk_records([c.id for c in pending])

                for cmd in pending:
                    raw = records.get(cmd.id, {})
                    json_data = self.data_mapper.map_outgoing(cmd.table_name, raw)
                    post = self.data_transformer.postprocess(cmd.table_name, json_data)

                    # last_modified — в той же сессии, без отдельного lock
                    lm = None
                    rec = record_crud.get_last_for_command(cmd.id)
                    if rec and rec.last_modified:
                        lm = rec.last_modified.isoformat()

                    commands.append({
                        "id": cmd.id,
                        "table": cmd.table_name,
                        "operation": cmd.operation.upper(),
                        "data": post,
                        "last_modified": lm
                    })

            # 4) Закрываем сессию сразу после работы с БД
            return_data = {"schema_hash": client_schema_hash, "commands": commands}
            self.json_validator.validate(return_data, "pull_response")
            self.sync_monitor.record_success(time.time() - start)
            self.diagnostic_logger.log_info("Pull completed", {"count": len(commands)})
            logger.info("[SyncProcessor] Pull completed.")
            return return_data

        except Exception as ex:
            logger.warning("[SyncProcessor] Pull failed.")
            self.diagnostic_logger.log_error("Pull failed", {
                "error": str(ex),
                "traceback": traceback.format_exc()
            })
            self.sync_monitor.record_failure(time.time() - start)
            raise

        finally:
            if sync_session:
                sync_session.close()

    def process_push(
            self,
            device: int,
            commands: List[Dict[str, Any]],
            client_schema_hash: str
    ) -> List[Dict[str, Any]]:
        """
        Push-этап: приём и применение команд от клиента.

        1. Валидация входящего списка команд JSON
        2. Фильтрация дубликатов ADD‑операций по полному совпадению
        3. Подготовка операций:
           a) preprocess (DataTransformer)
           b) валидация (DataTransformer.validate)
           c) детект структурных конфликтов (ConflictManager)
           d) map incoming (DataMapper)
           e) postprocess (DataTransformer.postprocess)
           f) detect & resolve data conflicts (ConflictManager)
        4. Пакетная отправка операций в БД (BatchProcessor.execute_batch)
        5. Обновление статусов команд (CommandStatusCRUD)
        6. Планирование retry для неудач (RetryManager)
        7. Сбор метрик и логирование

        :param device:               ID устройства
        :param commands:             Список команд от клиента
        :param client_schema_hash:   Хэш схемы
        :return: Список статусов {'id': ..., 'status': ..., 'error'?: ...}
        :raises: Exception при критических ошибках
        """
        start = time.time()
        try:
            # 1. Начало и лог
            logger.info("[SyncProcessor] Начало push-этапа. Устройство: %s, Команд: %s", device, len(commands))
            self.diagnostic_logger.log_info("Push start", {"device": device, "count": len(commands)})

            # 2. Валидация JSON
            self.json_validator.validate({"commands": commands}, "push_commands")
            logger.debug("[SyncProcessor] Валидация JSON завершена.")

            # 3. Основная транзакция по командам
            with self._schema_lock, self.cmd_crud.transaction(), self.status_crud.transaction():
                logger.debug("[SyncProcessor] Транзакция начата. Устройство: %s", device)
                mapping = self._get_mapping(client_schema_hash)
                ops, failed, skipped_results = [], [], []

                # 5. Подготовка операций
                logger.debug("[SyncProcessor] Начало обработки %s команд.", len(commands))
                for cmd in commands:
                    if not self.sync_config_crud.get_status(cmd["table"]):
                        logger.debug("[SyncProcessor] Таблица %s отключена - пропуск.", cmd["table"])
                        continue

                    # 5a-b. Препроцессинг и валидация
                    cleaned = self.data_transformer.preprocess(cmd["table"], cmd.get("data", {}))
                    if not self.data_transformer.validate(cmd["table"], cleaned):
                        logger.warning("[SyncProcessor] Ошибка валидации в таблице %s.", cmd["table"])
                        failed.append(cmd)
                        continue

                    # 5c-f. Обработка команды
                    op_result = self._process_single(cmd, mapping)
                    if op_result.get("skipped"):
                        skipped_results.append(op_result)
                    elif not op_result["success"]:
                        logger.warning("[SyncProcessor] Конфликт/ошибка в команде %s.", cmd.get("id"))
                        failed.append(op_result)
                    else:
                        ops.append(op_result)

                logger.debug("[SyncProcessor] Подготовлено операций: %s, пропущено: %s, неудач: %s.", len(ops), len(skipped_results), len(failed))

                # 6. Пакетное выполнение
                logger.debug("[SyncProcessor] Запуск пакетной обработки.")
                results = self.batch_processor.execute_batch(ops)
                # Пропущенные считаем успешно принятыми (COMPLETED), чтобы сервер не пересылал
                results = results + [{"command_id": r["command_id"], "success": True} for r in skipped_results]
                logger.debug("[SyncProcessor] Пакетная обработка завершена. Результатов: %s.", len(results))

                # 7. Обновление статусов
                logger.debug("[SyncProcessor] Обновление статусов команд.")
                statuses = self._update_command_statuses(results)

                # 8. Планирование повторов
                if failed:
                    logger.info("[SyncProcessor] Планирование %s повторов.", len(failed))
                    for cmd in failed:
                        retry_cmd: RetryCommand = {
                            "id": cmd["id"],
                            "table": cmd["table"],
                            "operation": cmd["operation"],
                            "data": cmd["data"],
                            "status": "failed",
                            "timestamp": datetime.utcnow().isoformat(),
                            "retry_count": 0
                        }
                        self.retry_manager.schedule_retry(retry_cmd, self.retry_delay)

                # 9. Фиксация транзакции
                logger.debug("[SyncProcessor] Фиксация изменений. Устройство: %s.", device)

            # 10. Успешный лог и возврат
            self.sync_monitor.record_success(time.time() - start)
            logger.info("[SyncProcessor] Push завершен успешно. Время: %.2fс.", time.time() - start)
            self.diagnostic_logger.log_info("Push completed", {"statuses": statuses})
            return statuses

        except Exception as ex:
            # общий обработчик ошибок
            logger.exception("[SyncProcessor] ОШИБКА PUSH: %s", ex)
            self.diagnostic_logger.log_error("Push failed", {
                "error": str(ex),
                "traceback": traceback.format_exc()
            })
            self.sync_monitor.record_failure(time.time() - start)
            raise

    # ——————————————————————————————————————————————————————————————————————————————

    def _get_mapping(self, client_schema_hash: str) -> Dict[str, Dict[str, str]]:
        """
        Получить или сгенерировать маппинг схемы по hash.
        Локальный fallback: src_schema=dst_schema=server_schema.

        :raises: Exception при ошибках доступа к cache/analyzer
        """
        mapping = self.schema_cache.get(client_schema_hash)
        if mapping is None:
            self.diagnostic_logger.log_info("Mapping miss, generating new", {"hash": client_schema_hash})
            mapping = self.schema_analyzer.generate_mapping(self.server_schema, self.server_schema)
            self.schema_cache.set(client_schema_hash, mapping)
        logger.info("[SyncProcessor] Mapping loaded.")
        return mapping

    def _process_single(self, cmd: Dict[str, Any], mapping: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Обработка одной команды:
         - preprocess → validate
         - detect_structure_conflict → on_conflict → update mapping
         - map_incoming → postprocess
         - detect_data_conflict → resolve

        :return: {'command_id', 'table', 'operation','data','id','success', 'skipped'?, 'error'?}
        """
        try:
            table = cmd["table"]
            raw = cmd.get("data", {})
            # Нормализация ID входящей команды: сервер может слать 'index', 'id' или оба
            rec_id = raw.get("id") or raw.get("index")

            # DIAGNOSTIC LOGGING: Record ID extraction and source
            logger.debug("[DIAGNOSTIC][CLIENT] Command ID extraction: raw.id=%s, raw.index=%s, rec_id=%s", raw.get("id"), raw.get("index"), rec_id)
            logger.debug("[DIAGNOSTIC][CLIENT] Raw data keys: %s", list(raw.keys()))

            if rec_id is None:
                self.diagnostic_logger.log_warning("IGNORED REMOTE UPDATE: No record id in command", {"table": table, "command_id": cmd.get("id")})
                return {
                    "command_id": cmd.get("id"),
                    "id": None,
                    "table": table,
                    "operation": cmd.get("operation"),
                    "data": {},
                    "success": True,
                    "skipped": True,
                }

            is_pull_command = cmd.get("last_modified") is not None
            # Железобетонная блокировка по Pending: id и index считаем одной записью, сравнение как строки
            if is_pull_command and hasattr(self, "queue") and self.queue:
                pending_commands = self.queue.get_pending_commands() + self.queue.get_retrying_commands()
                is_locked = False
                for p_cmd in pending_commands:
                    if p_cmd.get("table") != table:
                        continue
                    p_data = p_cmd.get("data", {})
                    p_id = p_data.get("id") or p_data.get("index")
                    if str(p_id) == str(rec_id):
                        is_locked = True
                        break
                if is_locked:
                    self.diagnostic_logger.log_warning(
                        "IGNORED REMOTE UPDATE: Local pending changes exist",
                        {"table": table, "id": rec_id, "command_id": cmd.get("id")},
                    )
                    return {
                        "command_id": cmd.get("id"),
                        "id": rec_id,
                        "table": table,
                        "operation": cmd.get("operation"),
                        "data": {},
                        "success": True,
                        "skipped": True,
                    }

            cleaned = self.data_transformer.preprocess(table, raw)
            if not self.data_transformer.validate(table, cleaned):
                return {"command_id": cmd.get("id"), "success": False, "error": "Validation failed"}

            # struct conflicts
            server_fields = list(self.server_schema.get(table, {}))
            conflicts = self.conflict_manager.detect_structure_conflict(list(cleaned), server_fields)
            if conflicts:
                new_map = self.mapping_config.on_conflict(src_table=table, dst_table=conflicts, ambiguous_fields=None)
                mapping.setdefault(table, {}).update(new_map)

            # map & postprocess
            local = self.data_mapper.map_incoming(table, cleaned, mapping.get(table, {}))
            local = self.data_transformer.postprocess(table, local)
            cmd["data"] = local
            index = local.get("id") or local.get("index") or rec_id

            # DIAGNOSTIC LOGGING: Existing data lookup
            logger.debug("[DIAGNOSTIC][CLIENT] Processed data keys: %s, chosen index=%s", list(local.keys()), index)
            logger.debug("[DIAGNOSTIC][CLIENT] About to lookup existing data for table=%s, rec_id=%s", table, index)

            existing = self.sync_manager.get_current_data(table=table, work_session=SessionLocal(), rec_id=index)
            logger.debug("[DIAGNOSTIC][CLIENT] Existing data lookup result: %s", existing)

            # Защита "Time Travel": если локальная запись новее серверной — не перезаписываем
            remote_ts_str = cmd.get("last_modified")
            if existing and remote_ts_str:
                local_ts = existing.get("updated_at") or existing.get("datetime") or existing.get("date")
                if local_ts:
                    try:
                        local_dt = (
                            datetime.fromisoformat(str(local_ts).replace("Z", "+00:00"))
                            if isinstance(local_ts, str)
                            else local_ts
                        )
                        remote_dt = datetime.fromisoformat(str(remote_ts_str).replace("Z", "+00:00"))
                        if local_dt > remote_dt:
                            self.diagnostic_logger.log_warning(
                                "IGNORED OBSOLETE: Local data is newer",
                                {"table": table, "id": index, "local_ts": str(local_dt), "remote_ts": str(remote_dt)},
                            )
                            return {
                                "command_id": cmd.get("id"),
                                "id": index,
                                "table": table,
                                "operation": cmd.get("operation"),
                                "data": {},
                                "success": True,
                                "skipped": True,
                            }
                    except (ValueError, TypeError):
                        pass

            if existing and self.conflict_manager.detect_data_conflict(existing, local):
                logger.debug("[DIAGNOSTIC][CLIENT] Data conflict detected, applying strategy")
                remote_stype = None
                if getattr(self.sync_manager, "get_status_stype", None) and local.get("status_id") is not None:
                    remote_stype = self.sync_manager.get_status_stype(local.get("status_id"))
                
                # Для Cell также получаем локальный stype для защиты активных операций
                local_stype = None
                if table == "Cell" and existing.get("status_id"):
                    local_stype = self.sync_manager.get_status_stype(existing.get("status_id"))
                
                local = self.conflict_manager.apply_data_strategy(
                    existing, local, 
                    remote_status_stype=remote_stype,
                    table=table,  # Передаем имя таблицы для специальной логики Cell
                    local_status_stype=local_stype  # Передаем локальный stype для защиты активных операций
                )
            else:
                logger.debug("[DIAGNOSTIC][CLIENT] No data conflict or no existing record")

            logger.debug("[SyncProcessor] Command processed.")
            logger.debug("[DIAGNOSTIC][CLIENT] Final result: success=True, rec_id=%s", index)

            return {
                "command_id": cmd.get("id"),
                "id": index,
                "table": table,
                "operation": cmd["operation"],
                "data": local,
                "success": True,
            }
        except Exception as ex:
            logger.exception("[SyncProcessor] Одиночная команда не удалась.")
            self.diagnostic_logger.log_error("Одиночная команда не удалась", {
                "command": cmd, "error": str(ex), "traceback": traceback.format_exc()
            })
            return {
                "command_id": cmd.get("id"),
                "id": cmd.get("id"),
                "table": cmd.get("table"),
                "operation": cmd.get("operation"),
                "data": cmd.get("data"),
                "success": False,
                "error": str(ex)
            }

    def _update_command_statuses(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обновляет статусы команд в базе по результатам batch-processor.

        :return: [{'id': ..., 'status': 'COMPLETED'|'FAILED', 'error'?}, …]
        """
        statuses = []
        for r in results:
            cmd_id, ok = r["command_id"], r.get("success", False)
            status = "COMPLETED" if ok else "FAILED"
            self.status_crud.add_status(cmd_id, status)
            entry = {"id": cmd_id, "status": status}
            if not ok: entry["error"] = r.get("error")
            statuses.append(entry)
        logger.debug("[SyncProcessor] Statuses updated.")
        return statuses

    def _get_last_modified(
            self,
            command_id: int,
            session
    ) -> Optional[str]:
        """
        Получает ISO-строку последней модификации команды, используя переданную сессию.

        :param command_id:  ID команды
        :param session:     SQLAlchemy Session, внутри которой уже открыта транзакция
        :return:            ISO-строка или None
        """
        # создаём CRUD-обёртку поверх той же сессии
        record_crud = RecordCRUD(session=session)
        try:
            # пытаемся достать самую свежую запись
            rec = record_crud.get_last_for_command(command_id)
            timestamp = rec.last_modified.isoformat() if rec and rec.last_modified else None
        except Exception:
            # если что-то пошло не так, возвращаем None
            timestamp = None

        logger.debug("[SyncProcessor] Last modified fetched for cmd=%s: %s", command_id, timestamp)
        return timestamp

    def emulate_server_push(self, commands: List[Dict[str, Any]], client_schema_hash: str) -> List[Dict[str, Any]]:
        """
        Dev-режим: эмулирует поведение сервера, вызывая process_push с device=0.
        """
        try:
            self.diagnostic_logger.log_info("Emulate server push", {"count": len(commands)})
            logger.info("[SyncProcessor] Emulate server push.")
            return self.process_push(device=0, commands=commands, client_schema_hash=client_schema_hash)
        except Exception:
            logger.exception("[SyncProcessor] Emulate push failed.")
            self.diagnostic_logger.log_error("Emulate push failed", {"traceback": traceback.format_exc()})
            raise

    def enqueue_local_command(self, cmd: Dict[str, Any]) -> None:
        """
        Получает одну локальную команду от декоратора и кладёт её
        в очередь CommandQueue, чтобы позже отправить на сервер.
        """
        try:

            self.queue.add_command(
                table=cmd["table"],
                operation=cmd["operation"],
                data=cmd["data"]
            )
            self.diagnostic_logger.log_info(
                "Local command enqueued",
                {"table": cmd["table"], "operation": cmd["operation"]}
            )
            logger.info("[SyncProcessor] Команда поставлена в очередь. table: %s, operation: %s", cmd["table"], cmd["operation"])
        except Exception as e:
            logger.exception("[SyncProcessor] Не удалось поставить локальную команду в очередь: %s", e)
            self.diagnostic_logger.log_error(
                "Не удалось поставить локальную команду в очередь.",
                {"error": str(e), "traceback": traceback.format_exc()}
            )
