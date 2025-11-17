# Процесс синхронизации баз данных между сервером и клиентом

## Обзор
Процесс синхронизации представляет собой двунаправленную (bidirectional) синхронизацию на основе журнала изменений (changelog-based synchronization) между серверной БД и клиентскими устройствами. Система обеспечивает eventual consistency с обработкой конфликтов, повторными попытками и безопасной передачей данных.

## Архитектура
- **Модель данных**: Используется отдельная SQLite-база `sync.db` для хранения состояний синхронизации.
- **Компоненты**: Наследование от паттернов Command Pattern, Observer, Scheduler.
- **Безопасность**: AES-256 шифрование, HMAC-подпись, JWT-аутентификация.
- **Платформа**: Python, SQLAlchemy, APScheduler, FastAPI (для сервера).

## Файлы и структура проекта
### Серверные файлы
- `server/dbSync/sync_db.py`: Инициализация sync БД на сервере.
- `server/dbSync/Runner.py`: Аналогичен клиентскому, но для серверной стороны.
- Аналогичная структура `server/dbSync/engines/`, `Logic_v2/` и т.д.

### Клиентские файлы
- `client/dbSync/sync_db.py`: Инициализация sync БД на клиенте.
- `client/dbSync/Runner.py`: Главный оркестратор синхронизации.
- `client/dbSync/Model/base.py`: Базовая модель SQLAlchemy.
- `client/dbSync/Model/Command.py`: Модель команд синхронизации.
- `client/dbSync/Model/Record.py`: Модель данных записей.
- `client/dbSync/Model/CommandStatus.py`: Модель статусов команд.
- `client/dbSync/Model/SyncConfig.py`: Конфигурация включенных таблиц.
- `client/dbSync/setup.py`: Функции инициализации компонентов.
- `client/dbSync/constants.py`: Перечисления констант (CommandStatusEnum).
- `client/dbSync/Logic_v2/`:
  - `SyncProcessor.py`: Центральный процессор операций.
  - `CommandSender.py`: Компонент push-процесса.
  - `CommandReceiver.py`: Компонент pull-процесса.
  - `TransportService.py`: Сервис HTTP-транспорта с шифрованием.
  - `SchemaCache.py`: Кэш маппингов схем.
  - `SchemaAnalyzer.py`: Анализатор схем БД.
  - `DataMapper.py`: Маппинг полей между схемами.
  - `DataTransformer.py`: Трансформация данных.
  - `ConflictManager.py`: Обнаружение и разрешение конфликтов.
  - `BatchProcessor.py`: Пакетное выполнение операций.
  - `RetryManager.py`: Управление повторными попытками.
  - `SyncMonitor.py`: Мониторинг операций.
  - `JSONSchemaValidator.py`: Валидация JSON-схем.
  - `DiagnosticLogger.py`: Детальное логирование.
  - `SyncManager.py`: Управление синхронизацией.
  - `CommandQueue.py`: Очередь локальных команд.

### Engines
- `client/dbSync/Engines/CommandEngine.py`: CRUD-операции для commands.
- `client/dbSync/Engines/RecordEngine.py`: CRUD для records.
- `client/dbSync/Engines/CommandStatusEngine.py`: CRUD для статусов.
- `client/dbSync/Engines/SyncConfigEngine.py`: CRUD для конфигурации.
- `client/dbSync/Engines/CommandSnapshotEngine.py`: CRUD для snapshots (rollback).
- `client/dbSync/Engines/BatchExecutionEngine.py`: CRUD для batch executions.
- `client/dbSync/Engines/IdempotencyTokenEngine.py`: CRUD для idempotency tokens.

## Модели данных

### Sync.db Структура
SQLite-база с WAL-режимом, NullPool, check_same_thread=False для многопоточности.

#### Таблица `Command`
- `id` (INTEGER, PRIMARY KEY): Уникальный ID команды.
- `table_name` (STRING): Имя целевой таблицы.
- `operation` (STRING): CREATE, UPDATE, DELETE (ограничено CHECK).
- `record_id` (INTEGER): ID затрагиваемой записи.
- `created_at` (DATE, server_default=NOW()): Время создания.
- `device_number` (INTEGER): ID устройства.

#### Таблица `Record`
- `id` (INTEGER, PRIMARY KEY)
- `command_id` (INTEGER, FOREIGN KEY → Command.id, CASCADE DELETE)
- `data_json` (TEXT): Сериализованные данные в JSON
- `last_modified` (DATE, DEFAULT NOW, UPDATE NOW)

#### Таблица `CommandStatus`
- `id` (INTEGER, PRIMARY KEY)
- `command_id` (INTEGER, FOREIGN KEY → Command.id, CASCADE DELETE)
- `status` (STRING): PENDING, IN_PROGRESS, COMPLETED, FAILED
- `updated_at` (DATE, DEFAULT NOW, UPDATE)

#### Таблица `SyncConfig`
- `table_name` (STRING, PRIMARY KEY)
- `enabled` (BOOLEAN, DEFAULT TRUE)

#### Таблица `CommandSnapshot` (Новое: для rollback/compensation)
- `id` (INTEGER, PRIMARY KEY): Уникальный ID снимка.
- `command_id` (INTEGER, FOREIGN KEY → Command.id): ID команды.
- `table_name` (STRING): Имя таблицы.
- `record_id` (INTEGER): ID записи, которая изменяется.
- `snapshot_data` (TEXT): JSON-снимок состояния ДО выполнения операции.
- `operation` (STRING): Тип операции (insert, update, delete).
- `created_at` (TIMESTAMP): Время создания снимка.

**Назначение**: Хранит состояние записей ПЕРЕД их изменением для возможности компенсации (rollback) при сбое пакетной операции.

#### Таблица `BatchExecution` (Новое: для отслеживания пакетов)
- `id` (INTEGER, PRIMARY KEY): Уникальный ID выполнения пакета.
- `batch_id` (STRING, UNIQUE): Уникальный идентификатор пакета.
- `status` (STRING): Статус (PENDING, IN_PROGRESS, COMPLETED, FAILED, ROLLED_BACK).
- `total_commands` (INTEGER): Общее количество команд в пакете.
- `successful_commands` (INTEGER): Количество успешно выполненных команд.
- `failed_commands` (INTEGER): Количество неудачных команд.
- `started_at` (TIMESTAMP): Время начала выполнения.
- `completed_at` (TIMESTAMP): Время завершения.
- `error_message` (TEXT): Сообщение об ошибке при сбое.

**Назначение**: Отслеживает метаданные выполнения пакетов команд синхронизации.

#### Таблица `IdempotencyToken` (Новое: для предотвращения дубликатов)
- `id` (INTEGER, PRIMARY KEY): Уникальный ID токена.
- `token` (STRING, UNIQUE): Уникальный токен идемпотентности.
- `batch_id` (STRING): ID связанного пакета.
- `status` (STRING): Статус обработки токена.
- `created_at` (TIMESTAMP): Время создания токена.
- `expires_at` (TIMESTAMP): Время истечения токена (обычно +24 часа).

**Назначение**: Предотвращает повторное выполнение одного и того же пакета команд (duplicate prevention).

## Ключевые функции и классы

### Инициализация
- `init_sync_db(force_recreate=False)` in `sync_db.py`: Создает/пересоздает sync.db с таблицами.
- `get_sync_session()` in `sync_db.py`: Фабрика сессий для sync.db.
- `start_sync(device_id, ...)` in `Runner.py`: Запуск синхронизации для устройства.
- `create_sync_components(device_id, ...)` in `Runner.py`: Инициализация всех компонентов.

### Handshake
- `SyncProcessor.process_schema(src_schema, client_schema_hash)`: Согласует схему клиента и сервера.
- `SchemaAnalyzer.generate_mapping(client_schema, server_schema)`: Генерирует маппинг полей.
- `SchemaCache.get/set(hash)`: Кэширует маппинги по хэшу.

### Push (Отправка изменений)
- `CommandSender.send_pending()`: Берёт pending из очереди, отправляет batch.
- `TransportService.send_push(endpoint, payload)`: HTTP POST с AES+HASH.
- `SyncProcessor.process_push(device, commands, schema_hash)`: Применяет команды на получателе.
- `ConflictManager.detect_data_conflict(existing, local)`: Обнаружение конфликтов.
- `BatchProcessor.execute_batch(ops)`: Атомарное выполнение в БД.

### Pull (Получение изменений)
- `CommandReceiver.fetch_and_apply()`: Запрашивает и применяет новые команды.
- `CommandReceiver._load_last_synced()`: Читает timestamp из `last_synced.txt`.
- `SyncProcessor.prepare_pull(device, since, schema_hash)`: Подготавливает команд для клиента.
- `SyncProcessor._process_single(cmd, mapping)`: Обрабатывает одну команду.

### Управление конфликтами
- `ConflictManager.detect_structure_conflict(client_fields, server_fields)`: Структурные конфликты.
- `ConflictManager.apply_data_strategy(existing, local)`: Разрешение merge/override.
- `MergeFieldsStrategy.merge(existing, local, field)`: Стратегия объединения.

### Transport
- `TransportService._encrypt(plaintext)`: AES-CBC с padding.
- `TransportService._decrypt(ciphertext)`: Расшифровка.
- `TransportService._sign_hmac(payload)`: HMAC-SHA256 подпись.

### Очереди и планировка
- `CommandQueue.add_command(table, operation, data)`: Добавление локальной команды.
- `CommandQueue.get_pending_commands()`: Получение ожидающих.
- `CommandQueue.mark_as_done/failed(id)`: Обновление статуса.
- `RetryManager.schedule_retry(command, delay)`: Планировка retry.
- APScheduler job_send/job_fetch каждые sender_timeout/receiver_timeout.

### Rollback и Compensation (Новое)
- `SnapshotManager.capture_snapshot(command_id, table, record_id, operation)`: Захват состояния записи ДО выполнения команды.
- `SnapshotManager.generate_compensation_for_command(command_id)`: Генерация обратной операции из снимка.
- `SnapshotManager.cleanup_old_snapshots(older_than_days)`: Автоматическая очистка старых снимков.
- `IdempotencyManager.generate_token()`: Генерация уникального токена для пакета.
- `IdempotencyManager.is_duplicate(token)`: Проверка, не был ли пакет уже обработан.
- `IdempotencyManager.mark_completed(token, batch_id)`: Отметка токена как успешно обработанного.
- `BatchProcessor.execute_batch(operations)`: Атомарное выполнение пакета команд с ALL_OR_NOTHING стратегией.

## Поэтапный процесс синхронизации

### Этап 1: Инициализация
1. Вызов `start_sync(device_id, host, port, token, secret, aes, sender_timeout, receiver_timeout)`.
2. Создание компонентов через `create_sync_components()`.
3. Запуск APScheduler с jobs: `job_send` (push каждые sender_timeout), `job_fetch` (pull каждые receiver_timeout).
4. Компоненты: SyncProcessor, CommandSender, CommandReceiver, TransportService, CRUD-engines, etc.

### Этап 2: Handshake
1. `CommandSender._ensure_handshake()` или аналоги.
2. Клиент: `SyncManager.get_local_schema()` → локальная схема.
3. `TransportService.send_schema("/sync/handshake", schema, device=device_id)`: POST с шифрованием.
4. Сервер: `SyncProcessor.process_schema(schema, hash)` → `SchemaAnalyzer.generate_mapping()` → кэш.
5. Возврат `mapping` и `schema_hash`.
6. Клиент: `SyncProcessor.update_schema(mapping, hash)` → `DataMapper.update_field_mappings()`.

### Этап 3: Push-процесс (клиент → сервер)
1. `job_send` → `CommandSender.send_pending()`.
2. `CommandQueue.get_pending_commands()` → список команд.
3. Формирование payload: `{"device": id, "schema_hash": hash, "commands": list}`.
4. `TransportService.send_push("/sync/push", payload)`: POST с AES+HASH.
5. Сервер принимает, дешифрует, валидирует.
6. `SyncProcessor.process_push(device, commands, hash)`:
   - `json_validator.validate(commands, "push_commands")`.
   - Фильтрация дубликатов.
   - Для каждой команды: `data_transformer.preprocess/clean/validate`.
   - `conflict_manager.detect_structure_conflict` → `mapping_config.on_conflict`.
   - `data_mapper.map_incoming` на серверную схему.
   - `conflict_manager.detect_data_conflict` → стратегия (например, MergeFieldsStrategy).
   - `batch_processor.execute_batch([{cmd, table, data, operation}])` → SQL в work.db.
   - Обновление статусов в sync.db: `CommandStatusCRUD.add_status()`.
7. Возврат статусов команд.
8. Клиент: `mark_as_done/failed`.
9. При ошибках: `retry_manager.schedule_retry`.

### Этап 4: Pull-процесс (сервер → клиент)
1. `job_fetch` → `CommandReceiver.fetch_and_apply()`.
2. Чтение `last_synced` из `last_synced.txt`.
3. `TransportService.send_pull("/sync/pull", params={"device":id, "since": since, "schema_hash":hash})`: GET.
4. Сервер: `SyncProcessor.prepare_pull(device, since, hash)`:
   - Запрос из sync.db: `CommandCRUD.get_pending_for_device(device)`.
   - Join с `RecordCRUD.get_bulk_records()`.
   - Для каждой: `data_mapper.map_outgoing` → `data_transformer.postprocess`.
   - Сбор `{id, table, operation, data, last_modified}`.
5. Возврат `{schema_hash, commands}`.
6. Клиент получает, для каждой команды: `SyncProcessor.process_push(device, [cmd], hash)` (локально применяется тот же процесс).
   - В работе БД клиента: создание/обновление записей.
7. Обновление `last_synced = max(last_modified)`, запись в файл.

### Этап 5: Локальная обработка
- Местные изменения: Декораторы → `SyncProcessor.enqueue_local_command(cmd)` → `CommandQueue.add_command()`.
- Ожидают в pending для следующего push.

### Этап 6: Мониторинг и ошибки
- `SyncMonitor.record_success/failure(duration)`.
- `DiagnosticLogger.log_info/error/context`.
- `ConflictManager`: стратегии: ServerWins, ClientWins, MergeFields.
- Retry: экспоненциальный backoff в `RetryManager`.
- При network errors: повтор в APScheduler.

## Базы данных
- **Sync.db**: Локальная на клиенте/сервере, хранение команд, записей, статусов.
- **Work.db**: Основная БД приложения (клиентская, серверная), куда применяются изменения.
- WAL-режим: `PRAGMA journal_mode=WAL`.
- Многопоточность: NullPool, no check_same_thread.

## Безопасность
- **Шифрование**: AES-256-CBC с подкреплением в send_push/schema/pull, дешифровка в receive.
- **Подпись**: HMAC-SHA256 в заголовке X-Signature.
- **Аутентификация**: JWT в Authorization header.
- **Валидация**: JSONSchema для handshake, push_commands, push_response, pull_response.

## Rollback и Compensation: Подробное описание

### Проблема
При синхронизации пакетов команд (например, массовая загрузка инструментов) частичный сбой может оставить базу данных в несогласованном состоянии:
- Команда 1: INSERT Tool ✅ (успешно)
- Команда 2: UPDATE Cell ❌ (ошибка)
- Команда 3: UPDATE Status (не выполнялась)

**Результат**: Инструмент вставлен, но ячейка/статус не обновлены = нарушенное состояние.

### Решение: Паттерн Saga с компенсацией

Система использует **Saga Pattern** для управления распределёнными транзакциями через компенсирующие операции.

#### Фаза A: Захват снимков (ПЕРЕД выполнением)

Для каждой операции UPDATE/DELETE система создаёт снимок текущего состояния записи:

```python
# SnapshotManager.capture_snapshot()
for operation in batch:
    if operation.type in ['UPDATE', 'DELETE']:
        # Запрос текущего состояния из work.db
        current_state = work_db.query(operation.table).get(operation.record_id)
        
        # Сохранение в sync.db (переживёт rollback work.db)
        snapshot = CommandSnapshot(
            command_id=operation.id,
            table_name=operation.table,
            record_id=operation.record_id,
            snapshot_data=json.dumps(current_state),
            operation=operation.type
        )
        sync_db.add(snapshot)
```

**Важно**: Снимки сохраняются в `sync.db` (отдельная БД), которая НЕ откатывается при rollback `work.db`.

#### Фаза B: Атомарное выполнение пакета

BatchProcessor выполняет все команды в одной транзакции с savepoint:

```python
# BatchProcessor.execute_batch()
with work_db.begin_nested():  # Создаёт SAVEPOINT
    for command in batch:
        try:
            # Предварительный захват снимка
            snapshot_manager.capture_snapshot(
                command_id=command.id,
                table=command.table,
                record_id=command.record_id,
                operation=command.operation
            )
            
            # Выполнение команды
            result = sync_manager.process_sync_command(command)
            results.append({"success": True, "command_id": command.id})
            
        except Exception as e:
            # ROLLBACK всего пакета при ЛЮБОЙ ошибке
            results.append({"success": False, "error": str(e)})
            raise  # Триггерит откат транзакции
```

**Стратегия ALL_OR_NOTHING**:
- Успех всех команд → COMMIT транзакции
- Ошибка хотя бы одной → ROLLBACK всего пакета

#### Фаза C: Автоматический Database Rollback

При возникновении ошибки SQLAlchemy автоматически откатывает транзакцию:

```python
except SQLAlchemyError:
    # Автоматический ROLLBACK SAVEPOINT
    # Все изменения в work.db отменены
    # НО: снимки в sync.db остаются
    return results
```

**Что происходит**:
1. Все INSERT/UPDATE/DELETE в `work.db` отменяются
2. База данных возвращается в состояние до начала пакета
3. Снимки в `sync.db` сохраняются для аудита

#### Фаза D: Генерация компенсирующих операций (опционально)

Хотя database rollback отменяет изменения, система может генерировать компенсирующие операции для логирования или ручного восстановления:

```python
# SnapshotManager.generate_compensation_for_command()
snapshot = sync_db.query(CommandSnapshot).filter_by(command_id=cmd_id).first()

if snapshot.operation == 'insert':
    # INSERT отменяется через DELETE
    compensation = {
        'table': snapshot.table_name,
        'operation': 'delete',
        'id': snapshot.record_id
    }

elif snapshot.operation == 'update':
    # UPDATE отменяется через UPDATE с исходными значениями
    compensation = {
        'table': snapshot.table_name,
        'operation': 'update',
        'id': snapshot.record_id,
        'data': json.loads(snapshot.snapshot_data)
    }

elif snapshot.operation == 'delete':
    # DELETE отменяется через INSERT
    compensation = {
        'table': snapshot.table_name,
        'operation': 'insert',
        'data': json.loads(snapshot.snapshot_data)
    }
```

**Логика компенсации**:

| Оригинальная операция | Компенсация | Обоснование |
|----------------------|-------------|-------------|
| INSERT | DELETE | Удалить созданную запись |
| UPDATE | UPDATE (старые значения) | Восстановить предыдущее состояние |
| DELETE | INSERT (снимок) | Восстановить удалённую запись |

### Идемпотентность и предотвращение дубликатов

Для предотвращения повторного выполнения одного и того же пакета используется IdempotencyManager:

```python
# При получении пакета команд
token = request.headers.get('Idempotency-Token')

if idempotency_manager.is_duplicate(token):
    # Пакет уже был обработан, возвращаем кэшированный результат
    return cached_results

# Выполнение пакета
results = batch_processor.execute_batch(commands)

# Сохранение токена
idempotency_manager.mark_completed(token, batch_id, results)
```

**Механизм**:
1. Клиент генерирует уникальный токен перед отправкой пакета
2. Сервер проверяет токен в `IdempotencyToken` таблице
3. Если токен найден → возвращается кэшированный результат
4. Если токен новый → выполняется пакет, токен сохраняется
5. Токены истекают через 24 часа (автоматическая очистка)

### Мониторинг и отслеживание

Все пакеты отслеживаются в таблице `BatchExecution`:

```python
batch_execution = BatchExecution(
    batch_id=unique_id,
    status='IN_PROGRESS',
    total_commands=len(commands),
    started_at=datetime.now()
)

# После выполнения
batch_execution.status = 'COMPLETED' if all_success else 'FAILED'
batch_execution.successful_commands = sum(1 for r in results if r['success'])
batch_execution.failed_commands = sum(1 for r in results if not r['success'])
batch_execution.completed_at = datetime.now()
```

### Автоматическая очистка

SnapshotManager выполняет периодическую очистку старых снимков:

```python
# APScheduler job (ежедневно в 3:00 AM)
scheduler.add_job(
    func=snapshot_manager.cleanup_old_snapshots,
    trigger='cron',
    hour=3,
    minute=0,
    args=[30]  # Удалить снимки старше 30 дней
)
```

### Примеры сценариев

#### Сценарий 1: Успешное выполнение пакета
```
1. Команда A (INSERT Tool) → Снимок: NULL → Выполнено ✅
2. Команда B (UPDATE Cell) → Снимок: {"status": 3, "tool_id": null} → Выполнено ✅
3. Команда C (INSERT History) → Снимок: NULL → Выполнено ✅

Результат: COMMIT транзакции, все изменения применены
```

#### Сценарий 2: Сбой в середине пакета
```
1. Команда A (INSERT Tool) → Снимок: NULL → Выполнено ✅
2. Команда B (UPDATE Cell) → Снимок: {"status": 3, "tool_id": null} → ОШИБКА ❌
   → ROLLBACK транзакции
   → Команда A автоматически отменена
   → Снимки сохранены в sync.db для аудита
3. Команда C (не выполнялась)

Результат: База данных в исходном состоянии, все снимки сохранены
```

#### Сценарий 3: Повторная отправка пакета
```
Клиент отправляет пакет с токеном: "abc123"
Сервер проверяет IdempotencyToken:
  - Токен найден → возврат кэшированного результата (без повторного выполнения)
  - Токен не найден → выполнение пакета, сохранение токена

Результат: Дубликаты предотвращены, данные согласованы
```

## Настройка
- `sender_timeout`: Интервал push (сек).
- `receiver_timeout`: Интервал pull (сек).
- Ключи: aes_key, hmac_secret, jwt_token.
- Host/port: endpoints сервера.

Эта документация охватывает полный цикл синхронизации с ссылками на файлы, функции и базы данных.
