from __future__ import annotations

import datetime
import threading
import logging
from typing import Dict, Any
from functools import partial

from DB.Engine.HistoryHasDeviceCRUD import EngineHistoryHasDevice
# from DB.Data.sqlite_db import SessionLocal
from DB.session import get_db_session
from dbSync.Logic_v2.SyncProcessor import SyncProcessor
from dbSync.Logic_v2.sync_events import register_after_insert

from dbSync.Logic_v2.utils import SERVER_SCHEMA, init_sync_config_table
from apscheduler.schedulers.background import BackgroundScheduler
import traceback
# import time
logger = logging.getLogger(__name__)

def init_crud():
    # from dbSync.Engines.CommandCRUD import CommandCRUD
    # from dbSync.Engines.RecordCRUD import RecordCRUD
    # from dbSync.Engines.CommandStatusCRUD import CommandStatusCRUD
    # from dbSync.Engines.SyncConfigCRUD import SyncConfigCRUD
    # --- Импорты компонентов синхронизации ---
    from dbSync.Engines.CommandEngine import CommandCRUD
    from dbSync.Engines.RecordEngine import RecordCRUD
    from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD
    from dbSync.Engines.SyncConfigEngine import SyncConfigCRUD


    # CRUD-слои

    cmd_crud = CommandCRUD()
    record_crud = RecordCRUD()
    status_crud = CommandStatusCRUD()
    sync_cfg = SyncConfigCRUD()
    print('[setup]init_crud')
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
    print('[setup]init_retry_manager')
    return retry_manager


def init_transport_service(host, token="<YOUR_JWT_TOKEN>", secret=b"supersecret", aes=b"16byteslongkey!!", Port=""):
    from dbSync.Transport.TransportService import TransportService
    if host and not host.startswith("http"):
        host = f"http://{host}"
    transport = TransportService(
        base_url=host,
        jwt_token=token,
        hmac_secret=secret,
        aes_key=aes,
        Port=Port
    )
    print('[setup]init_transport_service')
    return transport


def init_scheduler() -> BackgroundScheduler:
    """
    Возвращает новый BackgroundScheduler без ошибок.
    Регистрация job'ов переносим в runner(), чтобы мы могли
    передать в них реальные аргументы sender и receiver.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    print('[setup]init_scheduler')
    return BackgroundScheduler()


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

        transformer = DataTransformer()

        def enrich_tools(record: dict) -> dict:
            """
            Функция Обогащение таблицы Tools, данными из таблицы ToolTypes
            :param record:
            :return:
            """
            from DB.Models.ToolTypes import ToolTypes
            from DB.Engine.ToolTypesCRUD import EngineToolTypes
            from DB.Models.Tools import Tools
            from DB.Engine.ToolsCRUD import EngineTools

            tls_id = record.get("index") or record.get("id")
            if tls_id is None:
                return record

            e_tools = EngineTools()
            tool = e_tools.get_tool_by_id(tool_id=tls_id)
            tool_type_id = tool.tool_type_id
            if not tool_type_id:
                return record
            e_tool_types = EngineToolTypes()
            tt: ToolTypes = e_tool_types.get(tool_type_id)
            if tt:
                record["name"] = tt.name
                record["description"] = tt.description
                record["img"] = tt.img
                record["groups_id"] = tt.groups_id

            return record

        transformer.register_rule("Tools", "outgoing", enrich_tools)
        transformer.register_rule(
            'Cell',
            'incoming',
            lambda d: {**d, 'id': d.get('index', d.get('id'))}
        )
        
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
        
        transformer.register_rule("History", "incoming", extract_status_from_history)
        print('[setup]init_data_transformer')
        return transformer
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

def init_batch_processor(diagnostic, manager, dbsession):
    try:
        from .Logic_v2.BatchProcessor import BatchProcessor
        _batch_processor = BatchProcessor(
            sync_manager=manager,
            _logger=diagnostic,
            session=dbsession,
        )
        print('[setup]init_batch_processor')
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


def on_new_consumption(record: Dict[str, Any], processor) -> None:
    """
    Callback: после вставки в OperationsConsumption автоматически
    создаёт связь с текущим устройством в OperationsConsumptionHasDevice.
    """
    if not processor:
        raise
    # Device_id устанавливается в SyncProcessor перед вызовом SyncManager
    device_id = processor.current_device_id or None
    if not device_id:
        return

    from DB.Engine.OperationsConsumptionHasDeviceCRUD import EngineOperationsConsumptionHasDevice
    e = EngineOperationsConsumptionHasDevice()
    try:
        e.add_link(
            operations_consumption_id=record['id']  or record['index'],
            device_id=device_id
        )
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][on_new_consumption][ERROR] - error: {e}, подробности: - {record} {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')

def on_new_history(record: Dict[str, Any], processor) -> None:
    """
    Callback: после вставки в History автоматически
    создаёт связь с текущим устройством в HistoryHasDevice.
    """
    if not processor:
        raise
    # Device_id устанавливается в SyncProcessor перед вызовом SyncManager
    device_id = processor.current_device_id or None
    if not device_id:
        return

    from DB.Engine.HistoryHasDeviceCRUD import HistoryHasDevice
    e = EngineHistoryHasDevice()
    try:
        e.add_link(
            history_id=record['id']  or record['index'],
            device_id=device_id
        )
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][on_new_history][ERROR] - error: {e}, подробности: - {record} {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')


def init_processor(queue,sender, db_session, retry_manager, cmd_crud, record_crud, status_crud, sync_cfg, schema_cache, schema_analyzer,
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
            work_session=get_db_session()
        )
        print('[setup]init_processor')

        # регистрируем callback
        #TODO Вынести в отдельный плагин для реализации библиотеки синхронизации баз данных.
        register_after_insert(
            'OperationsConsumption',
            partial(on_new_consumption, processor=processor)
        )
        register_after_insert(
            'History',
            partial(on_new_history, processor=processor)
        )
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
        from .Logic_v2.CommandOrderer import CommandOrderer
        
        # Создаём CommandOrderer для оптимизации команд перед отправкой
        command_orderer = CommandOrderer(logger=proc.diagnostic_logger if proc else None)
        
        send = CommandSender(
            transport=transport,
            queue=queue,
            sync_processor=proc,
            device_id=device_id,
            command_orderer=command_orderer  # 🆕 Передаём CommandOrderer
        )
        print('[setup]init_sender with CommandOrderer')
        return send
    except Exception as e:
        print(f'[ПОТОК][{threading.current_thread().name}][setup][init_sender][ERROR] - error: {e}, подробности: - {traceback.format_exc()}. Текущее время: {datetime.datetime.now()}')
    return None
