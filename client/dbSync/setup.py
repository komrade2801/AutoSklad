from __future__ import annotations

import datetime
import threading
import logging

from DB.Data.sqlite_db import SessionLocal, engine
from dbSync.Logic_v2.SyncProcessor import SyncProcessor

from dbSync.Logic_v2.utils import SERVER_SCHEMA, init_sync_config_table
from apscheduler.schedulers.background import BackgroundScheduler
import traceback

# import time
logger = logging.getLogger(__name__)


# def init_crud():
#
#     # CRUD-слои
#     cmd_crud = CommandCRUD(SessionLocal(engine()))
#     record_crud = RecordCRUD(SessionLocal(engine()))
#     status_crud = CommandStatusCRUD(SessionLocal(engine()))
#     sync_cfg = SyncConfigCRUD(SessionLocal(engine()))
#     print('[setup]init_crud')
#     return cmd_crud, record_crud, status_crud, sync_cfg

def init_crud():
    from dbSync.Engines.CommandEngine import CommandCRUD
    from dbSync.Engines.RecordEngine import RecordCRUD
    from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD
    from dbSync.Engines.SyncConfigEngine import SyncConfigCRUD
    # --- Импорты компонентов синхронизации ---
    from dbSync.Model.sync_sqlite import SyncSession

    sync_session = SyncSession()
    cmd_crud = CommandCRUD(session=sync_session)
    record_crud = RecordCRUD(sync_session)
    status_crud = CommandStatusCRUD(sync_session)
    sync_cfg = SyncConfigCRUD(sync_session)
    print('[setup]init_crud')
    return cmd_crud, record_crud, status_crud, sync_cfg


def init_snapshot_crud():
    """Initialize CommandSnapshot CRUD engine for rollback snapshots"""
    try:
        from dbSync.Engines.CommandSnapshotEngine import CommandSnapshotCRUD
        from dbSync.Model.sync_sqlite import SyncSession
        
        sync_session = SyncSession()
        snapshot_crud = CommandSnapshotCRUD(session=sync_session)
        print('[setup]init_snapshot_crud')
        return snapshot_crud
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_snapshot_crud][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
        return None


def init_batch_execution_crud():
    """Initialize BatchExecution CRUD engine for batch tracking"""
    try:
        from dbSync.Engines.BatchExecutionEngine import BatchExecutionCRUD
        from dbSync.Model.sync_sqlite import SyncSession
        
        sync_session = SyncSession()
        batch_crud = BatchExecutionCRUD(session=sync_session)
        print('[setup]init_batch_execution_crud')
        return batch_crud
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_batch_execution_crud][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
        return None


def init_idempotency_token_crud():
    """Initialize IdempotencyToken CRUD engine for duplicate prevention"""
    try:
        from dbSync.Engines.IdempotencyTokenEngine import IdempotencyTokenCRUD
        from dbSync.Model.sync_sqlite import SyncSession
        
        sync_session = SyncSession()
        token_crud = IdempotencyTokenCRUD(session=sync_session)
        print('[setup]init_idempotency_token_crud')
        return token_crud
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_idempotency_token_crud][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
        return None


def init_snapshot_manager(snapshot_crud, work_session, sync_manager, diagnostic_logger, scheduler):
    """Initialize SnapshotManager for rollback compensation"""
    try:
        from dbSync.Logic_v2.SnapshotManager import SnapshotManager
        
        snapshot_manager = SnapshotManager(
            snapshot_crud=snapshot_crud,
            work_session=work_session,
            sync_manager=sync_manager,
            _logger=diagnostic_logger
        )
        
        # Schedule automatic cleanup (daily at 3 AM)
        if scheduler:
            scheduler.add_job(
                func=snapshot_manager.cleanup_old_snapshots,
                trigger='cron',
                hour=3,
                minute=0,
                args=[30],  # 30 days retention
                id='snapshot_cleanup',
                replace_existing=True
            )
        
        print('[setup]init_snapshot_manager')
        return snapshot_manager
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_snapshot_manager][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
        return None


def init_idempotency_manager(token_crud, diagnostic_logger, scheduler):
    """Initialize IdempotencyManager for duplicate prevention"""
    try:
        from dbSync.Logic_v2.IdempotencyManager import IdempotencyManager
        
        idempotency_manager = IdempotencyManager(
            token_crud=token_crud,
            _logger=diagnostic_logger
        )
        
        # Schedule automatic cleanup (daily at 4 AM)
        if scheduler:
            scheduler.add_job(
                func=idempotency_manager.cleanup_old_tokens,
                trigger='cron',
                hour=4,
                minute=0,
                args=[7],  # 7 days retention
                id='token_cleanup',
                replace_existing=True
            )
        
        print('[setup]init_idempotency_manager')
        return idempotency_manager
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_idempotency_manager][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
        return None


def init_retry_manager(scheduler, queue, sender, diagnostic_logger):
    from .Logic_v2.RetryManager import RetryManager
    retry_manager = RetryManager(
        scheduler=scheduler,
        queue=queue,
        sender=sender,
        _logger=diagnostic_logger,
        base_delay=60.0,  # или другое значение
        max_retries=5  # или другое значение
    )
    print('[setup]init_retry_manager')
    return retry_manager


def init_transport_service(host, token="<YOUR_JWT_TOKEN>", secret=b"supersecret", aes=b"16byteslongkey!!", Port=""):
    from .Logic_v2.TransportService import TransportService
    if host and not host.startswith("http"):
        host = f"http://{host}"
    transport = TransportService(
        base_url=host,
        jwt_token=token,
        hmac_secret=secret,
        aes_key=aes,
        port=Port
    )
    print('[setup]init_transport_service')
    return transport


def init_scheduler() -> BackgroundScheduler:
    """
    Возвращаем BackgroundScheduler, в котором "default" executor
    уже создан до шатаута Python.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor as APS_ThreadPoolExecutor
    # Создаём ThreadPoolExecutor до того, как интерпретатор начнёт завершаться
    executor = APS_ThreadPoolExecutor()
    # Передаём его в APScheduler. Ключ 'default' совпадает с именем по умолчанию,
    # поэтому APScheduler не будет вызывать _create_default_executor().
    scheduler = BackgroundScheduler(executors={'default': executor})
    print('[setup] init_scheduler (custom executor)')
    return scheduler


def init_schema_cache():
    try:
        from .Logic_v2.SchemaCache import SchemaCache
        schema_cache = SchemaCache()
        print('[setup]init_schema_cache')
        return schema_cache
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_schema_cache][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_schema_analyzer():
    try:
        from .Logic_v2.SchemaAnalyzer import SchemaAnalyzer
        schema_analyzer = SchemaAnalyzer()
        print('[setup]init_schema_analyzer')
        return schema_analyzer
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_schema_analyzer][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_mapping_config():
    try:
        from .Logic_v2.MappingConfigurator import MappingConfigurator
        mapping_config = MappingConfigurator()
        print('[setup]init_mapping_config')
        return mapping_config
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_mapping_config][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_data_mapper():
    try:
        from .Logic_v2.DataMapper import DataMapper
        import os
        import json

        base = os.path.dirname(__file__)
        path = os.path.join(base, "Logic_v2", "cache", "fields", "sync_fields.json")
        if not os.path.exists(path):
             print(f"[setup][init_data_mapper] WARNING: mapping file not found at {path}, using empty mappings")
             field_mappings = {}
        else:
             field_mappings = json.load(open(path, encoding="utf-8"))

        mapper = DataMapper(field_mappings=field_mappings)
        print(f'[setup]init_data_mapper (loaded fields from {path})')

        return mapper
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_data_mapper][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
        raise


def init_data_transformer():
    try:
        from .Logic_v2.DataTransformer import DataTransformer
        data_transformer = DataTransformer()
        print('[setup]init_data_transformer')
        return data_transformer

    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_data_transformer][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_sync_monitor():
    try:
        from .Logic_v2.SyncMonitor import SyncMonitor
        sync_monitor = SyncMonitor()
        print('[setup]init_sync_monitor')
        return sync_monitor
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_sync_monitor][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_json_validator():
    try:
        from .Logic_v2.JSONSchemaValidator import JSONSchemaValidator
        json_validator = JSONSchemaValidator()
        print('[setup]init_json_validator')
        return json_validator
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_json_validator][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_diagnostic_logger(device_id):
    try:
        from .Logic_v2.DiagnosticLogger import DiagnosticLogger
        diagnostic_logger = DiagnosticLogger(
            logger_name=f"sync.{device_id}"
        )
        print('[setup]init_diagnostic_logger')
        return diagnostic_logger
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_diagnostic_logger][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_queue():
    try:
        # очередь локальных команд
        from .Logic_v2.CommandQueue import CommandQueue
        queue = CommandQueue()
        print('[setup]init_queue')
        return queue
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_queue][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_batch_processor(diagnostic, manager, dbsession, snapshot_manager=None, 
                        idempotency_manager=None, batch_crud=None, device_number=None):
    try:
        from .Logic_v2.BatchProcessorEnhanced import BatchProcessorEnhanced
        _batch_processor = BatchProcessorEnhanced(
            session=dbsession,
            sync_manager=manager,
            snapshot_manager=snapshot_manager,
            idempotency_manager=idempotency_manager,
            batch_crud=batch_crud,
            device_number=device_number,
            _logger=diagnostic
        )
        print('[setup]init_batch_processor (enhanced with rollback support)')
        return _batch_processor
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_batch_processor][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_conflict_manager(config, _logger):
    try:
        from .Logic_v2.ConflictManager import ConflictManager
        _conflict_manager = ConflictManager(
            mapping_config=config,
            logger=_logger
        )
        print('[setup]init_conflict_manager')
        return _conflict_manager
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_conflict_manager][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_processor(queue, sender, db_session, retry_manager, cmd_crud, record_crud, status_crud, sync_cfg, schema_cache, schema_analyzer,
                   mapping_config, diagnostic_logger, data_mapper, data_transformer, sync_monitor, json_validator, batch_processor,
                   conflict_manager, sync_manager) -> SyncProcessor | None:
    try:

        init_sync_config_table(db_session)

        # главный процессор
        processor = SyncProcessor(
            queue=queue,
            sender=sender,
            schema_cache=schema_cache,
            schema_analyzer=schema_analyzer,
            mapping_config=mapping_config,
            data_mapper=data_mapper,
            data_transformer=data_transformer,
            conflict_manager=conflict_manager,
            batch_processor=batch_processor,
            cmd_crud=cmd_crud,
            record_crud=record_crud,
            status_crud=status_crud,
            sync_config_crud=sync_cfg,
            diagnostic_logger=diagnostic_logger,
            sync_monitor=sync_monitor,
            retry_manager=retry_manager,
            json_validator=json_validator,
            sync_manager=sync_manager,
            server_schema=SERVER_SCHEMA,
            sync_session=db_session,
            retry_attempts=5,  # настраиваемые параметры
            retry_delay=30,
            emulate_server=False,
            work_session=SessionLocal()
        )
        print('[setup]init_processor')
        return processor
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_processor][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
    return None


def init_receiver(device_id, proc, transport, ):
    try:
        from .Logic_v2.CommandReceiver import CommandReceiver
        receive = CommandReceiver(
            device_id=device_id,
            transport=transport,
            sync_processor=proc,
        )
        print('[setup]init_receiver')
        return receive
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_receiver][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
    return None


def init_sender(device_id, proc, queue, transport):
    try:
        from .Logic_v2.CommandSender import CommandSender
        send = CommandSender(
            transport=transport,
            queue=queue,
            sync_processor=proc,
            device_id=device_id
        )
        print('[setup]init_sender')
        return send
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_sender][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
    return None
