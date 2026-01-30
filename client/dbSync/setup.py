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
#     logger.info("[setup] init_crud")
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
    logger.info("[setup] init_crud")
    return cmd_crud, record_crud, status_crud, sync_cfg


def init_retry_manager(scheduler, queue, sender, diagnostic_logger):
    from .Logic_v2.RetryManager import RetryManager
    retry_manager = RetryManager(
        scheduler=scheduler,
        queue=queue,
        sender=sender,
        _logger=diagnostic_logger,
        base_delay=30.0,  # Фиксированный интервал 30 секунд
        max_retries=4320  # 36 часов = 129600 сек / 30 сек = 4320 попыток
    )
    logger.info("[setup] init_retry_manager")
    return retry_manager


def init_transport_service(host, token="<YOUR_JWT_TOKEN>", secret=b"supersecret", aes=b"16byteslongkey!!", Port="", push_http_timeout=120):
    from .Logic_v2.TransportService import TransportService
    if host and not host.startswith("http"):
        host = f"http://{host}"
    transport = TransportService(
        base_url=host,
        jwt_token=token,
        hmac_secret=secret,
        aes_key=aes,
        port=Port,
        push_http_timeout=push_http_timeout
    )
    logger.info("[setup] init_transport_service")
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
    logger.info("[setup] init_scheduler (custom executor)")
    return scheduler


def init_schema_cache():
    try:
        from .Logic_v2.SchemaCache import SchemaCache
        schema_cache = SchemaCache()
        logger.info("[setup] init_schema_cache")
        return schema_cache
    except Exception as e:
        logger.exception("[setup][init_schema_cache] error: %s", e)


def init_schema_analyzer():
    try:
        from .Logic_v2.SchemaAnalyzer import SchemaAnalyzer
        schema_analyzer = SchemaAnalyzer()
        logger.info("[setup] init_schema_analyzer")
        return schema_analyzer
    except Exception as e:
        logger.exception("[setup][init_schema_analyzer] error: %s", e)


def init_mapping_config():
    try:
        from .Logic_v2.MappingConfigurator import MappingConfigurator
        mapping_config = MappingConfigurator()
        logger.info("[setup] init_mapping_config")
        return mapping_config
    except Exception as e:
        logger.exception("[setup][init_mapping_config] error: %s", e)


def init_data_mapper():
    try:
        from .Logic_v2.DataMapper import DataMapper
        import os
        import json

        base = os.path.dirname(__file__)
        path = os.path.join(base, "Logic_v2", "cache", "fields", "sync_fields.json")
        if not os.path.exists(path):
             logger.warning("[setup][init_data_mapper] mapping file not found at %s, using empty mappings", path)
             field_mappings = {}
        else:
             field_mappings = json.load(open(path, encoding="utf-8"))

        mapper = DataMapper(field_mappings=field_mappings)
        logger.info("[setup] init_data_mapper (loaded fields from %s)", path)

        return mapper
    except Exception as e:
        logger.exception("[setup][init_data_mapper] error: %s", e)
        raise


def init_data_transformer():
    try:
        from .Logic_v2.DataTransformer import DataTransformer
        data_transformer = DataTransformer()
        
        def extract_status_from_history(record: dict) -> dict:
            """
            Извлекает status из вложенного объекта Status в History.
            Преобразует Status.id в status (integer).
            Если status уже является integer, оставляем как есть.
            """
            # Если есть вложенный объект Status, извлекаем id
            if 'Status' in record and isinstance(record['Status'], dict):
                status_obj = record['Status']
                # Извлекаем id из объекта Status
                if 'id' in status_obj:
                    record['status'] = status_obj['id']
                # Удаляем вложенный объект Status
                del record['Status']
            # Если status уже установлен как integer, оставляем как есть
            elif 'status' not in record and 'Status' not in record:
                # Если нет ни status, ни Status, оставляем как есть
                pass
            return record
        
        data_transformer.register_rule("History", "incoming", extract_status_from_history)
        logger.info("[setup] init_data_transformer")
        return data_transformer

    except Exception as e:
        logger.exception("[setup][init_data_transformer] error: %s", e)


def init_sync_monitor():
    try:
        from .Logic_v2.SyncMonitor import SyncMonitor
        sync_monitor = SyncMonitor()
        logger.info("[setup] init_sync_monitor")
        return sync_monitor
    except Exception as e:
        logger.exception("[setup][init_sync_monitor] error: %s", e)


def init_json_validator():
    try:
        from .Logic_v2.JSONSchemaValidator import JSONSchemaValidator
        json_validator = JSONSchemaValidator()
        logger.info("[setup] init_json_validator")
        return json_validator
    except Exception as e:
        logger.exception("[setup][init_json_validator] error: %s", e)


def init_diagnostic_logger(device_id):
    try:
        from .Logic_v2.DiagnosticLogger import DiagnosticLogger
        diagnostic_logger = DiagnosticLogger(
            logger_name=f"sync.{device_id}"
        )
        logger.info("[setup] init_diagnostic_logger")
        return diagnostic_logger
    except Exception as e:
        logger.exception("[setup][init_diagnostic_logger] error: %s", e)


def init_queue():
    try:
        # очередь локальных команд
        from .Logic_v2.CommandQueue import CommandQueue
        queue = CommandQueue()
        logger.info("[setup] init_queue")
        return queue
    except Exception as e:
        logger.exception("[setup][init_queue] error: %s", e)


def init_batch_processor(diagnostic, manager, dbsession):
    try:
        from .Logic_v2.BatchProcessor import BatchProcessor
        _batch_processor = BatchProcessor(
            sync_manager=manager,
            _logger=diagnostic,
            session=dbsession,
        )
        logger.info("[setup] init_batch_processor")
        return _batch_processor
    except Exception as e:
        logger.exception("[setup][init_batch_processor] error: %s", e)


def init_conflict_manager(config, _logger):
    try:
        from .Logic_v2.ConflictManager import ConflictManager
        _conflict_manager = ConflictManager(
            mapping_config=config,
            logger=_logger
        )
        logger.info("[setup] init_conflict_manager")
        return _conflict_manager
    except Exception as e:
        logger.exception("[setup][init_conflict_manager] error: %s", e)


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
        logger.info("[setup] init_processor")
        return processor
    except Exception as e:
        logger.exception("[setup][init_processor] error: %s", e)
    return None


def init_receiver(device_id, proc, transport, ):
    try:
        from .Logic_v2.CommandReceiver import CommandReceiver
        receive = CommandReceiver(
            device_id=device_id,
            transport=transport,
            sync_processor=proc,
        )
        logger.info("[setup] init_receiver")
        return receive
    except Exception as e:
        logger.exception("[setup][init_receiver] error: %s", e)
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
        logger.info("[setup] init_sender")
        return send
    except Exception as e:
        logger.exception("[setup][init_sender] error: %s", e)
    return None
