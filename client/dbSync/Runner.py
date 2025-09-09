# import threading, datetime, time, traceback, logging
# from .setup import init_scheduler, init_sender, init_receiver, init_crud, init_retry_manager, init_transport_service, init_schema_cache, init_schema_analyzer, init_mapping_config, init_data_mapper, init_data_transformer, init_sync_monitor, init_json_validator, init_diagnostic_logger, init_batch_processor, init_conflict_manager, init_processor
from sqlalchemy import create_engine, NullPool, text, inspect
from sqlalchemy.orm import sessionmaker

import dbSync
# from DB.Data.sqlite_db import SessionLocal
from dbSync.Logic_v2.SyncManager import SyncManager
from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES

from .Model.base import sync_base
from .setup import *
import os

# from queue import Queue, Empty

# глобальный реестр запущенных планировщиков
_active_schedulers = {}
# _active_schedulers: Dict[int, BackgroundScheduler] = {}
logger = logging.getLogger(__name__)

from apscheduler.schedulers.background import BackgroundScheduler
# где-то в модуле верхнего уровня, «до» запуска sync-потока:
from apscheduler.executors.pool import ThreadPoolExecutor as APS_ThreadPoolExecutor

# Создаём executor одномоментно, пока интерпретатор ещё «жив»:
GLOBAL_APS_EXECUTOR = APS_ThreadPoolExecutor()

# …далее идёт остальное…

def init_scheduler() -> BackgroundScheduler:
    """
    Возвращаем BackgroundScheduler с заранее созданным executor,
    чтобы внутри background-потока APScheduler больше не создавал новый executor.
    """
    # Используем глобальный executor, созданный раннее
    from apscheduler.executors.pool import ThreadPoolExecutor as APS_ThreadPoolExecutor
    executor = APS_ThreadPoolExecutor()  # <-- здесь создаётся слишком поздно
    scheduler = BackgroundScheduler(executors={'default': executor})
    return scheduler

def create_db_session_local():
    return SessionLocal()


def create_db_session():
    """
    Создаёт SQLAlchemy Session для всех CRUD-слоёв.
    Для избежания блокировок в multithreaded-окружении:
      - выключаем check_same_thread
      - используем NullPool, чтобы каждый .connect() открывал своё соединение
      - переключаем режим журнала в WAL (более конкурентный)
      - гарантируем создание таблиц через sync_base.metadata.create_all
    """
    # Файл находится в dbSync/Logic_v2 → поднимаемся на уровень выше до dbSync
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_file = os.path.join(base_dir, "Model", "sync.db")
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    print(f"[ПОТОК][{threading.current_thread().name}][runner][create_db_session]→ Opening SQLite DB at: {db_file}, время: {datetime.datetime.now()} ")

    database_url = f"sqlite:///{db_file}"
    engine = create_engine(
        database_url,
        poolclass=NullPool,
        connect_args={"check_same_thread": False}
    )

    # Устанавливаем WAL режим
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))

    # Проверяем и создаём таблицы, если они не существуют
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    if "Command" not in existing_tables:
        print("[runner] Таблицы отсутствуют. Создаём структуру...")
        sync_base.metadata.create_all(engine)
    else:
        print("[runner] Таблицы найдены, структура в порядке.")

    return sessionmaker(bind=engine)()


def job_send(_sender):
    _sender.send_pending()


def job_fetch(_receiver):
    _receiver.fetch_and_apply()


def start_sync(device_id: int, host=None, port="", token="<YOUR_JWT_TOKEN>", secret=b"supersecret", aes=b"16byteslongkey!!", scheduler_sender_timeout=60, scheduler_receiver_timeout=120):
    if device_id in _active_schedulers:
        logging.getLogger("sync.startup").warning(f"[INFO] Already running for device={device_id}")
        return

    from queue import Queue
    queue_in = Queue()
    INBOUND_QUEUES[device_id] = queue_in
    logging.getLogger("sync.startup").debug(f"[QUEUE] Created queue id={id(queue_in)} for device={device_id}")

    def runner():
        # 1) Создаём компоненты
        (queue, schema_cache, schema_analyzer, mapping_config,
         data_mapper, data_transformer, sync_monitor,
         json_validator, diagnostic_logger, sync_manager,
         cmd_crud, transport_service, batch_processor, conflict_manager,
         sender, receiver, retry_manager, scheduler, processor) = create_sync_components(
            device_id=device_id,
            host=host,
            token=token,
            secret=secret,
            aes=aes,
            Port=port
        )
        # Создаём все компоненты, в том числе scheduler = init_scheduler()
        # scheduler = init_scheduler()
        # 2) Регистрируем в scheduler наши job‐ы
        scheduler.add_job(job_send, 'interval',
                          seconds=scheduler_sender_timeout,
                          id=f"send_{device_id}",
                          args=[sender])
        scheduler.add_job(job_fetch, 'interval',
                          seconds=scheduler_receiver_timeout,
                          id=f"fetch_{device_id}",
                          args=[receiver])

        # 3) Сохраняем и стартуем scheduler
        _active_schedulers[device_id] = scheduler

        # Регистрируем в этом scheduler job-ы и т.д.
        # Теперь при вызове scheduler.start() не будет пытки register_atexit
        try:
            scheduler.start(paused=False)
            logging.getLogger("sync.startup").info(f"[STARTED] Sync for device={device_id}")
        except Exception as e:
            logging.getLogger("sync.startup").exception(f"Scheduler failed to start: {e}")
            return

        # 4) Основной loop, обрабатывающий сообщения из INBOUND_QUEUES[device_id]
        time_start = datetime.datetime.now()
        iteration_step = 0
        print(f'[ПОТОК][{threading.current_thread().name}][runner] Запуск синхронизации в {time_start}')

        from queue import Empty
        queue_in_thread = INBOUND_QUEUES[device_id]
        while device_id in _active_schedulers:
            iteration_step += 1
            try:
                try:
                    msg = queue_in_thread.get(timeout=10)
                except Empty:
                    print(f'[ПОТОК][{threading.current_thread().name}][runner] Очередь пуста, итерация {iteration_step}')
                    continue

                msg_type = msg.get("type")
                # Обязательно получаем очередь-ответчик, если она есть
                reply_queue: Queue = msg.get("reply_queue")

                if msg_type == "handshake":
                    schema = msg["payload"]
                    hash_ = msg["hash"]
                    print(f"[ПОТОК][{threading.current_thread().name}][runner] " + ', '.join(f"{k}: {v}" for k, v in msg.items()))

                    try:
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации попытка запустить процессор')
                        result = processor.process_schema(
                            src_schema=schema,
                            client_schema_hash=hash_
                        )
                    except Exception as err:
                        result = {"error": str(err)}
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {err} подробности: {traceback.format_exc()}')
                    # Отправляем результат обратно в HTTP-обработчик
                    print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации отправляем результат обратно в HTTP-обработчик')
                    if reply_queue:
                        reply_queue.put(result)

                elif msg_type == "push": #толкать задвинуть проталкивать
                    # 1) вызываем процессор — он вернёт список статусов
                    print(f'[ПОТОК][{threading.current_thread().name}][runner] Вызываем процессор')
                    try:
                        data = msg.get("hash", "")
                        print(f"[ПОТОК][{threading.current_thread().name}][runner][push] " + ', '.join(f"{k}: {v}" for k, v in msg.items()))
                        dbSync.init_db = True
                        statuses = processor.process_push(
                            device=device_id,
                            commands=msg["payload"],
                            client_schema_hash=data
                        )
                        dbSync.init_db = False
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] statuses: {statuses}')
                    except Exception as e:
                        # если упало — возвращаем ошибку в reply_queue
                        statuses = [{"id": None, "status": "FAILED", "error": str(e)}]
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {e} подробности: {traceback.format_exc()}')
                    # 2) отправляем результат в reply_queue
                    print(f'[ПОТОК][{threading.current_thread().name}][runner] отправляем результат в reply_queue')
                    if reply_queue:
                        reply_queue.put(statuses)

                elif msg_type == "pull": # тянуть потянуть
                    print(f"[ПОТОК][{threading.current_thread().name}][runner] " + ', '.join(f"{k}: {v}" for k, v in msg.items()))
                    logging.getLogger("sync.runner").info(f"[runner] handling pull: since={msg['since']!r}, hash={msg.get('hash')!r}")
                    try:
                        data = msg.get("hash", "")
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] Вызываем prepare_pull')
                        result = processor.prepare_pull(
                            device=msg["device"],
                            since=msg["since"],
                            client_schema_hash=msg.get("hash", "")
                        )
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] prepare_pull отработал')
                        logging.getLogger("sync.runner").info(f"[runner] pull → result: {result!r}")
                    except Exception as ex:
                        logging.getLogger("sync.runner").exception("Error in prepare_pull")
                        result = {"error": str(ex)}
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {ex} подробности: {traceback.format_exc()}')
                    # обязательно кладём ответ обратно
                    print(f'[ПОТОК][{threading.current_thread().name}][runner] кладём ответ обратно в reply_queue')
                    if msg.get("reply_queue"):
                        msg["reply_queue"].put(result)
                        logging.getLogger("sync.runner").info("[runner] reply_queue.put() done")
                elif msg_type == "local":
                    # print(f'[ПОТОК][{threading.current_thread().name}][runner] msg_type: {msg_type}, msg: {json.dumps(msg, ensure_ascii=False)}')
                    cmd = msg  # содержит table, operation, data
                    try:
                        # Здесь SyncProcessor должен иметь метод enqueue_local_command
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации попытка запустить процессор')
                        processor.enqueue_local_command(cmd)
                    except Exception as ex:
                        diagnostic_logger.info(f"Error enqueuing local command: {ex}")
                        print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {ex} подробности: {traceback.format_exc()}')
                # Если будут ошибки, они будут залогированы ниже в блоке except

            except Exception as e:
                logging.getLogger("sync.runner").exception("Unexpected error in runner loop, exiting")
                print(f'[ПОТОК][{threading.current_thread().name}][runner] UNEXPECTED ERROR at {time_start}: {e} — {traceback.format_exc()}')
                break

        # Cleanup (остановка и удаление scheduler из реестра)
        print(f'[ПОТОК][{threading.current_thread().name}][runner] STOP at {datetime.datetime.now()}, total iterations: {iteration_step}')
        INBOUND_QUEUES.pop(device_id, None)
        _active_schedulers.pop(device_id, None)
        logging.getLogger("sync.startup").info(f"[STOPPED] Sync for device={device_id}")

    thread = threading.Thread(target=runner, name=f"sync-thread-{device_id}", daemon=False)
    thread.start()


def stop_sync(device_id: int):
    """
    Останавливает планировщик синхронизации для конкретного device_id.
    """
    print(f'[ПОТОК][{threading.current_thread().name}][stop_sync] device_id: {device_id}')
    sched = _active_schedulers.get(device_id)
    if not sched:
        logging.getLogger("sync.startup").warning(f"[WARN] Нет активного scheduler для device={device_id}")
        return

    sched.shutdown(wait=False)
    del _active_schedulers[device_id]
    logging.getLogger("sync.startup").info(f"[STOPPED] Остановлен sync для device={device_id}")


def create_sync_components(device_id: int, host, token, secret, aes, Port=""):
    """
    Инстанцирует все зависимости логического слоя синхронизации для одного устройства.
    """
    db_session_local = create_db_session_local()
    db_session = create_db_session()
    queue = init_queue()
    schema_cache = init_schema_cache()
    schema_analyzer = init_schema_analyzer()
    mapping_config = init_mapping_config()
    data_mapper = init_data_mapper()
    data_transformer = init_data_transformer()
    sync_monitor = init_sync_monitor()
    json_validator = init_json_validator()
    diagnostic_logger = init_diagnostic_logger(
        device_id=device_id
    )
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_diagnostic_logger - Успешно.')

    sync_manager = SyncManager(session=db_session_local)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] SyncManager - Успешно.')

    scheduler = init_scheduler()
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_scheduler - Успешно.')

    cmd_crud, record_crud, status_crud, sync_cfg = init_crud()
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_crud - Успешно.')

    transport_service = init_transport_service(host=host, token=token, secret=secret, aes=aes, Port=Port)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_transport_service - Успешно.')

    batch_processor = init_batch_processor(diagnostic=diagnostic_logger, manager=sync_manager, dbsession=db_session)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_batch_processor - Успешно.')

    conflict_manager = init_conflict_manager(_logger=diagnostic_logger, config=mapping_config)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_conflict_manager - Успешно.')

    retry_manager = init_retry_manager(scheduler=scheduler, queue=queue, sender=None, diagnostic_logger=diagnostic_logger)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_retry_manager - Успешно.')

    processor = init_processor(
        queue=queue,
        sender=None,
        db_session=db_session,
        diagnostic_logger=diagnostic_logger,
        mapping_config=mapping_config,
        sync_monitor=sync_monitor,
        batch_processor=batch_processor,
        conflict_manager=conflict_manager,
        schema_cache=schema_cache,
        schema_analyzer=schema_analyzer,
        data_mapper=data_mapper,
        data_transformer=data_transformer,
        json_validator=json_validator,
        retry_manager=retry_manager,
        cmd_crud=cmd_crud,
        record_crud=record_crud,
        status_crud=status_crud,
        sync_cfg=sync_cfg,
        sync_manager=sync_manager
    )
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_processor - Успешно.')
    # Если init_processor вернул None — сразу падаем с ошибкой:
    assert processor, "Не получилось создать SyncProcessor"

    sender = init_sender(
        device_id=device_id,
        transport=transport_service,
        proc=processor,
        queue=queue
    )
    print(f'[ПОТОК][{threading.current_thread().name}][runner] init_sender - Успешно.')

    receiver = init_receiver(
        device_id=device_id,
        proc=None,
        transport=transport_service,
    )
    print(f'[ПОТОК][{threading.current_thread().name}][runner] init_receiver - Успешно.')

    # sender и receiver берут на себя отправку/приём
    sender.sync_processor = processor
    sender.transport = transport_service
    sender.logger = diagnostic_logger
    receiver.sync_processor = processor
    receiver.transport = transport_service
    receiver.logger = diagnostic_logger
    # 4) «Подпишем» обратно в processor его sender (нужен для retry_manager)
    processor.sender = sender
    retry_manager.sender = sender
    print(f">>> DEBUG: sender.sync_processor is {sender.sync_processor!r}")
    print(f">>> DEBUG: sender.data_mapper      is {sender.sync_processor.data_mapper!r}")
    return (queue, schema_cache, schema_analyzer, mapping_config, data_mapper, data_transformer, sync_monitor, json_validator, diagnostic_logger, sync_manager,
            cmd_crud, transport_service, batch_processor, conflict_manager, sender, receiver, retry_manager, scheduler, processor)


def _create_sync_components(device_id: int, host, token, secret, aes, Port=""):
    """
    Инстанцирует все зависимости логического слоя синхронизации для одного устройства.
    """
    scheduler = init_scheduler()
    db_session_local = create_db_session_local()
    db_session = create_db_session()
    queue = init_queue()
    schema_cache = init_schema_cache()
    schema_analyzer = init_schema_analyzer()
    mapping_config = init_mapping_config()
    data_mapper = init_data_mapper()
    data_transformer = init_data_transformer()
    sync_monitor = init_sync_monitor()
    json_validator = init_json_validator()
    diagnostic_logger = init_diagnostic_logger(
        device_id=device_id
    )
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_diagnostic_logger - Успешно.')

    sync_manager = SyncManager(session=db_session_local)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] SyncManager - Успешно.')


    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_scheduler - Успешно.')

    cmd_crud, record_crud, status_crud, sync_cfg = init_crud()
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_crud - Успешно.')

    transport_service = init_transport_service(host=host, token=token, secret=secret, aes=aes, Port=Port)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_transport_service - Успешно.')

    batch_processor = init_batch_processor(diagnostic=diagnostic_logger, manager=sync_manager, dbsession=db_session)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_batch_processor - Успешно.')

    conflict_manager = init_conflict_manager(_logger=diagnostic_logger, config=mapping_config)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_conflict_manager - Успешно.')

    receiver = init_receiver(
        device_id=device_id,
        proc=None,
        transport=transport_service,
    )
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_receiver - Успешно.')

    sender = init_sender(
        device_id=device_id,
        transport=transport_service,
        proc=None,
        queue=queue
    )
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_sender - Успешно.')

    retry_manager = init_retry_manager(scheduler=scheduler, queue=queue, sender=sender, diagnostic_logger=diagnostic_logger)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_retry_manager - Успешно.')

    processor = init_processor(
        queue=queue,
        sender=sender,
        db_session=db_session,
        diagnostic_logger=diagnostic_logger,
        mapping_config=mapping_config,
        sync_monitor=sync_monitor,
        batch_processor=batch_processor,
        conflict_manager=conflict_manager,
        schema_cache=schema_cache,
        schema_analyzer=schema_analyzer,
        data_mapper=data_mapper,
        data_transformer=data_transformer,
        json_validator=json_validator,
        retry_manager=retry_manager,
        cmd_crud=cmd_crud,
        record_crud=record_crud,
        status_crud=status_crud,
        sync_cfg=sync_cfg,
        sync_manager=sync_manager
    )
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_processor - Успешно.')

    # sender и receiver берут на себя отправку/приём
    sender.sync_processor = processor
    sender.transport = transport_service
    sender.logger = diagnostic_logger
    receiver.sync_processor = processor
    receiver.transport = transport_service
    receiver.logger = diagnostic_logger
    return (queue, schema_cache, schema_analyzer, mapping_config, data_mapper, data_transformer, sync_monitor, json_validator, diagnostic_logger, sync_manager,
            cmd_crud, transport_service, batch_processor, conflict_manager, sender, receiver, retry_manager, scheduler, processor)
