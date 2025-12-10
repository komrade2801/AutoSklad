# Диаграммы последовательностей системы синхронизации

## Оглавление

1. [Handshake - согласование схем](#handshake---согласование-схем)
2. [Push - отправка локальных изменений](#push---отправка-локальных-изменений)
3. [Pull - получение удаленных изменений](#pull---получение-удаленных-изменений)
4. [Обработка ошибок и повторы](#обработка-ошибок-и-повторы)
5. [Полный цикл двусторонней синхронизации](#полный-цикл-двусторонней-синхронизации)

---

## Handshake - согласование схем

### Инициация handshake (первый запрос)

```mermaid
sequenceDiagram
    participant App as Application
    participant Sender as CommandSender
    participant Proc as SyncProcessor
    participant Trans as TransportService
    participant Server as Server API
    participant SProc as Server SyncProcessor
    participant Cache as SchemaCache
    participant Analyzer as SchemaAnalyzer

    App->>Sender: send_pending()
    Sender->>Sender: _ensure_handshake()
    
    Note over Sender: Первый вызов - handshake не выполнен
    
    Sender->>Proc: sync_manager.get_local_schema()
    Proc-->>Sender: client_schema
    
    Sender->>Trans: send_schema("/sync/handshake", client_schema, device_id)
    
    Note over Trans: Формирует запрос
    Trans->>Trans: JSON serialize schema
    Trans->>Trans: AES encrypt
    Trans->>Trans: HMAC sign
    
    Trans->>Server: POST /sync/handshake?device=X<br/>Headers: Authorization, X-Signature<br/>Body: encrypted schema
    
    Server->>Server: Verify HMAC signature
    Server->>Server: AES decrypt
    Server->>Server: Parse JSON
    
    Server->>SProc: process_schema(client_schema, schema_hash)
    
    SProc->>SProc: JSONSchemaValidator.validate(schema, "handshake_request")
    
    SProc->>Cache: get(schema_hash)
    Cache-->>SProc: None (первый запрос)
    
    SProc->>Analyzer: generate_mapping(client_schema, server_schema)
    
    Note over Analyzer: Сравнивает схемы:<br/>- Таблицы<br/>- Поля<br/>- Типы данных
    
    Analyzer-->>SProc: mapping = {table: {client_field: server_field}}
    
    SProc->>Cache: set(schema_hash, mapping)
    Cache-->>SProc: saved
    
    SProc->>SProc: JSONSchemaValidator.validate(response, "handshake_response")
    SProc-->>Server: {mapping, schema_hash}
    
    Server->>Server: JSON serialize
    Server->>Server: AES encrypt
    Server->>Server: HMAC sign
    
    Server-->>Trans: HTTP 200<br/>Body: encrypted response
    
    Trans->>Trans: Verify HMAC
    Trans->>Trans: AES decrypt
    Trans->>Trans: Parse JSON
    Trans-->>Sender: {mapping, schema_hash}
    
    Sender->>Proc: update_schema(mapping, schema_hash)
    Sender->>Sender: data_mapper.update_field_mappings(mapping)
    Sender->>Sender: _handshaken = True
    
    Note over Sender: Handshake завершен<br/>Следующие запросы используют<br/>сохраненный mapping
```

### Повторный запрос (mapping в кэше)

```mermaid
sequenceDiagram
    participant Sender as CommandSender
    participant Trans as TransportService
    participant Server as Server API
    participant SProc as Server SyncProcessor
    participant Cache as SchemaCache

    Sender->>Sender: _ensure_handshake()
    
    Note over Sender: _handshaken = True<br/>Пропускаем handshake
    
    Sender->>Trans: send_push(endpoint, payload)
    
    Note over Trans: Используем сохраненный<br/>schema_hash из handshake
    
    Trans->>Server: POST /sync/push?device=X<br/>Body: {device, schema_hash, commands}
    
    Server->>SProc: process_push(device, commands, schema_hash)
    
    SProc->>SProc: _get_mapping(schema_hash)
    SProc->>Cache: get(schema_hash)
    Cache-->>SProc: mapping (из кэша)
    
    Note over SProc: Используем сохраненный mapping<br/>Без генерации нового
```

---

## Push - отправка локальных изменений

### Сценарий: Пользователь добавляет инструмент

```mermaid
sequenceDiagram
    participant User as User
    participant App as Application
    participant CRUD as ToolsCRUD
    participant Dec as @sync_aware
    participant Queue as INBOUND_QUEUE
    participant Runner as Runner Thread
    participant CmdQueue as CommandQueue
    participant Sched as APScheduler
    participant Sender as CommandSender
    participant Trans as DataTransformer
    participant TServ as TransportService
    participant Server as Server
    participant SProc as Server SyncProcessor
    participant Orderer as CommandOrderer
    participant Batch as BatchProcessor
    participant SMan as SyncManager

    User->>App: add_tool(name="Молоток", count=5)
    App->>CRUD: add(name="Молоток", count=5)
    
    Note over CRUD: @sync_aware декоратор
    
    CRUD->>Dec: wrapper(self, name="Молоток", count=5)
    
    Dec->>Dec: Проверка dbSync.init_db<br/>(False - нормальный режим)
    Dec->>Dec: Проверка sync_context<br/>(False - локальное изменение)
    Dec->>Dec: Вычисление payload_key<br/>для дедупликации
    Dec->>Dec: Проверка в _state[device_id]<br/>(не найдено - новая операция)
    
    Dec->>Dec: transformer.validate(table, kwargs)
    
    Dec->>CRUD: add(name="Молоток", count=5)
    CRUD-->>Dec: result = Tool(id=42, name="Молоток", count=5)
    
    Dec->>Dec: _state[device_id][dedup_key] = result
    
    Dec->>Queue: put({<br/>  type: "local",<br/>  table: "Tools",<br/>  operation: "add",<br/>  data: {index: 42, name: "Молоток", count: 5}<br/>})
    
    Dec-->>App: Tool(id=42)
    App-->>User: "Инструмент добавлен"
    
    Note over Runner: Отдельный поток<br/>обрабатывает очередь
    
    Runner->>Queue: get(timeout=10)
    Queue-->>Runner: msg = {type: "local", ...}
    
    Runner->>SProc: enqueue_local_command(msg)
    SProc->>CmdQueue: add_command(table="Tools", operation="add", data={...})
    
    CmdQueue->>CmdQueue: Генерация UUID
    CmdQueue->>CmdQueue: Создание команды:<br/>{<br/>  id: uuid,<br/>  table: "Tools",<br/>  operation: "add",<br/>  data: {...},<br/>  status: "pending",<br/>  timestamp: ISO,<br/>  retry_count: 0<br/>}
    CmdQueue->>CmdQueue: Добавление в queue[]
    CmdQueue->>CmdQueue: _save_queue() → JSON file
    
    Note over Sched: job_send запускается<br/>каждые 60 секунд
    
    Sched->>Sender: send_pending()
    
    Sender->>Sender: _ensure_handshake()
    Note over Sender: Handshake выполнен ранее
    
    Sender->>CmdQueue: get_pending_commands()
    CmdQueue-->>Sender: [{id: uuid, table: "Tools", ...}]
    
    Sender->>Trans: postprocess("Tools", data)
    
    Note over Trans: Обогащение данных:<br/>добавляет поля из ToolTypes
    
    Trans-->>Sender: enriched_data = {<br/>  index: 42,<br/>  name: "Молоток",<br/>  count: 5,<br/>  description: "...",<br/>  img: "..."<br/>}
    
    Sender->>Sender: Формирование payload:<br/>{<br/>  device: 1,<br/>  schema_hash: "abc...",<br/>  commands: [{<br/>    id: uuid,<br/>    table: "Tools",<br/>    operation: "INSERT",<br/>    data: enriched_data<br/>  }]<br/>}
    
    Sender->>TServ: send_push("/sync/push", payload)
    
    TServ->>TServ: JSON serialize
    TServ->>TServ: AES encrypt
    TServ->>TServ: HMAC sign
    
    TServ->>Server: POST /sync/push?device=1
    
    Server->>Server: Verify HMAC
    Server->>Server: AES decrypt
    Server->>Server: Parse JSON
    
    Server->>SProc: process_push(device=1, commands=[...], schema_hash)
    
    SProc->>SProc: JSONSchemaValidator.validate(commands)
    
    Note over SProc: 🆕 Оптимизация команд
    
    SProc->>Orderer: order_and_validate(commands)
    
    Orderer->>Orderer: Группировка по (table, record_id)
    Orderer->>Orderer: Сжатие последовательностей:<br/>ADD+DELETE → DELETE
    Orderer->>Orderer: Топологическая сортировка:<br/>DELETE → UPDATE → ADD
    Orderer->>Orderer: Проверка FK зависимостей
    
    Orderer-->>SProc: (optimized_commands, warnings)
    
    Note over SProc: Сжатие: 15 → 8 команд (46.7%)
    
    SProc->>SProc: Фильтрация дубликатов:<br/>sync_manager.get_current_data(table, id)<br/>Сравнение с existing
    
    Note over SProc: Если дубликат - пропускаем
    
    SProc->>SProc: Для каждой команды:<br/>_process_single(cmd, mapping)
    
    SProc->>SProc: DataTransformer.preprocess(table, data)
    SProc->>SProc: DataTransformer.validate(table, data)
    SProc->>SProc: ConflictManager.detect_structure_conflict()
    SProc->>SProc: DataMapper.map_incoming(table, data, mapping)
    SProc->>SProc: DataTransformer.postprocess(table, data)
    SProc->>SProc: ConflictManager.detect_data_conflict()
    
    Note over SProc: Подготовлены операции<br/>для BatchProcessor
    
    SProc->>Batch: execute_batch(operations)
    
    Batch->>Batch: _link_consumption_to_history()
    
    Batch->>Batch: session.begin_nested() (SAVEPOINT)
    
    loop Для каждой операции
        Batch->>SMan: process_sync_command({<br/>  table: "Tools",<br/>  operation: "insert",<br/>  data: {...}<br/>}, sync_context=True)
        
        SMan->>SMan: _handle_insert(crud, table, data, rec_id, sync_context=True)
        
        Note over SMan: sync_context=True:<br/>НЕ инкрементируем count,<br/>устанавливаем точное значение
        
        SMan->>SMan: crud.add(sync_context=True, **clean_data)
        
        Note over SMan: sync_context передается в CRUD,<br/>@sync_aware НЕ генерирует команду
        
        SMan-->>Batch: {id: 42}
        
        Batch->>Batch: results.append({<br/>  command_id: uuid,<br/>  success: True,<br/>  new_id: 42<br/>})
    end
    
    Batch->>Batch: session.commit() (SAVEPOINT)
    
    Batch-->>SProc: results
    
    SProc->>SProc: _update_command_statuses(results)
    
    loop Для каждого результата
        SProc->>SProc: status_crud.add_status(cmd_id, "COMPLETED")
    end
    
    SProc-->>Server: [{id: uuid, status: "COMPLETED"}]
    
    Server->>Server: JSON serialize
    Server->>Server: AES encrypt
    
    Server-->>TServ: HTTP 200
    
    TServ->>TServ: AES decrypt
    TServ->>TServ: Parse JSON
    
    TServ-->>Sender: {statuses: [{id: uuid, status: "COMPLETED"}]}
    
    Sender->>CmdQueue: mark_as_done(uuid)
    
    CmdQueue->>CmdQueue: Обновление status: "done"
    CmdQueue->>CmdQueue: _save_queue()
    
    Note over Sender: Команда успешно синхронизирована
```

---

## Pull - получение удаленных изменений

### Сценарий: Сервер изменяет ячейку, клиент получает обновление

```mermaid
sequenceDiagram
    participant Admin as Admin (Server)
    participant SApp as Server App
    participant SCRUD as Server CellCRUD
    participant SDec as @sync_aware
    participant SCmdQ as Server CommandQueue
    participant Sched as Client APScheduler
    participant Receiver as Client CommandReceiver
    participant Trans as Client TransportService
    participant Server as Server API
    participant SProc as Server SyncProcessor
    participant CmdCRUD as CommandCRUD
    participant RecCRUD as RecordCRUD
    participant Mapper as DataMapper
    participant CTrans as DataTransformer
    participant CProc as Client SyncProcessor
    participant CBatch as Client BatchProcessor
    participant CSMan as Client SyncManager

    Admin->>SApp: update_cell(id=10, tools_id=42)
    SApp->>SCRUD: update(id=10, tools_id=42)
    
    Note over SCRUD: @sync_aware на сервере
    
    SCRUD->>SDec: wrapper(self, id=10, tools_id=42)
    SDec->>SDec: Выполнение CRUD операции
    SDec->>SCRUD: update(id=10, tools_id=42)
    SCRUD-->>SDec: Cell(id=10, tools_id=42)
    
    SDec->>SCmdQ: add_command(<br/>  table="Cell",<br/>  operation="update",<br/>  data={index: 10, tools_id: 42}<br/>)
    
    SCmdQ->>SCmdQ: Сохранение команды в БД<br/>(pending для всех устройств)
    
    Note over Sched: job_fetch на клиенте<br/>запускается каждые 120 секунд
    
    Sched->>Receiver: fetch_and_apply()
    
    Receiver->>Receiver: _ensure_handshake()
    Note over Receiver: Handshake выполнен
    
    Receiver->>Receiver: Чтение last_synced<br/>из файла last_synced.txt
    Receiver->>Receiver: Формирование params:<br/>{<br/>  device: 1,<br/>  since: "2024-01-15T10:00:00Z",<br/>  schema_hash: "abc..."<br/>}
    
    Receiver->>Trans: send_pull("/sync/pull", params)
    
    Trans->>Trans: Формирование URL с query params
    Trans->>Trans: Добавление заголовков<br/>(Authorization, X-Signature)
    
    Trans->>Server: GET /sync/pull?device=1&since=...&schema_hash=...
    
    Server->>Server: Verify HMAC (если есть)
    Server->>SProc: prepare_pull(device=1, since="...", schema_hash="...")
    
    SProc->>SProc: _get_mapping(schema_hash)
    
    Note over SProc: Получение mapping из кэша
    
    SProc->>CmdCRUD: get_pending_for_device(device=1)
    
    Note over CmdCRUD: SELECT * FROM Command<br/>WHERE target_device_id=1<br/>  AND status='pending'<br/>  AND created_at > since
    
    CmdCRUD-->>SProc: [Command(id=15, table="Cell", operation="UPDATE", ...)]
    
    SProc->>RecCRUD: get_bulk_records([15])
    
    Note over RecCRUD: SELECT * FROM Record<br/>WHERE command_id IN (15)
    
    RecCRUD-->>SProc: {15: {index: 10, tools_id: 42, ...}}
    
    loop Для каждой команды
        SProc->>Mapper: map_outgoing("Cell", raw_data)
        
        Note over Mapper: Применяет mapping:<br/>{index: 10} → {id: 10}<br/>(если нужно)
        
        Mapper-->>SProc: json_data
        
        SProc->>CTrans: postprocess("Cell", json_data)
        CTrans-->>SProc: post_data
        
        SProc->>RecCRUD: get_last_for_command(15)
        RecCRUD-->>SProc: Record(last_modified="2024-01-15T10:25:00Z")
        
        SProc->>SProc: commands.append({<br/>  id: "15",<br/>  table: "Cell",<br/>  operation: "UPDATE",<br/>  data: post_data,<br/>  last_modified: "2024-01-15T10:25:00Z"<br/>})
    end
    
    SProc->>SProc: Формирование ответа:<br/>{<br/>  schema_hash: "abc...",<br/>  commands: [...]<br/>}
    
    SProc->>SProc: JSONSchemaValidator.validate(response, "pull_response")
    
    SProc-->>Server: {schema_hash, commands}
    
    Server->>Server: JSON serialize
    Server->>Server: AES encrypt
    Server->>Server: HMAC sign
    
    Server-->>Trans: HTTP 200<br/>Body: encrypted response
    
    Trans->>Trans: Verify HMAC
    Trans->>Trans: AES decrypt
    Trans->>Trans: Parse JSON
    
    Trans-->>Receiver: {schema_hash: "...", commands: [...]}
    
    Receiver->>Receiver: new_last = last_synced
    
    loop Для каждой команды
        Receiver->>CProc: process_push(<br/>  device=1,<br/>  commands=[cmd],<br/>  schema_hash<br/>)
        
        Note over CProc: Применяет команду<br/>как push от сервера
        
        CProc->>CProc: JSONSchemaValidator.validate(commands)
        CProc->>CProc: Фильтрация дубликатов
        CProc->>CProc: _process_single(cmd, mapping)
        
        CProc->>CBatch: execute_batch([operation])
        
        CBatch->>CSMan: process_sync_command({<br/>  table: "Cell",<br/>  operation: "update",<br/>  data: {index: 10, tools_id: 42}<br/>}, sync_context=True)
        
        CSMan->>CSMan: _handle_update(crud, data, rec_id=10)
        
        Note over CSMan: sync_context=True:<br/>@sync_aware НЕ генерирует команду
        
        CSMan->>CSMan: crud.update(index=10, sync_context=True, tools_id=42)
        
        CSMan-->>CBatch: Cell(id=10, tools_id=42)
        
        CBatch-->>CProc: [{command_id: "15", success: True}]
        
        CProc-->>Receiver: Команда применена
        
        Receiver->>Receiver: if cmd.last_modified > new_last:<br/>  new_last = cmd.last_modified
    end
    
    Receiver->>Receiver: if new_last != last_synced:<br/>  _save_last_synced(new_last)
    
    Note over Receiver: Обновление границы:<br/>last_synced.txt = "2024-01-15T10:25:00Z"
```

---

## Обработка ошибок и повторы

### Сценарий: Сетевая ошибка при отправке команды

```mermaid
sequenceDiagram
    participant Sched as APScheduler
    participant Sender as CommandSender
    participant CmdQ as CommandQueue
    participant Trans as TransportService
    participant Server as Server
    participant Retry as RetryManager

    Note over Sched: job_send срабатывает

    Sched->>Sender: send_pending()
    
    Sender->>Sender: _ensure_handshake()
    Sender->>CmdQ: get_pending_commands()
    CmdQ-->>Sender: [cmd1, cmd2, cmd3]
    
    Sender->>Sender: Подготовка payload
    Sender->>Trans: send_push(endpoint, payload)
    
    Trans->>Trans: AES encrypt
    Trans->>Trans: HMAC sign
    
    Trans->>Server: POST /sync/push
    
    Note over Server: Сервер недоступен<br/>или таймаут
    
    Server--xTrans: ConnectionError / Timeout
    
    Trans--xSender: Exception: Connection failed
    
    Note over Sender: Обработка ошибки
    
    loop Для каждой pending команды
        Sender->>CmdQ: mark_as_retrying(cmd.id)
        
        CmdQ->>CmdQ: Обновление статуса: "retrying"
        CmdQ->>CmdQ: _save_queue()
    end
    
    Sender-->>Sched: Exception propagated
    
    Note over Sched: job_send завершается с ошибкой<br/>Следующая попытка через 60 сек

    Note over Sched: job_process_retrying<br/>срабатывает (30 сек)

    Sched->>Retry: retry_all_retrying()
    
    Retry->>CmdQ: get_retrying_commands()
    CmdQ-->>Retry: [cmd1, cmd2, cmd3]
    
    loop Для каждой команды
        Retry->>Retry: Проверка retry_count
        
        Note over Retry: retry_count = 0<br/>(первая попытка)
        
        Retry->>CmdQ: get_last_retry_timestamp(cmd.id)
        CmdQ-->>Retry: None (еще не пытались)
        
        Retry->>CmdQ: update_last_retry_timestamp(cmd.id, now)
        
        Retry->>Retry: _retry_one(cmd)
        
        Retry->>Sender: send_single_command(cmd)
        
        Sender->>Sender: Обогащение данных
        Sender->>Trans: send_push(endpoint, {commands: [cmd]})
        
        Trans->>Server: POST /sync/push
        
        alt Сервер доступен
            Server-->>Trans: HTTP 200
            Trans-->>Sender: Success
            Sender-->>Retry: Success
            
            Retry->>CmdQ: mark_as_done(cmd.id)
            
            CmdQ->>CmdQ: Обновление статуса: "done"
            CmdQ->>CmdQ: _save_queue()
            
            Note over Retry: Команда успешно отправлена
            
        else Сервер недоступен
            Server--xTrans: ConnectionError
            Trans--xSender: Exception
            Sender--xRetry: Exception
            
            Retry->>CmdQ: update_last_retry_timestamp(cmd.id, now)
            Retry->>Retry: schedule_retry(cmd)
            
            Retry->>CmdQ: add_retry_count(cmd.id)
            
            CmdQ->>CmdQ: retry_count = 1
            CmdQ->>CmdQ: _save_queue()
            
            Note over Retry: Команда остается в "retrying"<br/>Следующая попытка через 30 сек
        end
    end
```

### Сценарий: Превышение max_retries

```mermaid
sequenceDiagram
    participant Sched as APScheduler
    participant Retry as RetryManager
    participant CmdQ as CommandQueue
    participant Logger as DiagnosticLogger

    Note over Sched: job_process_retrying<br/>срабатывает каждые 30 сек

    loop 4320 раз (36 часов)
        Sched->>Retry: retry_all_retrying()
        
        Retry->>CmdQ: get_retrying_commands()
        CmdQ-->>Retry: [cmd1]
        
        Retry->>CmdQ: get_retry_count(cmd1.id)
        CmdQ-->>Retry: retry_count = 4319
        
        Note over Retry: retry_count < max_retries (4320)<br/>Продолжаем попытки
        
        Retry->>CmdQ: get_last_retry_timestamp(cmd1.id)
        CmdQ-->>Retry: "2024-01-15T10:24:30Z"
        
        Retry->>Retry: Проверка времени:<br/>now - last_retry_timestamp >= 30 сек?
        
        alt Прошло >= 30 сек
            Retry->>CmdQ: update_last_retry_timestamp(cmd1.id, now)
            Retry->>Retry: _retry_one(cmd1)
            
            Note over Retry: Попытка отправки...
            Note over Retry: Неудача
            
            Retry->>CmdQ: add_retry_count(cmd1.id)
            CmdQ->>CmdQ: retry_count = 4320
            
        else Еще не прошло 30 сек
            Note over Retry: Пропускаем эту итерацию
        end
    end

    Note over Sched: Следующая итерация

    Sched->>Retry: retry_all_retrying()
    Retry->>CmdQ: get_retrying_commands()
    CmdQ-->>Retry: [cmd1]
    
    Retry->>CmdQ: get_retry_count(cmd1.id)
    CmdQ-->>Retry: retry_count = 4320
    
    Retry->>Retry: if retry_count >= max_retries
    
    Note over Retry: Превышен лимит попыток
    
    Retry->>Logger: log_warning(<br/>  "Max retries exceeded",<br/>  {id: cmd1.id, retry_count: 4320}<br/>)
    
    Retry->>CmdQ: mark_as_failed(cmd1.id)
    
    CmdQ->>CmdQ: Обновление статуса: "failed"
    CmdQ->>CmdQ: _save_queue()
    
    Note over Retry: Команда помечена как "failed"<br/>Требуется ручное вмешательство
```

---

## Полный цикл двусторонней синхронизации

### Сценарий: Одновременные изменения на клиенте и сервере

```mermaid
sequenceDiagram
    participant CUser as Client User
    participant CApp as Client App
    participant CCmdQ as Client CommandQueue
    participant CSender as Client CommandSender
    participant SUser as Server User
    participant SApp as Server App
    participant SCmdQ as Server CommandQueue
    participant Server as Server API
    participant CReceiver as Client CommandReceiver

    Note over CUser,CReceiver: T=0: Начальное состояние<br/>Tools(id=42): count=10

    par Client добавляет 5 инструментов
        CUser->>CApp: use_tool(id=42, count=5)
        CApp->>CApp: @sync_aware add(id=42, count=5)
        
        Note over CApp: Локально:<br/>Tools(id=42).count += 5<br/>→ count = 15
        
        CApp->>CCmdQ: add_command(<br/>  table="Tools",<br/>  operation="insert",<br/>  data={index: 42, count: 5}<br/>)
        
        Note over CCmdQ: Команда в pending<br/>Будет отправлена через 60 сек
        
    and Server добавляет 3 инструмента
        SUser->>SApp: add_tools(id=42, count=3)
        SApp->>SApp: @sync_aware add(id=42, count=3)
        
        Note over SApp: Локально на сервере:<br/>Tools(id=42).count += 3<br/>→ count = 13
        
        SApp->>SCmdQ: add_command(<br/>  table="Tools",<br/>  operation="insert",<br/>  data={index: 42, count: 3}<br/>)
        
        Note over SCmdQ: Команда в pending<br/>для всех устройств
    end

    Note over CUser,CReceiver: T=60: Client отправляет свои изменения

    CSender->>CCmdQ: get_pending_commands()
    CCmdQ-->>CSender: [{table: "Tools", operation: "insert", data: {index: 42, count: 5}}]
    
    CSender->>Server: POST /sync/push<br/>{commands: [<br/>  {table: "Tools", operation: "INSERT", data: {index: 42, count: 5}}<br/>]}
    
    Note over Server: Получена команда от клиента:<br/>count = 5
    
    Server->>Server: process_push()
    
    Server->>Server: _handle_insert(table="Tools", data={index: 42, count: 5})
    
    Note over Server: Проверка: запись 42 существует<br/>Режим: sync_context = True<br/>→ НЕ инкрементируем, устанавливаем точное значение
    
    Server->>Server: UPSERT:<br/>Tools(id=42).count = 5
    
    Note over Server: Конфликт!<br/>Сервер имел count=13<br/>Клиент перезаписал count=5
    
    Server-->>CSender: {status: "COMPLETED"}
    
    CSender->>CCmdQ: mark_as_done(cmd.id)

    Note over CUser,CReceiver: T=120: Client запрашивает изменения с сервера

    CReceiver->>Server: GET /sync/pull?device=1&since=...
    
    Server->>SCmdQ: get_pending_for_device(device=1)
    SCmdQ-->>Server: [{table: "Tools", operation: "insert", data: {index: 42, count: 3}}]
    
    Server-->>CReceiver: {commands: [<br/>  {table: "Tools", operation: "INSERT", data: {index: 42, count: 3}}<br/>]}
    
    CReceiver->>CReceiver: process_push([cmd])
    
    CReceiver->>CReceiver: _handle_insert(table="Tools", data={index: 42, count: 3})
    
    Note over CReceiver: Проверка: запись 42 существует<br/>Режим: sync_context = True<br/>→ НЕ инкрементируем, устанавливаем точное значение
    
    CReceiver->>CReceiver: UPSERT:<br/>Tools(id=42).count = 3
    
    Note over CReceiver: Итоговое состояние:<br/>Client: Tools(id=42).count = 3<br/>Server: Tools(id=42).count = 5

    Note over CUser,CReceiver: Конфликт: разные значения на клиенте и сервере<br/>Причина: одновременные изменения + last-write-wins стратегия<br/>Решение: использовать инкрементальные операции или conflict resolution
```

### Правильный сценарий с инкрементальными операциями

```mermaid
sequenceDiagram
    participant CUser as Client User
    participant CApp as Client App
    participant SUser as Server User
    participant SApp as Server App

    Note over CUser,SApp: T=0: Начальное состояние<br/>Tools(id=42): count=10

    par Client добавляет 5 инструментов
        CUser->>CApp: use_tool(id=42, count=5)
        CApp->>CApp: @sync_aware add(id=42, count=5)
        
        Note over CApp: Локально:<br/>Tools(id=42).count += 5<br/>→ count = 15
        
        Note over CApp: Команда:<br/>{operation: "increment", delta: +5}
        
    and Server добавляет 3 инструмента
        SUser->>SApp: add_tools(id=42, count=3)
        SApp->>SApp: @sync_aware add(id=42, count=3)
        
        Note over SApp: Локально:<br/>Tools(id=42).count += 3<br/>→ count = 13
        
        Note over SApp: Команда:<br/>{operation: "increment", delta: +3}
    end

    Note over CUser,SApp: После синхронизации:<br/>Client: count = 10 + 5 + 3 = 18<br/>Server: count = 10 + 3 + 5 = 18<br/>✅ Корректный результат
```

---

## Диаграмма компонентов и их взаимодействия

```
┌─────────────────────────────────────────────────────────────────┐
│                       Application Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  User Interaction → CRUD Operations → @sync_aware Decorator     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Capture Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  • Дедупликация операций (_state cache)                         │
│  • Валидация данных (DataTransformer)                           │
│  • Генерация команд (INBOUND_QUEUE)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Queue Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  • CommandQueue (JSON persistence)                              │
│  • Статусы: pending → retrying → done / failed                  │
│  • Retry tracking (retry_count, last_retry_timestamp)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Scheduling Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  APScheduler Jobs:                                               │
│  • job_send (60s) → CommandSender.send_pending()                │
│  • job_fetch (120s) → CommandReceiver.fetch_and_apply()         │
│  • job_process_retrying (30s) → RetryManager.retry_all()        │
└──────────────┬─────────────────────────────┬────────────────────┘
               │                             │
               ▼                             ▼
┌──────────────────────────┐   ┌────────────────────────────────┐
│   Push Process (PUSH)    │   │   Pull Process (PULL)          │
├──────────────────────────┤   ├────────────────────────────────┤
│ CommandSender            │   │ CommandReceiver                │
│   ↓                      │   │   ↓                            │
│ DataTransformer          │   │ TransportService               │
│   (enrich)               │   │   ↓                            │
│   ↓                      │   │ Server API                     │
│ TransportService         │   │   ↓                            │
│   (encrypt + sign)       │   │ SyncProcessor.prepare_pull()   │
│   ↓                      │   │   ↓                            │
│ Server API               │   │ DataMapper + DataTransformer   │
│   ↓                      │   │   ↓                            │
│ SyncProcessor            │   │ TransportService               │
│   .process_push()        │   │   (decrypt + verify)           │
│   ↓                      │   │   ↓                            │
│ 🆕 CommandOrderer        │   │ CommandReceiver                │
│   (optimize + order)     │   │   ↓                            │
│   ↓                      │   │ SyncProcessor.process_push()   │
│ BatchProcessor           │   │   ↓                            │
│   ↓                      │   │ 🆕 CommandOrderer              │
│ SyncManager → Database   │   │   (optimize + order)           │
└──────────────────────────┘   │   ↓                            │
                               │ BatchProcessor                 │
                               │   ↓                            │
                               │ SyncManager → Database         │
                               └────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   🆕 Optimization Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  CommandOrderer (интеллектуальная обработка):                   │
│    • Группировка по (table, record_id)                          │
│    • Сжатие последовательностей: ADD+DELETE → DELETE            │
│    • Валидация корректности операций                            │
│    • Топологическая сортировка по FK                            │
│    • Результат: сокращение команд на 30-80%                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Core Processing Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  SyncProcessor (координация):                                   │
│    • Handshake (SchemaCache + SchemaAnalyzer)                   │
│    • Push processing (валидация, трансформация, конфликты)     │
│    • Pull preparation (команды из БД)                           │
│    • 🆕 Оптимизация через CommandOrderer                        │
│                                                                  │
│  BatchProcessor (транзакции):                                   │
│    • Атомарная обработка операций                               │
│    • Автосвязывание (Consumption ↔ History)                     │
│                                                                  │
│  SyncManager (CRUD-фасад):                                      │
│    • process_command → _handle_insert/update/delete             │
│    • UPSERT логика                                              │
│    • Специальная обработка (count increment, автосвязи)         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       Support Components                         │
├─────────────────────────────────────────────────────────────────┤
│  • DataMapper: маппинг полей между схемами                      │
│  • DataTransformer: бизнес-правила (enrich, validate)           │
│  • ConflictManager: обнаружение и разрешение конфликтов         │
│  • RetryManager: планирование повторов                          │
│  • 🆕 CommandOrderer: оптимизация и упорядочивание команд       │
│  • DiagnosticLogger: централизованное логирование               │
│  • SyncMonitor: метрики (success/failure counts, duration)      │
│  • JSONSchemaValidator: валидация по JSON Schema                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Заключение

Эти диаграммы последовательностей иллюстрируют:

1. **Handshake** - процесс согласования схем между клиентом и сервером с кэшированием
2. **Push** - полный цикл отправки локальных изменений на сервер с оптимизацией 🆕
3. **Pull** - получение удаленных изменений с сервера
4. **Retry** - обработка ошибок с автоматическими повторами
5. **Bidirectional** - двустороннюю синхронизацию с обработкой конфликтов
6. **Optimization** - интеллектуальная оптимизация команд (сжатие 30-80%) 🆕

Система обеспечивает надежную доставку команд, автоматическое разрешение конфликтов, интеллектуальную оптимизацию и безопасность данных через шифрование и подпись.

