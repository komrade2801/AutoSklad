# Архитектура системы синхронизации AutoSklad

## Оглавление

1. [Обзор системы](#обзор-системы)
2. [Архитектурные принципы](#архитектурные-принципы)
3. [Компоненты системы](#компоненты-системы)
4. [Процесс синхронизации](#процесс-синхронизации)
5. [Сравнение клиент-сервер](#сравнение-клиент-сервер)
6. [Потоки данных](#потоки-данных)
7. [Управление конфликтами](#управление-конфликтами)
8. [Обработка ошибок и повторы](#обработка-ошибок-и-повторы)
9. [Безопасность](#безопасность)
10. [Мониторинг и диагностика](#мониторинг-и-диагностика)

---

## Обзор системы

Система синхронизации AutoSklad представляет собой распределённую архитектуру для двунаправленной синхронизации данных между центральным сервером и множеством клиентских устройств (вендинговых машин). Система обеспечивает:

- **Двунаправленную синхронизацию** данных между сервером и клиентами
- **Офлайн-работу** клиентов с последующей синхронизацией при восстановлении связи
- **Автоматическое разрешение конфликтов** при одновременных изменениях
- **Гарантированную доставку** команд через механизм очередей и повторов
- **Безопасную передачу** данных через AES-CBC шифрование
- **Гибкую схему данных** через автоматическое согласование структур БД

### Основные характеристики

- **Протокол**: HTTP REST API с AES-CBC шифрованием
- **Формат данных**: JSON с валидацией через JSON Schema
- **База данных**: SQLite (локально) + MySQL (опционально на сервере)
- **Паттерн синхронизации**: Command Queue Pattern с eventual consistency
- **Модель консистентности**: Eventual consistency (конечная согласованность)

---

## Архитектурные принципы

### 1. Command Pattern (Паттерн команд)

Все изменения данных представляются как команды (`Command`), которые:
- Имеют уникальный идентификатор (UUID)
- Содержат метаданные: таблица, операция (insert/update/delete), данные
- Хранятся в очереди до успешной синхронизации
- Сохраняются в JSON-файле для восстановления после сбоев

### 2. Разделение ответственности

Система разделена на слои:

```
┌─────────────────────────────────────────┐
│   Transport Layer (HTTP/AES)           │  ← Сетевая коммуникация
├─────────────────────────────────────────┤
│   Sync Layer (Logic_v2)                 │  ← Бизнес-логика синхронизации
│   - SyncProcessor                        │
│   - CommandSender/Receiver               │
│   - ConflictManager                      │
│   - DataMapper/Transformer               │
├─────────────────────────────────────────┤
│   Data Layer (CRUD)                     │  ← Доступ к данным
│   - SyncManager                          │
│   - BatchProcessor                       │
│   - CommandQueue                         │
├─────────────────────────────────────────┤
│   Database Layer (SQLAlchemy)           │  ← Хранилище данных
└─────────────────────────────────────────┘
```

### 3. Event-Driven Architecture

- Изменения в БД перехватываются через декораторы (`@sync_aware`)
- Команды помещаются в очередь через `INBOUND_QUEUES`
- Фоновый поток (`Runner`) обрабатывает очередь асинхронно
- Планировщик (APScheduler) запускает периодические задачи синхронизации

### 4. Resilience (Устойчивость к сбоям)

- **Персистентная очередь**: команды сохраняются в `command_queue.json`
- **Автоматические повторы**: RetryManager с экспоненциальным backoff
- **Транзакционность**: BatchProcessor обеспечивает атомарность операций
- **Мониторинг**: SyncMonitor отслеживает успехи и ошибки

---

## Компоненты системы

### Клиентская сторона (`client/dbSync/`)

#### 1. Runner.py
**Назначение**: Главный координатор синхронизации на клиенте

**Основные функции**:
- Создаёт и управляет фоновым потоком синхронизации
- Инициализирует все компоненты через `create_sync_components()`
- Запускает планировщик (APScheduler) для периодических задач
- Обрабатывает сообщения из `INBOUND_QUEUES[device_id]`

**Поток выполнения**:
```python
def runner():
    # 1. Создание компонентов
    components = create_sync_components(device_id, ...)
    
    # 2. Регистрация задач в планировщике
    scheduler.add_job(job_send, interval=15s)      # Отправка команд
    scheduler.add_job(job_fetch, interval=30s)    # Получение команд
    scheduler.add_job(job_process_retrying, interval=30s)  # Повторы
    
    # 3. Основной цикл обработки очереди
    while device_id in _active_schedulers:
        msg = queue_in.get(timeout=10)
        if msg_type == "local":
            processor.enqueue_local_command(msg)
        # ... другие типы сообщений
```

**Ключевые особенности**:
- Использует отдельный поток (`threading.Thread`) для синхронизации
- Обрабатывает типы сообщений: `local`, `handshake`, `push`, `pull`
- Координирует работу между HTTP-обработчиками и фоновым процессом

#### 2. SyncProcessor.py
**Назначение**: Центральный процессор синхронизации

**Основные методы**:

**`process_schema()`** - Handshake (согласование схемы)
```python
def process_schema(src_schema, client_schema_hash):
    # 1. Валидация входящей схемы
    json_validator.validate(src_schema, "handshake_request")
    
    # 2. Поиск в кэше или генерация маппинга
    mapping = schema_cache.get(client_schema_hash)
    if not mapping:
        mapping = schema_analyzer.generate_mapping(src_schema, server_schema)
        schema_cache.set(client_schema_hash, mapping)
    
    # 3. Возврат маппинга и хэша
    return {"mapping": mapping, "schema_hash": client_schema_hash}
```

**`process_push()`** - Обработка входящих команд от сервера
```python
def process_push(device, commands, client_schema_hash):
    # 1. Валидация JSON
    json_validator.validate({"commands": commands}, "push_commands")
    
    # 2. Обработка каждой команды
    for cmd in commands:
        # - Preprocess (DataTransformer)
        # - Validate
        # - Map incoming (DataMapper)
        # - Detect conflicts (ConflictManager)
        # - Resolve conflicts
        # - Prepare for batch execution
    
    # 3. Пакетное выполнение (BatchProcessor)
    results = batch_processor.execute_batch(operations)
    
    # 4. Обновление статусов
    statuses = _update_command_statuses(results)
    
    return statuses
```

**`prepare_pull()`** - Подготовка команд для отправки клиенту
```python
def prepare_pull(device, since, client_schema_hash):
    # 1. Получение pending команд из БД
    pending = cmd_crud.get_pending_for_device(device)
    records = record_crud.get_bulk_records([c.id for c in pending])
    
    # 2. Преобразование в формат клиента
    commands = []
    for cmd in pending:
        raw = records[cmd.id]
        json_data = data_mapper.map_outgoing(cmd.table_name, raw)
        post = data_transformer.postprocess(cmd.table_name, json_data)
        commands.append({...})
    
    return {"schema_hash": client_schema_hash, "commands": commands}
```

**`enqueue_local_command()`** - Добавление локальной команды в очередь
```python
def enqueue_local_command(cmd):
    queue.add_command(
        table=cmd["table"],
        operation=cmd["operation"],
        data=cmd["data"]
    )
```

#### 3. CommandQueue.py
**Назначение**: Персистентная очередь команд

**Структура команды**:
```python
{
    "id": "uuid",                    # Уникальный идентификатор
    "table": "Tools",                # Таблица БД
    "operation": "insert",           # insert|update|delete
    "data": {...},                   # Данные записи
    "status": "pending",             # pending|retrying|failed|done
    "timestamp": "2025-01-30T...",   # ISO 8601 UTC
    "retry_count": 0,                # Количество попыток
    "last_retry_timestamp": None     # Время последней попытки
}
```

**Основные методы**:
- `add_command()` - Добавление команды в очередь
- `get_pending_commands()` - Получение команд со статусом pending
- `get_retrying_commands()` - Получение команд на повторе
- `mark_as_done()` / `mark_as_failed()` / `mark_as_retrying()` - Обновление статусов
- `clear_done()` - Очистка выполненных команд

**Хранение**: JSON-файл `command_queue.json` для персистентности

#### 4. CommandSender.py
**Назначение**: Отправка команд на сервер

**Логика работы**:
```python
def send_pending():
    # 1. Проверка handshake
    _ensure_handshake()
    
    # 2. Обработка retrying команд
    retry_manager.retry_all_retrying()
    
    # 3. Получение pending команд
    pending = queue.get_pending_commands()
    
    # 4. Проверка порядка (retrying/failed старше pending)
    if has_older_retrying_or_failed(pending):
        return  # Не отправляем pending, пока не обработаны старые
    
    # 5. Отправка батчами (PUSH_BATCH_SIZE = 30)
    for batch in chunks(pending, PUSH_BATCH_SIZE):
        payload = {
            "device": device_id,
            "schema_hash": schema_hash,
            "commands": [...]
        }
        response = transport.send_push(endpoint, payload)
        
        # 6. Обновление статусов по ответу сервера
        for cmd in batch:
            if response.status == "COMPLETED":
                queue.mark_as_done(cmd.id)
            elif response.status == "FAILED":
                queue.mark_as_failed(cmd.id)
```

**Особенности**:
- Отправка батчами для оптимизации сетевого трафика
- Сохранение порядка команд
- Обработка retrying команд перед pending
- Автоматический handshake при необходимости

#### 5. CommandReceiver.py
**Назначение**: Получение команд от сервера

**Логика работы**:
```python
def fetch_and_apply():
    # 1. Проверка handshake
    _ensure_handshake()
    
    # 2. Запрос pull с параметрами
    params = {
        "device": device_id,
        "since": last_synced,        # Временная метка последней синхронизации
        "schema_hash": schema_hash
    }
    response = transport.send_pull(endpoint, params)
    
    # 3. Применение команд локально
    for cmd in response["commands"]:
        sync_processor.process_push(
            device=device_id,
            commands=[cmd],
            client_schema_hash=schema_hash
        )
        # Обновление last_synced
        if cmd["last_modified"] > last_synced:
            last_synced = cmd["last_modified"]
    
    # 4. Сохранение новой метки
    _save_last_synced(last_synced)
```

**Хранение метки**: Файл `last_synced.txt` с ISO-8601 timestamp

#### 6. DataMapper.py
**Назначение**: Преобразование данных между форматами клиента и сервера

**Два направления**:

**`map_incoming()`** - Сервер → Клиент
```python
def map_incoming(table, record, mapping=None):
    # 1. Сохранение защищённых полей (id, index)
    result = {field: record[field] for field in PROTECTED_FIELDS}
    
    # 2. Применение маппинга полей
    base_map = field_mappings.get(table, {})
    for remote_field, value in record.items():
        local_field = base_map.get(remote_field)
        if local_field:
            # 3. Применение конвертеров и типизации
            if local_field in converters:
                value = converters[local_field](value)
            elif local_field in type_map:
                value = type_map[local_field](value)
            result[local_field] = value
    
    return result
```

**`map_outgoing()`** - Клиент → Сервер
```python
def map_outgoing(table, record, mapping=None):
    # Обратный процесс: local_field → remote_field
    reverse_map = {local: remote for remote, local in base_map.items()}
    # ... аналогичная логика в обратном направлении
```

**Особенности**:
- Поддержка кастомных конвертеров для полей
- Автоматическое приведение типов (datetime, int, float, bool)
- Защита критических полей (id, index) от потери
- Pass-through режим при отсутствии маппинга

#### 7. DataTransformer.py
**Назначение**: Бизнес-логика валидации и трансформации данных

**Три этапа обработки**:

**`preprocess()`** - Предобработка входящих данных
```python
def preprocess(table, raw):
    rules = self.rules.get(table, {})
    data = raw.copy()
    for fn in rules.get('incoming', []):
        data = fn(data)  # Применение правил предобработки
    return data
```

**`validate()`** - Валидация данных
```python
def validate(table, data):
    fn = self.rules.get(table, {}).get('validate')
    if fn:
        return fn(data)  # Проверка бизнес-правил
    return True
```

**`postprocess()`** - Постобработка перед отправкой
```python
def postprocess(table, mapped):
    rules = self.rules.get(table, {})
    data = mapped.copy()
    for fn in rules.get('outgoing', []):
        data = fn(data)  # Применение правил постобработки
    return data
```

**Регистрация правил**:
```python
transformer.register_rule("Tools", "incoming", lambda d: {...})
transformer.register_rule("Tools", "validate", lambda d: d["count"] > 0)
transformer.register_rule("Tools", "outgoing", lambda d: {...})
```

#### 8. ConflictManager.py
**Назначение**: Обнаружение и разрешение конфликтов

**Типы конфликтов**:

**1. Структурные конфликты** (разные поля в схемах)
```python
def detect_structure_conflict(client_fields, server_fields):
    missing_on_server = [f for f in client_fields if f not in server_fields]
    missing_on_client = [f for f in server_fields if f not in client_fields]
    return missing_on_server + missing_on_client
```

**2. Конфликты данных** (разные значения в одинаковых полях)
```python
def detect_data_conflict(local_data, remote_data):
    return local_data != remote_data
```

**Стратегии разрешения**:

**LWW (Last-Write-Wins)** - По умолчанию
```python
def apply_data_strategy(local, remote, strategy="LWW"):
    # Специальная логика для таблицы Cell:
    if table == "Cell":
        # Массовые операции с сервера имеют приоритет
        if remote_status_stype in ("mass_load_init", "mass_load_ready", ...):
            return merged  # Принимаем удалённые данные
        
        # Защита локальных активных операций
        if local_status_stype in ("load_ready", "mass_load_ready"):
            return local_data  # Сохраняем локальные данные
    
    # Стандартная логика: принимаем удалённые данные
    return remote
```

**MergeFields** - Слияние полей
```python
def resolve(local, remote):
    merged = local.copy()
    merged.update(remote)  # Перезаписываем пересекающиеся поля
    return merged
```

**VectorClock** - Векторные часы (заглушка для будущей реализации)

#### 9. BatchProcessor.py
**Назначение**: Атомарное выполнение операций в транзакциях

**Логика работы**:
```python
def execute_batch(operations):
    results = []
    try:
        with session.begin_nested():  # Вложенная транзакция
            for op in operations:
                try:
                    res = sync_manager.process_sync_command(op, sync_context=True)
                    results.append({
                        "command_id": op["command_id"],
                        "success": True,
                        "new_id": res.get("id")
                    })
                except Exception as e:
                    results.append({
                        "command_id": op["command_id"],
                        "success": False,
                        "error": str(e)
                    })
                    raise  # Откат всей транзакции
    except SQLAlchemyError:
        return results  # Возвращаем накопленные результаты
    
    return results
```

**Особенности**:
- Все операции в одной транзакции
- Откат при первой ошибке
- Возврат детальных результатов по каждой операции

#### 10. RetryManager.py
**Назначение**: Управление повторными попытками неудачных команд

**Логика работы**:
```python
def retry_all_retrying():
    retrying = queue.get_retrying_commands()
    now = datetime.utcnow()
    
    for cmd in retrying:
        # Проверка max_retries
        if retry_count >= max_retries:
            queue.mark_as_failed(cmd.id)
            continue
        
        # Проверка времени с последней попытки
        last_retry = queue.get_last_retry_timestamp(cmd.id)
        if time_since_last < base_delay:
            continue  # Ещё рано для повтора
        
        # Попытка отправки
        if sender.send_single_command(cmd):
            queue.mark_as_done(cmd.id)
        else:
            queue.add_retry_count(cmd.id)
            queue.update_last_retry_timestamp(cmd.id, now)
```

**Параметры**:
- `max_retries`: Максимум попыток (по умолчанию 5)
- `base_delay`: Базовая задержка между попытками (по умолчанию 60 сек)
- Экспоненциальный backoff: `delay = base_delay * 2^(retry_count - 1)`

#### 11. SyncManager.py
**Назначение**: Фасад для выполнения CRUD-операций

**Основные методы**:
```python
def process_sync_command(command, sync_context=True):
    table, op, data, rec_id = _parse_command(command)
    crud = _get_crud(table)
    
    if op == "insert":
        return _handle_insert(crud, table, data, rec_id, sync_context)
    elif op == "update":
        return _handle_update(crud, data, rec_id)
    elif op == "delete":
        return _handle_delete(crud, rec_id)

def get_current_data(table, rec_id, work_session):
    # Получение текущего состояния записи для конфликтов
    crud = crud_registry[table](work_session)
    record = crud.get(rec_id)
    return record.to_dict() if record else None
```

**Особенности**:
- Поддержка `sync_context` для различения синхронизации и локальных операций
- Специальная логика для инкремента `count` в таблицах Tools/Consumption
- Upsert-логика при конфликтах IntegrityError
- Нормализация ID (id/index)

#### 12. SyncMonitor.py
**Назначение**: Сбор метрик синхронизации

**Метрики**:
- `successful_count`: Количество успешных операций
- `failed_count`: Количество неудачных операций
- `average_time`: Среднее время обработки
- `total_time`: Суммарное время обработки

**Использование**:
```python
start = time.time()
try:
    # ... синхронизация ...
    sync_monitor.record_success(time.time() - start)
except Exception:
    sync_monitor.record_failure(time.time() - start)
    raise
```

#### 13. Decorators.py
**Назначение**: Перехват изменений БД для создания команд синхронизации

**Декоратор `@sync_aware`**:
```python
@sync_aware
def add(self, **kwargs):
    # 1. Проверка флагов
    if dbSync.init_db or kwargs.get('sync_context'):
        return func(self, **kwargs)  # Пропуск синхронизации
    
    # 2. Валидация через DataTransformer
    transformer.validate(table_name, kwargs)
    
    # 3. Вызов CRUD-метода
    result = func(self, **kwargs)
    
    # 4. Добавление команды в очередь
    queue_in.put({
        "type": "local",
        "table": table_name,
        "operation": method_name,
        "data": kwargs
    })
    
    return result
```

**Особенности**:
- Автоматическое создание команд при изменениях БД
- Пропуск синхронизации при инициализации БД или sync_context
- Валидация данных перед созданием команды

### Серверная сторона (`server/dbSync/`)

Серверная сторона использует те же компоненты, что и клиент, но с некоторыми отличиями:

#### 1. Runner.py (сервер)
**Отличия от клиента**:
- Использует `get_db_session()` вместо `SessionLocal()`
- Обрабатывает команды типа `local` перед `pull` для включения их в ответ
- Устанавливает `processor.current_device_id` для правильной маршрутизации

#### 2. Transport/routers.py
**Назначение**: HTTP endpoints для синхронизации

**Эндпоинты**:

**`POST /sync/push?device=<id>`**
```python
async def api_sync_push(device: int, request: Request):
    # 1. Чтение тела (JSON или AES-зашифрованные байты)
    raw_body = await request.body()
    
    # 2. Дешифровка (если нужно)
    parsed = json.loads(raw_body) or AESDecryptor(AES_KEY).decrypt(raw_body)
    
    # 3. Валидация через JSONSchemaValidator
    json_validator.validate(parsed, "push_commands")
    
    # 4. Отправка в очередь фонового потока
    queue_in.put({
        "type": "push",
        "payload": parsed["commands"],
        "hash": parsed["schema_hash"],
        "reply_queue": reply_queue
    })
    
    # 5. Ожидание результата
    statuses = reply_queue.get(timeout=50)
    
    return {"statuses": statuses}
```

**`GET /sync/pull?device=<id>&since=<timestamp>`**
```python
def api_sync_pull(device: int, since: str = ""):
    # 1. Отправка запроса в очередь
    queue_in.put({
        "type": "pull",
        "device": device,
        "since": since,
        "hash": "",
        "reply_queue": reply_queue
    })
    
    # 2. Ожидание результата
    response = reply_queue.get(timeout=50)
    
    return PullResponseModel(**response)
```

**`POST /sync/handshake?device=<id>`**
```python
async def api_sync_handshake(device: int, request: Request):
    # 1. Дешифровка AES-CBC
    raw = await request.body()
    iv = raw[:16]
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(raw[16:]), AES.block_size)
    
    # 2. Парсинг JSON схемы
    src_schema = json.loads(decrypted.decode("utf-8"))
    
    # 3. Вычисление хэша
    schema_hash = hashlib.sha256(json.dumps(src_schema, sort_keys=True).encode()).hexdigest()
    
    # 4. Отправка в очередь
    queue_in.put({
        "type": "handshake",
        "payload": src_schema,
        "hash": schema_hash,
        "reply_queue": reply_queue
    })
    
    # 5. Получение результата и шифрование ответа
    result = reply_queue.get(timeout=50)
    encrypted = AES.encrypt(json.dumps(result).encode(), AES_KEY)
    
    return Response(content=encrypted, media_type="application/octet-stream")
```

#### 3. SyncProcessor.py (сервер)
**Отличия от клиента**:
- Использует `DB.session.get_db_session()` для работы с основной БД
- Обрабатывает команды от клиентов через `process_push()`
- Генерирует команды для клиентов через `prepare_pull()`
- Поддерживает обработку локальных команд (`enqueue_local_command`) для включения в pull

---

## Процесс синхронизации

### Этап 1: Handshake (Согласование схемы)

**Цель**: Установить соответствие между схемами БД клиента и сервера

**Последовательность**:

1. **Клиент отправляет схему**:
   ```
   Client → Server: POST /sync/handshake?device=1
   Body (AES-encrypted): {
     "Tools": {"id": "integer", "name": "string", "count": "integer"},
     "Cell": {"id": "integer", "status_id": "integer", ...}
   }
   ```

2. **Сервер обрабатывает**:
   - Вычисляет SHA256 хэш схемы клиента
   - Проверяет кэш маппингов (`SchemaCache`)
   - Если маппинга нет → генерирует через `SchemaAnalyzer`
   - Сохраняет маппинг в кэш под хэшем клиента

3. **Сервер возвращает маппинг**:
   ```
   Server → Client: (AES-encrypted)
   {
     "mapping": {
       "Tools": {"name": "tools_name", "count": "tools_count"},
       "Cell": {"status_id": "cell_status_id"}
     },
     "schema_hash": "abc123..."
   }
   ```

4. **Клиент сохраняет маппинг**:
   - Обновляет `DataMapper.field_mappings`
   - Сохраняет `schema_hash` для последующих запросов

**Диаграмма последовательности**:
```
Client                    Server
  |                         |
  |--[AES] schema---------->|
  |                         |--[SchemaCache] get(hash)
  |                         |<--[null]
  |                         |--[SchemaAnalyzer] generate_mapping()
  |                         |--[SchemaCache] set(hash, mapping)
  |<--[AES] mapping---------|
  |                         |
```

### Этап 2: Push (Отправка изменений клиента на сервер)

**Цель**: Синхронизировать локальные изменения клиента с сервером

**Последовательность**:

1. **Клиент собирает pending команды**:
   ```python
   pending = command_queue.get_pending_commands()
   # Фильтрация: нет ли retrying/failed старше pending
   ```

2. **Клиент формирует payload**:
   ```python
   payload = {
       "device": device_id,
       "schema_hash": cached_schema_hash,
       "commands": [
           {
               "id": "uuid1",
               "table": "Tools",
               "operation": "INSERT",
               "data": {"name": "Drill", "count": 5}
           },
           ...
       ]
   }
   ```

3. **Клиент шифрует и отправляет**:
   ```
   Client → Server: POST /sync/push?device=1
   Body (AES-encrypted): payload
   ```

4. **Сервер дешифрует и валидирует**:
   - AES-дешифровка
   - JSON Schema валидация
   - Pydantic валидация

5. **Сервер обрабатывает команды**:
   ```python
   for cmd in commands:
       # Preprocess
       cleaned = data_transformer.preprocess(cmd["table"], cmd["data"])
       
       # Validate
       if not data_transformer.validate(cmd["table"], cleaned):
           failed.append(cmd)
           continue
       
       # Map incoming (server format → local format)
       local = data_mapper.map_incoming(cmd["table"], cleaned, mapping)
       
       # Detect conflicts
       existing = sync_manager.get_current_data(cmd["table"], rec_id)
       if existing and conflict_manager.detect_data_conflict(existing, local):
           local = conflict_manager.apply_data_strategy(existing, local, "LWW")
       
       # Prepare for batch
       operations.append({
           "command_id": cmd["id"],
           "table": cmd["table"],
           "operation": cmd["operation"],
           "data": local,
           "id": rec_id
       })
   ```

6. **Сервер выполняет батч**:
   ```python
   results = batch_processor.execute_batch(operations)
   # Все операции в одной транзакции
   ```

7. **Сервер возвращает статусы**:
   ```
   Server → Client: (AES-encrypted)
   {
     "statuses": [
       {"id": "uuid1", "status": "COMPLETED"},
       {"id": "uuid2", "status": "FAILED", "error": "..."}
     ]
   }
   ```

8. **Клиент обновляет очередь**:
   ```python
   for status in response["statuses"]:
       if status["status"] == "COMPLETED":
           queue.mark_as_done(status["id"])
       elif status["status"] == "FAILED":
           queue.mark_as_failed(status["id"])
           retry_manager.schedule_retry(cmd)
   ```

**Диаграмма последовательности**:
```
Client                    Server
  |                         |
  |--[AES] commands-------->|
  |                         |--[Decrypt]
  |                         |--[Validate]
  |                         |--[Process each]
  |                         |   |--[Preprocess]
  |                         |   |--[Map incoming]
  |                         |   |--[Detect conflicts]
  |                         |   |--[Resolve conflicts]
  |                         |--[Batch execute]
  |                         |--[Update statuses]
  |<--[AES] statuses--------|
  |                         |
  |--[Update queue]         |
```

### Этап 3: Pull (Получение изменений с сервера)

**Цель**: Получить изменения, сделанные на сервере или другими клиентами

**Последовательность**:

1. **Клиент запрашивает изменения**:
   ```
   Client → Server: GET /sync/pull?device=1&since=2025-01-30T10:00:00Z
   ```

2. **Сервер обрабатывает запрос**:
   ```python
   # Получение pending команд для устройства
   pending = cmd_crud.get_pending_for_device(device)
   
   # Фильтрация по since (если указано)
   if since:
       pending = [c for c in pending if c.created_at > since]
   
   # Получение данных записей
   records = record_crud.get_bulk_records([c.id for c in pending])
   ```

3. **Сервер преобразует в формат клиента**:
   ```python
   commands = []
   for cmd in pending:
       raw = records[cmd.id]
       # Map outgoing (local format → client format)
       json_data = data_mapper.map_outgoing(cmd.table_name, raw)
       # Postprocess
       post = data_transformer.postprocess(cmd.table_name, json_data)
       
       commands.append({
           "id": cmd.id,
           "table": cmd.table_name,
           "operation": cmd.operation.upper(),
           "data": post,
           "last_modified": record.last_modified.isoformat()
       })
   ```

4. **Сервер возвращает команды**:
   ```
   Server → Client: (AES-encrypted)
   {
     "schema_hash": "abc123...",
     "commands": [
       {
         "id": 123,
         "table": "Tools",
         "operation": "UPDATE",
         "data": {"id": 5, "count": 10},
         "last_modified": "2025-01-30T12:00:00Z"
       },
       ...
     ]
   }
   ```

5. **Клиент применяет команды локально**:
   ```python
   for cmd in response["commands"]:
       # Использует тот же process_push для применения
       sync_processor.process_push(
           device=device_id,
           commands=[cmd],
           client_schema_hash=schema_hash
       )
       
       # Обновление last_synced
       if cmd["last_modified"] > last_synced:
           last_synced = cmd["last_modified"]
   ```

6. **Клиент сохраняет метку времени**:
   ```python
   _save_last_synced(last_synced)  # В файл last_synced.txt
   ```

**Диаграмма последовательности**:
```
Client                    Server
  |                         |
  |--[GET] pull?since=...-->|
  |                         |--[Query pending commands]
  |                         |--[Get records data]
  |                         |--[Map outgoing]
  |                         |--[Postprocess]
  |<--[AES] commands--------|
  |                         |
  |--[Apply locally]        |
  |--[Update last_synced]   |
```

### Периодическая синхронизация

**Планировщик (APScheduler)**:

```python
# На клиенте (Runner.py)
scheduler.add_job(job_send, 'interval', seconds=15)      # Push каждые 15 сек
scheduler.add_job(job_fetch, 'interval', seconds=30)    # Pull каждые 30 сек
scheduler.add_job(job_process_retrying, 'interval', seconds=30)  # Повторы каждые 30 сек
```

**Цикл синхронизации**:
```
┌─────────────────────────────────────┐
│  Каждые 15 сек: Push                │
│  - Отправка pending команд          │
│  - Обновление статусов              │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Каждые 30 сек: Pull                │
│  - Запрос изменений с сервера       │
│  - Применение локально               │
│  - Обновление last_synced           │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Каждые 30 сек: Retry                │
│  - Обработка retrying команд         │
│  - Повторная отправка                │
│  - Обновление retry_count            │
└─────────────────────────────────────┘
```

---

## Сравнение клиент-сервер

### Общие компоненты

Оба используют одинаковые компоненты из `Logic_v2/`:
- `SyncProcessor` - Центральный процессор
- `CommandQueue` - Очередь команд
- `CommandSender` / `CommandReceiver` - Отправка/получение
- `DataMapper` / `DataTransformer` - Преобразование данных
- `ConflictManager` - Разрешение конфликтов
- `BatchProcessor` - Пакетная обработка
- `RetryManager` - Повторы
- `SyncMonitor` - Мониторинг

### Различия

| Аспект | Клиент | Сервер |
|--------|--------|--------|
| **База данных** | `vending.db` (локальная) | `web_vending.db` (центральная) |
| **Sync DB** | `dbSync/Model/sync.db` | `dbSync/Model/sync.db` |
| **HTTP Server** | Встроенный FastAPI (порт 8080) | Основной FastAPI (порт 8000) |
| **Роль в синхронизации** | Инициатор push/pull | Обработчик push, генератор pull |
| **CommandQueue** | Хранит локальные изменения | Хранит команды для клиентов |
| **Transport** | Клиент (отправка запросов) | Сервер (приём запросов) |
| **Handshake** | Отправляет схему | Генерирует маппинг |
| **Локальные команды** | Создаются через `@sync_aware` | Создаются через `enqueue_local_command` |

### Потоки данных

**Клиент → Сервер (Push)**:
```
Локальная БД
    ↓ [@sync_aware decorator]
CommandQueue (pending)
    ↓ [CommandSender.send_pending()]
TransportService (AES encrypt)
    ↓ [HTTP POST /sync/push]
Сервер Transport/routers.py
    ↓ [Queue → Runner]
Сервер SyncProcessor.process_push()
    ↓ [BatchProcessor]
Сервер БД (web_vending.db)
```

**Сервер → Клиент (Pull)**:
```
Сервер БД (web_vending.db)
    ↓ [CommandCRUD.get_pending_for_device()]
Сервер SyncProcessor.prepare_pull()
    ↓ [DataMapper.map_outgoing()]
Сервер Transport/routers.py
    ↓ [HTTP GET /sync/pull]
Клиент TransportService (AES decrypt)
    ↓ [CommandReceiver.fetch_and_apply()]
Клиент SyncProcessor.process_push()
    ↓ [BatchProcessor]
Клиент БД (vending.db)
```

---

## Потоки данных

### Создание команды на клиенте

```
Пользователь → GUI → CRUD метод
    ↓
[@sync_aware decorator]
    ↓
Проверка флагов (init_db? sync_context?)
    ↓ [Нет]
Валидация (DataTransformer.validate)
    ↓
Выполнение CRUD операции
    ↓
Создание команды в INBOUND_QUEUES[device_id]
    ↓
Runner обрабатывает сообщение типа "local"
    ↓
SyncProcessor.enqueue_local_command()
    ↓
CommandQueue.add_command()
    ↓
Сохранение в command_queue.json
```

### Обработка команды на сервере

```
HTTP POST /sync/push
    ↓
Transport/routers.py (дешифровка AES)
    ↓
Валидация (JSONSchemaValidator)
    ↓
Очередь INBOUND_QUEUES[device_id]
    ↓
Runner обрабатывает сообщение типа "push"
    ↓
SyncProcessor.process_push()
    ↓
Для каждой команды:
  - DataTransformer.preprocess()
  - DataTransformer.validate()
  - DataMapper.map_incoming()
  - ConflictManager.detect_data_conflict()
  - ConflictManager.apply_data_strategy()
    ↓
BatchProcessor.execute_batch()
    ↓
SyncManager.process_sync_command()
    ↓
CRUD операция в БД
    ↓
Обновление статусов (CommandStatusCRUD)
    ↓
Возврат статусов клиенту
```

### Разрешение конфликтов

```
Входящая команда (remote)
    ↓
DataMapper.map_incoming() → local format
    ↓
SyncManager.get_current_data() → existing
    ↓
ConflictManager.detect_data_conflict(existing, local)
    ↓ [Конфликт обнаружен]
ConflictManager.apply_data_strategy()
    ↓
Стратегия LWW:
  - Для Cell: проверка массовых операций
  - Для Cell: защита активных операций
  - Для остальных: стандартная логика
    ↓
Разрешённые данные
    ↓
BatchProcessor.execute_batch()
```

---

## Управление конфликтами

### Типы конфликтов

#### 1. Структурные конфликты

**Причина**: Разные схемы БД на клиенте и сервере

**Пример**:
```
Клиент: Tools {id, name, count, description}
Сервер: Tools {id, tools_name, tools_count, desc}
```

**Разрешение**:
- `SchemaAnalyzer` генерирует маппинг при handshake
- `MappingConfigurator` позволяет ручную настройку
- `SchemaCache` кэширует маппинги по хэшу схемы

#### 2. Конфликты данных

**Причина**: Одновременное изменение одной записи

**Пример**:
```
Клиент: Cell {id: 1, status_id: 3}  (load_ready)
Сервер: Cell {id: 1, status_id: 1}  (start_system)
```

**Разрешение через стратегии**:

**LWW (Last-Write-Wins)** - По умолчанию
- Принимает данные с более поздним timestamp
- Специальная логика для таблицы `Cell`:
  - Массовые операции с сервера имеют приоритет
  - Локальные активные операции защищены от затирания
  - Результаты команд выдачи инструмента принимаются

**MergeFields** - Слияние полей
- Объединяет поля из обеих версий
- Удалённые данные перезаписывают локальные

**VectorClock** - Векторные часы (заглушка)

### Специальная логика для Cell

```python
if table == "Cell":
    # 1. Массовые операции с сервера имеют приоритет
    if remote_status_stype in ("mass_load_init", "mass_load_ready", 
                                "mass_drop_init", "mass_drop_ready"):
        return merged  # Принимаем удалённые данные
    
    # 2. Защита локальных активных операций
    if local_status_stype in ("load_ready", "mass_load_ready"):
        # ИСКЛЮЧЕНИЕ: Результат команды выдачи инструмента
        if remote_status_stype == "start_system" and remote_status_id == 1:
            return merged  # Принимаем удалённые данные
        return local_data  # Сохраняем локальные данные
    
    # 3. Стандартная логика по status_id
    if local_status_id != remote_status_id:
        return local_data  # Сохраняем локальные данные
```

---

## Обработка ошибок и повторы

### Механизм повторов

**Статусы команд**:
- `pending` - Ожидает отправки
- `retrying` - На повторной попытке
- `failed` - Неудачная после max_retries
- `done` - Успешно обработана

**Процесс повтора**:

1. **Неудачная отправка**:
   ```python
   try:
       response = transport.send_push(endpoint, payload)
   except Exception:
       queue.mark_as_retrying(cmd.id)
       queue.add_retry_count(cmd.id)
   ```

2. **Планирование повтора**:
   ```python
   retry_manager.schedule_retry(cmd, delay=base_delay * 2^(retry_count-1))
   ```

3. **Обработка retrying команд**:
   ```python
   def retry_all_retrying():
       retrying = queue.get_retrying_commands()
       for cmd in retrying:
           if time_since_last_retry >= base_delay:
               if sender.send_single_command(cmd):
                   queue.mark_as_done(cmd.id)
               else:
                   queue.add_retry_count(cmd.id)
                   if retry_count >= max_retries:
                       queue.mark_as_failed(cmd.id)
   ```

**Параметры**:
- `max_retries`: 5 (по умолчанию)
- `base_delay`: 60 секунд
- Экспоненциальный backoff: `delay = base_delay * 2^(retry_count - 1)`

### Защита от дубликатов

**На уровне команды**:
- UUID команды гарантирует уникальность
- Проверка существования записи перед INSERT

**На уровне данных**:
- Проверка `pending/retrying` команд перед применением pull
- Защита "Time Travel": локальные данные новее → не перезаписываем

**На уровне транзакций**:
- BatchProcessor использует транзакции для атомарности
- Откат при первой ошибке в батче

---

## Безопасность

### Шифрование

**Алгоритм**: AES-CBC с PKCS7 padding

**Процесс шифрования**:
```python
# Генерация IV
iv = os.urandom(16)

# Шифрование
cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
plaintext = json.dumps(payload).encode("utf-8")
padded = pad(plaintext, AES.block_size)
ciphertext = cipher.encrypt(padded)

# Формат: IV (16 байт) + ciphertext
encrypted = iv + ciphertext
```

**Процесс дешифрования**:
```python
# Извлечение IV
iv = encrypted[:16]
ciphertext = encrypted[16:]

# Дешифрование
cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
padded_plaintext = cipher.decrypt(ciphertext)
plaintext = unpad(padded_plaintext, AES.block_size)

# Парсинг JSON
payload = json.loads(plaintext.decode("utf-8"))
```

**Ключ**: Конфигурируется в `options.py` (сервер) и `config.json` (клиент)

### Валидация

**JSON Schema валидация**:
- Схемы в `Logic_v2/schemas/`
- Валидация запросов и ответов
- Типы: `handshake_request`, `push_commands`, `pull_response`

**Pydantic валидация**:
- Модели в `Transport/routers.py`
- Строгая типизация полей
- Автоматическая валидация типов

**Бизнес-валидация**:
- `DataTransformer.validate()` для каждой таблицы
- Проверка обязательных полей
- Проверка бизнес-правил

---

## Мониторинг и диагностика

### SyncMonitor

**Метрики**:
- `successful_count`: Количество успешных операций
- `failed_count`: Количество неудачных операций
- `average_time`: Среднее время обработки
- `total_time`: Суммарное время обработки

**Использование**:
```python
start = time.time()
try:
    # ... синхронизация ...
    sync_monitor.record_success(time.time() - start)
except Exception:
    sync_monitor.record_failure(time.time() - start)
    raise

metrics = sync_monitor.get_metrics()
```

### DiagnosticLogger

**Уровни логирования**:
- `log_info()` - Информационные сообщения
- `log_debug()` - Отладочная информация
- `log_warning()` - Предупреждения
- `log_error()` - Ошибки с контекстом

**Контекст**:
```python
diagnostic_logger.log_error(
    "Push failed",
    {
        "error": str(ex),
        "traceback": traceback.format_exc(),
        "device": device_id,
        "command_count": len(commands)
    }
)
```

### Логирование потоков

**Формат**:
```
[ПОТОК][thread-name][component][method] message [timestamp]
```

**Примеры**:
```
[ПОТОК][sync-thread-1][CommandSender][send_pending] Отправка батча из 5 команд [2025-01-30 12:00:00]
[ПОТОК][sync-thread-1][SyncProcessor][process_push] Push завершен успешно [2025-01-30 12:00:01]
```

### Файлы логов

- `command_queue.json` - Состояние очереди команд
- `last_synced.txt` - Метка времени последней синхронизации
- `logs/` - Директория с логами приложения
- `crash.log` - Логи критических ошибок

---

## Заключение

Система синхронизации AutoSklad представляет собой комплексное решение для двунаправленной синхронизации данных между центральным сервером и множеством клиентских устройств. Архитектура основана на паттерне Command Queue с eventual consistency, что обеспечивает надёжную работу в условиях нестабильной сети и офлайн-режима.

**Ключевые преимущества**:
- ✅ Надёжность через персистентные очереди и повторы
- ✅ Гибкость через автоматическое согласование схем
- ✅ Безопасность через AES-шифрование
- ✅ Масштабируемость через батчевую обработку
- ✅ Отказоустойчивость через транзакции и откаты

**Области для улучшения**:
- Векторные часы для более точного разрешения конфликтов
- WebSocket транспорт для real-time синхронизации
- Метрики Prometheus для мониторинга в production
- Распределённые транзакции для мульти-серверных сценариев
