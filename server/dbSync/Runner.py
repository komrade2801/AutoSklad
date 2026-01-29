# import datetime
# import json
# # import threading
# import logging
# from typing import Dict

# import time
# import traceback
# from typing import Dict
from sqlalchemy import create_engine, NullPool, text, inspect
from sqlalchemy.orm import sessionmaker

# from DB.session import SessionLocal
from dbSync.Logic_v2.SyncManager import SyncManager
from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES

from .Model.base import sync_base
from .setup import *
import os
from queue import Queue, Empty

# глобальный реестр запущенных планировщиков
_active_schedulers = {}
# _active_schedulers: Dict[int, BackgroundScheduler] = {}
logger = logging.getLogger(__name__)


def job_send(_sender):
    _sender.send_pending()


def job_fetch(_receiver):
    _receiver.fetch_and_apply()


def job_process_retrying(_sender, _retry_manager):
    _sender.process_retrying(_retry_manager)


def create_db_session_local():
    return get_db_session()


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
    base_dir = os.path.dirname(__file__)
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


def start_sync(
        device_id: int,
        host: str = None,
        port="",
        token: str = "<YOUR_JWT_TOKEN>",
        secret=b"supersecret",
        aes=b"16byteslongkey!!",
        scheduler_sender_timeout=60,
        scheduler_receiver_timeout=120
):
    if device_id in _active_schedulers:
        logging.getLogger("sync.startup").warning(
            f"[INFO] Already running for device={device_id}")
        return
    # до запуска потока
    queue_in = Queue()
    INBOUND_QUEUES[device_id] = queue_in
    logging.getLogger("sync.startup").debug(
        f"[QUEUE] Created queue id={id(queue_in)} for device={device_id}")

    def runner():
        time_start = datetime.datetime.now()

        print(
            f'[ПОТОК][{threading.current_thread().name}][runner] старт процесса синхронизации от {time_start}')

        # … инициализация всех компонентов …
        # 1) создаём все компоненты
        (queue, schema_cache, schema_analyzer, mapping_config,
         data_mapper, data_transformer, sync_monitor,
         json_validator, diagnostic_logger, sync_manager,
         cmd_crud, transport_service, batch_processor, conflict_manager,
         _sender, _receiver, retry_manager, scheduler, processor) = create_sync_components(
            device_id=device_id,
            host=host,
            token=token,
            secret=secret,
            aes=aes,
            Port=port
        )

        # print(f'[ПОТОК][{threading.current_thread().name}][runner] create_sync_components - Успешно. {time_start}')

        # 2) Регистрируем в scheduler наши jobs, передавая sender и receiver
        scheduler.add_job(job_send, 'interval',
                          seconds=scheduler_sender_timeout,
                          id=f"send_{device_id}",
                          args=[_sender])
        # print(f'[ПОТОК][{threading.current_thread().name}][runner] scheduler_sender - Успешно. {time_start}')

        scheduler.add_job(job_fetch, 'interval',
                          seconds=scheduler_receiver_timeout,
                          id=f"fetch_{device_id}",
                          args=[_receiver])
        # print(f'[ПОТОК][{threading.current_thread().name}][runner] scheduler_receiver - Успешно. {time_start}')

        scheduler.add_job(job_process_retrying, 'interval',
                          seconds=30,  # Check retrying commands every 30 seconds
                          id=f"process_retrying_{device_id}",
                          args=[_sender, retry_manager])

        # 3) Запускаем scheduler
        _active_schedulers[device_id] = scheduler
        scheduler.start(paused=False)
        logging.getLogger("sync.startup").info(
            f"[STARTED] Sync for device={device_id}")
        # print(f'[ПОТОК][{threading.current_thread().name}][runner] scheduler_start - Успешно. {time_start}')

        # создаём очередь для сообщений от HTTP
        queue_in_thread = INBOUND_QUEUES[device_id]
        logging.getLogger("sync.runner").info(
            f"[runner start] sees queue_id={id(queue_in_thread)} for device={device_id}")

        iteration_step = 0
        # print(f'[ПОТОК][{threading.current_thread().name}][runner] количество active_schedulers: {len(_active_schedulers)}. {time_start}')

        while device_id in _active_schedulers:
            # print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации, время на данный момент {datetime.datetime.now()}, итерация цикла: {iteration_step} попытка считать очередь')

            iteration_step += 1
            try:
                try:
                    msg = queue_in_thread.get(timeout=10)
                    # logging.getLogger("sync.runner").info(f"[runner] got msg: {msg!r}")
                    logging.getLogger("sync.runner").debug(
                        "queue empty, next iteration")
                except Empty:
                    # print(f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации, время на данный момент {datetime.datetime.now()}, итерация цикла: {iteration_step} очередь пуста')
                    continue

                msg_type = msg.get("type")
                # Обязательно получаем очередь-ответчик, если она есть
                reply_queue: Queue = msg.get("reply_queue")

                if msg_type == "handshake":
                    schema = msg["payload"]
                    hash_ = msg["hash"]
                    print(f"[ПОТОК][{threading.current_thread().name}][runner] " +
                          ', '.join(f"{k}: {v}" for k, v in msg.items()))

                    try:
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации попытка запустить процессор')
                        result = processor.process_schema(
                            src_schema=schema,
                            client_schema_hash=hash_
                        )
                    except Exception as err:
                        result = {"error": str(err)}
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {err} подробности: {traceback.format_exc()}')
                    # Отправляем результат обратно в HTTP-обработчик
                    print(
                        f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации отправляем результат обратно в HTTP-обработчик')
                    if reply_queue:
                        reply_queue.put(result)

                elif msg_type == "push":
                    # 1) вызываем процессор — он вернёт список статусов
                    print(
                        f'[ПОТОК][{threading.current_thread().name}][runner] Вызываем процессор')
                    try:
                        data = msg.get("hash", "")
                        print(f"[ПОТОК][{threading.current_thread().name}][runner] " +
                              ', '.join(f"{k}: {v}" for k, v in msg.items()))
                        import dbSync
                        dbSync.init_db = True
                        statuses = processor.process_push(
                            device=device_id,
                            commands=msg["payload"],
                            client_schema_hash=data
                        )
                        dbSync.init_db = False
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] statuses: {statuses}')
                    except Exception as e:
                        # если упало — возвращаем ошибку в reply_queue
                        statuses = [
                            {"id": None, "status": "FAILED", "error": str(e)}]
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {e} подробности: {traceback.format_exc()}')
                    # 2) отправляем результат в reply_queue
                    print(
                        f'[ПОТОК][{threading.current_thread().name}][runner] отправляем результат в reply_queue')
                    if reply_queue:
                        reply_queue.put(statuses)

                elif msg_type == "pull":
                    print(f"[ПОТОК][{threading.current_thread().name}][runner] " +
                          ', '.join(f"{k}: {v}" for k, v in msg.items()))
                    logging.getLogger("sync.runner").info(
                        f"[runner] handling pull: since={msg['since']!r}, hash={msg.get('hash')!r}")
                    # Сначала обрабатываем все накопившиеся "local" команды (Plan, PlanToolTypes и т.д.),
                    # чтобы они попали в таблицу Command до prepare_pull — иначе pull не вернёт их клиенту.
                    while True:
                        try:
                            m = queue_in_thread.get_nowait()
                        except Empty:
                            break
                        if m.get("type") == "local":
                            processor.current_device_id = device_id
                            try:
                                processor.enqueue_local_command(m)
                            except Exception as ex:
                                diagnostic_logger.info(
                                    f"Error enqueuing local command before pull: {ex}")
                        else:
                            queue_in_thread.put(m)
                            break
                    try:
                        data = msg.get("hash", "")
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] Вызываем prepare_pull')
                        result = processor.prepare_pull(
                            device=msg["device"],
                            since=msg["since"],
                            client_schema_hash=msg.get("hash", "")
                        )
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] prepare_pull отработал')
                        logging.getLogger("sync.runner").info(
                            f"[runner] pull → result: {result!r}")
                    except Exception as ex:
                        logging.getLogger("sync.runner").exception(
                            "Error in prepare_pull")
                        result = {"error": str(ex)}
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {ex} подробности: {traceback.format_exc()}')
                    # обязательно кладём ответ обратно
                    print(
                        f'[ПОТОК][{threading.current_thread().name}][runner] кладём ответ обратно в reply_queue')
                    if msg.get("reply_queue"):
                        msg["reply_queue"].put(result)
                        logging.getLogger("sync.runner").info(
                            "[runner] reply_queue.put() done")
                elif msg_type == "local":
                    # print(f'[ПОТОК][{threading.current_thread().name}][runner] msg_type: {msg_type}, msg: {json.dumps(msg, ensure_ascii=False)}')
                    cmd = msg  # содержит table, operation, data
                    try:
                        # Устанавливаем current_device_id для правильной синхронизации
                        processor.current_device_id = device_id
                        # Здесь SyncProcessor должен иметь метод enqueue_local_command
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации попытка запустить процессор')
                        processor.enqueue_local_command(cmd)
                    except Exception as ex:
                        diagnostic_logger.info(
                            f"Error enqueuing local command: {ex}")
                        print(
                            f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации ошибка в {time_start} причина: {ex} подробности: {traceback.format_exc()}')

            except Exception as e:
                logging.getLogger("sync.runner").exception(
                    "Unexpected error in runner loop, exiting")
                print(
                    f'[ПОТОК][{threading.current_thread().name}][runner] процесс синхронизации сломался в {time_start} причина: {e} подробности: {traceback.format_exc()}')
                # break

        # … другие типы …

        # cleanup
        print(f'[ПОТОК][{threading.current_thread().name}][runner] Стоп цикла. Времся останова: {datetime.datetime.now()}, всего итераций цикла: {iteration_step}')

        INBOUND_QUEUES.pop(device_id, None)
        _active_schedulers.pop(device_id, None)
        logging.getLogger("sync.startup").info(
            f"[STOPPED] Sync for device={device_id}")

    thread = threading.Thread(
        target=runner, name=f"sync-thread-{device_id}", daemon=True)
    thread.start()


def stop_sync(device_id: int):
    """
    Останавливает планировщик синхронизации для конкретного device_id.
    """
    print(
        f'[ПОТОК][{threading.current_thread().name}][stop_sync] device_id: {device_id}')
    sched = _active_schedulers.get(device_id)
    if not sched:
        logging.getLogger("sync.startup").warning(
            f"[WARN] Нет активного scheduler для device={device_id}")
        return

    sched.shutdown(wait=False)
    del _active_schedulers[device_id]
    logging.getLogger("sync.startup").info(
        f"[STOPPED] Остановлен sync для device={device_id}")


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

    transport_service = init_transport_service(
        host=host, token=token, secret=secret, aes=aes, Port=Port)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_transport_service - Успешно.')

    batch_processor = init_batch_processor(
        diagnostic=diagnostic_logger, manager=sync_manager, dbsession=db_session)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_batch_processor - Успешно.')

    conflict_manager = init_conflict_manager(
        _logger=diagnostic_logger, config=mapping_config)
    # print(f'[ПОТОК][{threading.current_thread().name}][runner] init_conflict_manager - Успешно.')

    retry_manager = init_retry_manager(
        scheduler=scheduler, queue=queue, sender=None, diagnostic_logger=diagnostic_logger)
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
    print(
        f'[ПОТОК][{threading.current_thread().name}][runner] init_sender - Успешно.')

    receiver = init_receiver(
        device_id=device_id,
        proc=None,
        transport=transport_service,
    )
    print(
        f'[ПОТОК][{threading.current_thread().name}][runner] init_receiver - Успешно.')

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
    sender.retry_manager = retry_manager
    print(f">>> DEBUG: sender.sync_processor is {sender.sync_processor!r}")
    print(
        f">>> DEBUG: sender.data_mapper      is {sender.sync_processor.data_mapper!r}")
    return (queue, schema_cache, schema_analyzer, mapping_config, data_mapper, data_transformer, sync_monitor, json_validator, diagnostic_logger, sync_manager,
            cmd_crud, transport_service, batch_processor, conflict_manager, sender, receiver, retry_manager, scheduler, processor)

# def start_sync_scheduler(device_id: int, scheduler):

# def start_sync(...):
#     # …
#     def runner(device_id):
#         *_, scheduler, processor = create_sync_components(...)
#
#         _active_schedulers[device_id] = scheduler
#         scheduler.start(paused=False)
#         logging.getLogger("sync.startup").info(f"[STARTED] Sync for device={device_id}")
#
#         while device_id in _active_schedulers:
#             try:
#                 msg = queue_in.get(timeout=1.0)
#             except queue.Empty:
#                 continue
#
#             msg_type = msg.get("type")
#             # Обязательно получаем очередь-ответчик, если она есть
#             reply_queue: Queue = msg.get("reply_queue")
#
#             if msg_type == "handshake":
#                 schema = msg["payload"]
#                 hash_  = msg["hash"]
#                 try:
#                     result = processor.process_schema(
#                         src_schema=schema,
#                         client_schema_hash=hash_
#                     )
#                 except Exception as err:
#                     result = {"error": str(err)}
#                 # Отправляем результат обратно в HTTP-обработчик
#                 if reply_queue:
#                     reply_queue.put(result)
#
#             elif msg_type == "push":
#                 # аналогично, можно сделать reply_queue для push, если нужно
#                 processor.process_push(
#                     device=device_id,
#                     commands=msg["payload"],
#                     client_schema_hash=msg.get("hash", "")
#                 )
#                 if reply_queue:
#                     reply_queue.put({"status": "ok"})
#             # … другие типы …
#
#         # cleanup
#         INBOUND_QUEUES.pop(device_id, None)
#         _active_schedulers.pop(device_id, None)
#         logging.getLogger("sync.startup").info(f"[STOPPED] Sync for device={device_id}")
#
#     thread = threading.Thread(target=runner, name=f"sync-thread-{device_id}", daemon=False)
#     thread.start()

# Что было добавлено и улучшено
#     Полная инициализация всех зависимостей
#     – Теперь create_sync_components создаёт все компоненты, которые требует SyncProcessor (включая DataTransformer, SyncMonitor, RetryManager, JSONSchemaValidator, DiagnosticLogger, а также CRUD-классы и SQLAlchemy-сессию).
#     SQLAlchemy Session
#     – Функция create_db_session настраивает подключение к вашей БД и возвращает сессию, которую используют все CRUD-движки.
#     Конфигурация через настройки
#     – SERVER_SCHEMA загружается из модуля my_project.settings (можно заменить на чтение файла JSON/YAML).
#     Логирование
#     – Везде используются logging.getLogger, чтобы можно было тонко настраивать уровень вывода и перехватить логи.
#     CLI-точка входа
#     – Блок if __name__ == "__main__": позволяет вызывать запуск через python sync_start.py <device_id>.
#     Улучшенный контроль жизненного цикла
#     – При остановке через Ctrl+C вызывается stop_sync, корректно завершаются фоновый планировщик и потоки.
#     Идентификация Jobs
#     – Каждое задание получает уникальный id в планировщике, чтобы впоследствии можно было управлять ими по имени.
#     Параметризация
#     – В SyncProcessor прокинули retry_attempts и retry_delay явно, чтобы их легко менять.
#     Документация
#     – Каждый метод снабжён кратким описанием, объясняющим, что именно он делает и какие шаги выполняет.
