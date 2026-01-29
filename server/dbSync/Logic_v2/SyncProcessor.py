from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import time
import threading
import traceback

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

# from DB.Data.db_depends import get_db
from DB.session import get_db, get_db_session
# from DB.session import SessionLocal
# from DB.Data.sqlite_db import SessionLocal
# Sync layer components
# from .SchemaCache import SchemaCache
# from .SchemaAnalyzer import SchemaAnalyzer
# from .MappingConfigurator import MappingConfigurator
from .DataMapper import DataMapper
from .DataTransformer import DataTransformer
# from .ConflictManager import ConflictManager
# from .BatchProcessor import BatchProcessor
from .SyncMonitor import SyncMonitor
from .RetryManager import RetryCommand  # RetryManager,
from .JSONSchemaValidator import JSONSchemaValidator
from .DiagnosticLogger import DiagnosticLogger
from .CommandOrderer import CommandOrderer
# from docs.docs import CommandCRUD, RecordCRUD
# from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD
# from dbSync.Engines.SyncConfigEngine import SyncConfigCRUD
# from .SyncManager import SyncManager
import logging

from ..Engines.CommandEngine import CommandCRUD
from ..Engines.RecordEngine import RecordCRUD

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
        self.current_device_id = None
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
        
        # CommandOrderer для валидации и упорядочивания команд
        self.command_orderer = CommandOrderer(logger=diagnostic_logger)
        self.json_validator = json_validator

        self.sync_manager = sync_manager
        self.server_schema = server_schema
        self.current_schema_hash = None

        # старую сессию более не используем
        self.db_session = None
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.emulate_server = emulate_server

        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Инициализирова'              f'н. [{datetime.now()}]')

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
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Обновлены маппинги. [{datetime.now()}]')
        except:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Список пуст. [{datetime.now()}]')

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
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Handshake completed. [{datetime.now()}]')
            return response

        except Exception as ex:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Handshake failed. [{datetime.now()}]')
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
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor][prepare_pull] Найдено {len(pending)} pending команд для device={device}. [{datetime.now()}]')
                for cmd in pending:
                    print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor][prepare_pull]   - Команда ID={cmd.id}, table={cmd.table_name}, operation={cmd.operation}, record_id={cmd.record_id}')
                records = record_crud.get_bulk_records([c.id for c in pending])

                for cmd in pending:
                    # Для DELETE операций используем cmd.record_id напрямую, так как DELETE не требует полных данных
                    if cmd.operation.upper() == "DELETE":
                        # Для DELETE используем record_id из команды
                        post = {"index": cmd.record_id} if cmd.record_id else {}
                        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor][prepare_pull] DELETE команда: table={cmd.table_name}, record_id={cmd.record_id}, data={post}')
                    else:
                        # Для ADD/UPDATE используем данные из Record
                        raw = records.get(cmd.id, {})
                        json_data = self.data_mapper.map_outgoing(cmd.table_name, raw)
                        post = self.data_transformer.postprocess(cmd.table_name, json_data)

                    # last_modified — в той же сессии, без отдельного lock
                    lm = None
                    rec = record_crud.get_last_for_command(cmd.id)
                    if rec and rec.last_modified:
                        lm = rec.last_modified.isoformat()

                    commands.append({
                        "id": str(cmd.id),  # Преобразуем ID в строку для соответствия схеме валидации
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
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Pull completed at {datetime.now()}')
            return return_data

        except Exception as ex:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Pull failed at {datetime.now()}')
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
            # сохраняем текущий device
            self.current_device_id = device

            # 1. Начало и лог
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Начало push-этапа. Устройство: {device}, Команд: {len(commands)}. [{datetime.now()}]')
            self.diagnostic_logger.log_info("Push start", {"device": device, "count": len(commands)})

            # 2. Валидация JSON
            self.json_validator.validate({"commands": commands}, "push_commands")
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Валидация JSON завершена. [{datetime.now()}]')
            
            # 2.5. ═══ ВАЛИДАЦИЯ И УПОРЯДОЧИВАНИЕ КОМАНД ═══
            original_count = len(commands)
            ordered_commands, orderer_warnings = self.command_orderer.order_and_validate(commands)

            if orderer_warnings:
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] '
                      f'CommandOrderer validation warnings ({len(orderer_warnings)}):')
                for i, warn in enumerate(orderer_warnings[:10], 1):
                    print(f'  {i}. ⚠️  {warn}')
                if len(orderer_warnings) > 10:
                    print(f'  ... и ещё {len(orderer_warnings) - 10} warnings')

                self.diagnostic_logger.log_warning("Command order validation", {
                    "warnings_count": len(orderer_warnings),
                    "warnings": orderer_warnings[:5]
                })

            if len(ordered_commands) < original_count:
                compressed_count = original_count - len(ordered_commands)
                compression_ratio = compressed_count / original_count if original_count > 0 else 0

                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] '
                      f'CommandOrderer оптимизировал команды: {original_count} → {len(ordered_commands)} '
                      f'(удалено {compressed_count}, сжатие {compression_ratio:.1%})')

                self.diagnostic_logger.log_info("Commands optimized by CommandOrderer", {
                    "original_count": original_count,
                    "optimized_count": len(ordered_commands),
                    "compressed_count": compressed_count,
                    "compression_ratio": f"{compression_ratio:.1%}"
                })

            commands = ordered_commands

            if not commands:
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] '
                      f'Нет команд после оптимизации CommandOrderer, выходим.')
                return []
            # ═══════════════════════════════════════════

            # 3. Основная транзакция по командам
            with self._schema_lock, self.cmd_crud.transaction(), self.status_crud.transaction():
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] ' f'Транзакция начата. Устройство: {device}. [{datetime.now()}]')
                mapping = self._get_mapping(client_schema_hash)
                ops, failed = [], []

                # 5. Подготовка операций
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] ' f'Начало обработки {len(commands)} команд. [{datetime.now()}]')
                for cmd in commands:
                    if not self.sync_config_crud.get_status(cmd["table"]):
                        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] ' f'Таблица {cmd["table"]} отключена - пропуск. [{datetime.now()}]')
                        continue

                    # 5a-b. Препроцессинг и валидация
                    cleaned = self.data_transformer.preprocess(cmd["table"], cmd.get("data", {}))
                    if not self.data_transformer.validate(cmd["table"], cleaned):
                        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Ошибка валидации в таблице {cmd["table"]}. [{datetime.now()}]')
                        failed.append(cmd)
                        continue

                    # 5c-f. Обработка команды
                    op_result = self._process_single(cmd, mapping)
                    if not op_result["success"]:
                        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Конфликт/ошибка в команде {cmd.get("id")}. [{datetime.now()}]')
                        failed.append(op_result)
                    else:
                        ops.append(op_result)

                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Подготовлено операций: {len(ops)}, неудач: {len(failed)}. [{datetime.now()}]')

                # 6. Пакетное выполнение
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Запуск пакетной обработки. [{datetime.now()}]')
                results = self.batch_processor.execute_batch(ops)
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Пакетная обработка завершена. Результатов: {len(results)}. [{datetime.now()}]')

                # 7. Обновление статусов
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Обновление статусов команд. [{datetime.now()}]')
                statuses = self._update_command_statuses(results)

                # 8. Планирование повторов
                if failed:
                    print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Планирование {len(failed)} повторов. [{datetime.now()}]')
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
                print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Фиксация изменений. Устройство: {device}. [{datetime.now()}]')

            # 10. Успешный лог и возврат
            self.sync_monitor.record_success(time.time() - start)
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Push завершен успешно. Время: {time.time() - start:.2f}с. [{datetime.now()}]')
            self.diagnostic_logger.log_info("Push completed", {"statuses": statuses})
            return statuses

        except Exception as ex:
            # общий обработчик ошибок
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'ОШИБКА PUSH: {str(ex)}. [{datetime.now()}]')
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
        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Mapping loaded. [{datetime.now()}]')
        return mapping

    def _process_single(self, cmd: Dict[str, Any], mapping: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Обработка одной команды:
         - preprocess → validate
         - detect_structure_conflict → on_conflict → update mapping
         - map_incoming → postprocess
         - detect_data_conflict → resolve

        :return: {'command_id', 'table', 'operation','data','id','success', 'error'?}
        """
        try:
            table = cmd["table"]
            rec_id = cmd.get("id")
            raw = cmd.get("data", {})

            # DIAGNOSTIC LOGGING: Record ID extraction and source
            print(f'[DIAGNOSTIC][SERVER] Command ID extraction: cmd.get("id")={cmd.get("id")}, final rec_id={rec_id}')
            print(f'[DIAGNOSTIC][SERVER] Raw data keys: {list(raw.keys())}')
            print(f'[DIAGNOSTIC][SERVER] Current device ID: {self.current_device_id}')

            cleaned = self.data_transformer.preprocess(table, raw)
            if not self.data_transformer.validate(table, cleaned):
                return {"command_id": cmd["id"], "success": False, "error": "Validation failed"}

            # struct conflicts
            server_fields = list(self.server_schema.get(table, {}))
            conflicts = self.conflict_manager.detect_structure_conflict(list(cleaned), server_fields)
            if conflicts:
                new_map = self.mapping_config.on_conflict(src_table=table, dst_table=conflicts, ambiguous_fields=None)
                mapping.setdefault(table, {}).update(new_map)

            # map & postprocess
            local = self.data_mapper.map_incoming(table, cleaned, mapping.get(table, {}))
            local = self.data_transformer.postprocess(table, local)
            # Используем только обработанные данные (local), а не raw, чтобы избежать попадания необработанных полей типа Status
            # raw может содержать вложенные объекты, которые уже обработаны в DataTransformer
            cmd['data'] = local

            # DIAGNOSTIC LOGGING: Existing data lookup
            print(f'[DIAGNOSTIC][SERVER] Processed data keys: {list(local.keys())}')
            print(f'[DIAGNOSTIC][SERVER] About to lookup existing data for table={table}, rec_id={rec_id}')

            # data conflicts
            existing = self.sync_manager.get_current_data(table=table, work_session=get_db_session(), rec_id=rec_id)
            print(f'[DIAGNOSTIC][SERVER] Existing data lookup result: {existing}')

            if existing and self.conflict_manager.detect_data_conflict(existing, local):
                print('[DIAGNOSTIC][SERVER] Data conflict detected, applying strategy')
                local = self.conflict_manager.apply_data_strategy(existing, local)
            else:
                print('[DIAGNOSTIC][SERVER] No data conflict or no existing record')

            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Command processed. [{datetime.now()}]')
            print(f'[DIAGNOSTIC][SERVER] Final result: success=True, rec_id={rec_id}')

            return {
                "command_id": cmd["id"],
                "id": rec_id,
                "table": table,
                "operation": cmd["operation"],
                "data": local,
                "success": True
            }
        except Exception as ex:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Одиночная команда не удалась. Подробности: {traceback.format_exc()} [{datetime.now()}]')
            self.diagnostic_logger.log_error("Одиночная команда не удалась", {
                "command": cmd, "error": str(ex), "traceback": traceback.format_exc()
            })
            # return {"command_id": cmd.get("id"), "success": False, "error": str(ex)}
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
        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Statuses updated. [{datetime.now()}]')
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

        print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] 'f'Last modified fetched for cmd={command_id}: {timestamp} at {datetime.now()}')
        return timestamp

    def emulate_server_push(self, commands: List[Dict[str, Any]], client_schema_hash: str) -> List[Dict[str, Any]]:
        """
        Dev-режим: эмулирует поведение сервера, вызывая process_push с device=0.
        """
        try:
            self.diagnostic_logger.log_info("Emulate server push", {"count": len(commands)})
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Emulate server push. [{datetime.now()}]')
            return self.process_push(device=0, commands=commands, client_schema_hash=client_schema_hash)
        except Exception:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Emulate push failed. [{datetime.now()}]')
            self.diagnostic_logger.log_error("Emulate push failed", {"traceback": traceback.format_exc()})
            raise

    def enqueue_local_command(self, cmd: Dict[str, Any]) -> None:
        """
        Получает одну локальную команду от декоратора и кладёт её
        в очередь CommandQueue, чтобы позже отправить на сервер.
        Также создаёт запись в таблице Command для синхронизации с клиентом.
        """
        try:
            # Добавляем команду в локальную очередь для отправки на сервер
            self.queue.add_command(
                table=cmd["table"],
                operation=cmd["operation"],
                data=cmd["data"]
            )
            
            # Создаём запись в таблице Command для синхронизации с клиентом
            # Это необходимо для того, чтобы клиент мог получить изменения через pull
            record_id = cmd["data"].get("id") or cmd["data"].get("index")
            if record_id and self.current_device_id:
                import json
                try:
                    data_json = json.dumps(cmd["data"], ensure_ascii=False)
                    operation = cmd["operation"].upper()
                    if operation == "UPDATE":
                        operation = "UPDATE"
                    elif operation in ("ADD", "INSERT"):
                        operation = "ADD"
                    elif operation == "DELETE":
                        operation = "DELETE"
                    
                    self.cmd_crud.add_command(
                        table_name=cmd["table"],
                        operation=operation,
                        record_id=record_id,
                        device_number=self.current_device_id,
                        data_json=data_json
                    )
                    print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Команда создана в таблице Command. table={cmd["table"]}, operation={operation}, record_id={record_id}, device_number={self.current_device_id} [{datetime.now()}]')
                except Exception as cmd_error:
                    print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Ошибка создания команды в таблице Command: {cmd_error} [{datetime.now()}]')
                    # Не прерываем выполнение, так как команда уже добавлена в локальную очередь
            
            self.diagnostic_logger.log_info(
                "Local command enqueued",
                {"table": cmd["table"], "operation": cmd["operation"]}
            )
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Команда поставлена в очередь. data: {cmd["data"]}'f'table: {cmd["table"]}, operation: {cmd["operation"]} [{datetime.now()}]')
        except Exception as e:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncProcessor] Не удалось поставить локальную команду в очередь. [{datetime.now()}]')
            self.diagnostic_logger.log_error(
                "Не удалось поставить локальную команду в очередь.",
                {"error": str(e), "traceback": traceback.format_exc()}
            )
