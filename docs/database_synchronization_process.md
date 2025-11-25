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

## Модели данных

### Sync.db Структура
SQLite-база с WAL-режимом, NullPool, check_same_thread=False для многопоточности.

#### Таблица `Command`
- `id` (INTEGER, PRIMARY KEY): Уникальный ID команды.
- `table_name` (STRING): Имя целевой таблицы.
- `operation` (STRING): insert, update, delete (lowercase).
- `record_id` (INTEGER): ID затрагиваемой записи.
- `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP): Время создания.
- `device_number` (INTEGER): ID устройства.

#### Таблица `Record`
- `id` (INTEGER, PRIMARY KEY)
- `command_id` (INTEGER, FOREIGN KEY → Command.id, CASCADE DELETE)
- `data_json` (TEXT): Сериализованные данные в JSON
- `last_modified` (DATE, DEFAULT NOW, UPDATE NOW)

#### Таблица `CommandStatus`
- `id` (INTEGER, PRIMARY KEY)
- `command_id` (INTEGER, FOREIGN KEY → Command.id, CASCADE DELETE)
- `status` (STRING): pending, in_progress, completed, failed (lowercase)
- `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

#### Таблица `SyncConfig`
- `table_name` (STRING, PRIMARY KEY)
- `enabled` (BOOLEAN, DEFAULT TRUE)

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
- `TransportService.send_push(endpoint, payload)`: HTTP POST с AES-шифрованием.
- `SyncProcessor.process_push(device, commands, schema_hash)`: Применяет команды на получателе.
- `ConflictManager.detect_data_conflict(existing, local)`: Обнаружение конфликтов.
- `BatchProcessor.execute_batch(ops)`: Атомарное выполнение в БД.
- `CommandQueue.get_pending_commands()`: Получает команды со статусом "pending" из JSON-файла.

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
- `TransportService._encrypt(plaintext)`: AES-CBC с PKCS7 padding, IV (16 байт) prepended к ciphertext.
- `TransportService._decrypt(ciphertext)`: Расшифровка AES-CBC, извлечение IV из первых 16 байт.
- `TransportService._sign_hmac(payload)`: HMAC-SHA256 подпись (если используется).
- **Transport Directory**: `dbSync/Transport/` содержит HTTP и WebSocket (опционально) реализации.

### Очереди и планировка
- `CommandQueue.add_command(table, operation, data)`: Добавление локальной команды (operation: "insert"|"update"|"delete").
- `CommandQueue.get_pending_commands()`: Получение ожидающих команд со статусом "pending".
- `CommandQueue.mark_as_done/failed(id)`: Обновление статуса команды.
- `RetryManager.schedule_retry(command, delay)`: Планировка retry с экспоненциальным backoff.
- APScheduler job_send/job_fetch каждые sender_timeout/receiver_timeout (по умолчанию 15/30 секунд).
- `INBOUND_QUEUES[device_id]`: Словарь очередей для передачи сообщений между HTTP-обработчиками и фоновыми потоками.

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
1. `job_send` (APScheduler) → `CommandSender.send_pending()` каждые `sender_timeout` секунд.
2. `CommandQueue.get_pending_commands()` → список команд со статусом "pending".
3. Формирование payload: `{"device": id, "schema_hash": hash, "commands": list}`.
4. `TransportService.send_push("/sync/push?device=<id>", payload)`: POST с AES-CBC шифрованием (IV + ciphertext).
5. Сервер принимает через `/sync/push`, дешифрует AES, валидирует через JSONSchemaValidator.
6. HTTP-обработчик кладёт сообщение в `INBOUND_QUEUES[device_id]` с типом "push" и `reply_queue`.
7. Фоновый поток Runner обрабатывает сообщение и вызывает `SyncProcessor.process_push(device, commands, hash)`:
   - `json_validator.validate(commands, "push_commands")`.
   - Фильтрация дубликатов.
   - Для каждой команды: `data_transformer.preprocess/clean/validate`.
   - `conflict_manager.detect_structure_conflict` → `mapping_config.on_conflict`.
   - `data_mapper.map_incoming` на серверную схему.
   - `conflict_manager.detect_data_conflict` → стратегия (например, MergeFieldsStrategy).
   - `batch_processor.execute_batch([{cmd, table, data, operation}])` → SQL в work.db (web_vending.db).
   - Обновление статусов в sync.db: `CommandStatusCRUD.add_status()`.
8. Результат кладётся в `reply_queue`, HTTP-обработчик возвращает статусы клиенту.
9. Клиент: `CommandQueue.mark_as_done/failed(id)`.
10. При ошибках: `retry_manager.schedule_retry` с экспоненциальным backoff.

### Этап 4: Pull-процесс (сервер → клиент)
1. `job_fetch` (APScheduler) → `CommandReceiver.fetch_and_apply()` каждые `receiver_timeout` секунд.
2. Чтение `last_synced` из `last_synced.txt` (файл в корне клиента/сервера).
3. `TransportService.send_pull("/sync/pull?device=<id>&since=<timestamp>")`: GET запрос.
4. Сервер HTTP-обработчик `/sync/pull` кладёт сообщение в `INBOUND_QUEUES[device_id]` с типом "pull".
5. Фоновый поток Runner вызывает `SyncProcessor.prepare_pull(device, since, hash)`:
   - Запрос из sync.db: `CommandCRUD.get_pending_for_device(device)`.
   - Join с `RecordCRUD.get_bulk_records()` для получения данных.
   - Для каждой команды: `data_mapper.map_outgoing` → `data_transformer.postprocess`.
   - Сбор `{id, table, operation, data, last_modified}`.
6. Результат кладётся в `reply_queue`, HTTP-обработчик возвращает `{schema_hash, commands}`.
7. Клиент получает, для каждой команды применяет локально через `SyncProcessor.process_push(device, [cmd], hash)`:
   - В работе БД клиента (vending.db): создание/обновление записей через BatchProcessor.
8. Обновление `last_synced = max(last_modified)`, запись в файл `last_synced.txt`.

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
- **Sync.db**: Локальная на клиенте/сервере (`dbSync/Model/sync.db`), хранение команд, записей, статусов.
- **Work.db**: Основная БД приложения:
  - Клиент: `DB/Data/vending.db`
  - Сервер: `DB/Data/web_vending.db`
- WAL-режим: `PRAGMA journal_mode=WAL` для конкурентного доступа.
- Многопоточность: NullPool, `check_same_thread=False` для SQLite.

## Безопасность
- **Шифрование**: AES-256-CBC с подкреплением в send_push/schema/pull, дешифровка в receive.
- **Подпись**: HMAC-SHA256 в заголовке X-Signature.
- **Аутентификация**: JWT в Authorization header.
- **Валидация**: JSONSchema для handshake, push_commands, push_response, pull_response.

## Настройка
- `sender_timeout`: Интервал push (сек, по умолчанию 15).
- `receiver_timeout`: Интервал pull (сек, по умолчанию 30).
- Ключи: aes_key (16 байт), secret (HMAC), token (JWT).
- Host/port: endpoints сервера (клиент: `config.json`, сервер: `options.py`).
- `command_queue.json`: Путь к файлу очереди команд (по умолчанию в корне клиента/сервера).

## Недавние улучшения (ноябрь 2025)
- **Фильтрация служебных полей**: `SyncManager._handle_update/_upsert_update` убирают `id`, `index`, `created_at`, `updated_at`, что устраняет ошибки вида `unexpected keyword argument` и защищает служебные timestamp’ы.
- **Upsert-поведение**: при неудачном `update()` автоматически выполняется повторная вставка/обновление, поэтому команды больше не падают с `ValueError: Update failed for record ...`.
- **Обработка History/Status**: правило `extract_status_from_history` в `DataTransformer` извлекает `Status.id` в integer `status`, а маппинги History дополнены полями `Status`, `plan_id`.
- **Согласованность схем**: `sync_fields.json` для `Consumption`, `Load`, `LoadOperations`, `PlanToolTypes` теперь содержат все обязательные колонки (`history_id`, `plan_id`, `status_id`, `tool_types_id`, `load_id`, и т.д.), поэтому NOT NULL ограничения соблюдаются.
- **Связи внутри батча**: `BatchProcessor` и `SyncManager._handle_insert()` автоматически ищут подходящий `history_id` в текущем батче или БД, что устраняет `Consumption.history_id`/`Load.history_id` ошибки.
- **BaseCRUD hardening**: метод `add()` фильтрует неизвестные колонки, а `update()` требует keyword-only `index`, предотвращая передачу лишних аргументов в CRUDы и Engine-классы.
- **Обратная связь клиенту**: `CommandSender` теперь учитывает `response["statuses"]` и помечает команды `done/failed/retrying` по реальным результатам вместо слепого `done`.
- **Mass Load UI**: drag&drop-скрипты (`createCells.js`, `drag_and_drop.js`, `deleteLoad.js`) блокируют ячейки `1/36/71/106/141/176`, запрещая добавление инструментов и массовое сохранение в недоступные позиции.

Эта документация охватывает полный цикл синхронизации с ссылками на файлы, функции и базы данных.
