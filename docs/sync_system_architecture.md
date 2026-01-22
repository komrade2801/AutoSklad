# Документация системы синхронизации AutoSklad

## Оглавление

1. [Общая архитектура](#общая-архитектура)
2. [Компоненты системы](#компоненты-системы)
3. [Жизненный цикл синхронизации](#жизненный-цикл-синхронизации)
4. [Протоколы и форматы данных](#протоколы-и-форматы-данных)
5. [Обработка ошибок и повторы](#обработка-ошибок-и-повторы)
6. [Безопасность](#безопасность)
7. [Конфигурация](#конфигурация)
8. [Диагностика и мониторинг](#диагностика-и-мониторинг)

---

## Общая архитектура

Система синхронизации AutoSklad представляет собой двустороннюю (bidirectional) систему синхронизации данных между центральным сервером и множеством клиентских устройств. Архитектура построена на принципах:

- **Event-Driven Architecture** - изменения в БД отслеживаются через декораторы и CDC (Change Data Capture)
- **Queue-Based Processing** - команды буферизируются в очередях для надежной доставки
- **Schema-Aware Synchronization** - автоматическое согласование схем между клиентом и сервером
- **Conflict Resolution** - автоматическое разрешение конфликтов при одновременных изменениях
- **Retry Mechanism** - автоматические повторы при сбоях с экспоненциальной задержкой

### Высокоуровневая диаграмма

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT DEVICE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐       │
│  │ Application  │───>│ @sync_aware │───>│CommandQueue  │       │
│  │  (CRUD Ops)  │    │  Decorator  │    │  (JSON file) │       │
│  └──────────────┘    └─────────────┘    └──────┬───────┘       │
│                                                  │               │
│                                                  ▼               │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐       │
│  │CommandSender │<───│   Runner    │───>│CommandReceiver│      │
│  │   (PUSH)     │    │  (Scheduler)│    │   (PULL)      │      │
│  └──────┬───────┘    └─────────────┘    └──────┬────────┘      │
│         │                                       │                │
│         │            ┌─────────────┐            │                │
│         └───────────>│SyncProcessor│<───────────┘                │
│                      └──────┬──────┘                             │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                     ┌────────▼────────┐
                     │TransportService │
                     │  (HTTP/WS +     │
                     │   AES + HMAC)   │
                     └────────┬────────┘
                              │
┌─────────────────────────────┼────────────────────────────────────┐
│                             │                                    │
│                      ┌──────▼──────┐                             │
│                      │SyncProcessor│                             │
│                      └──────┬──────┘                             │
│                             │                                    │
│  ┌──────────────┐    ┌─────▼────────┐    ┌──────────────┐      │
│  │CommandReceiver───>│BatchProcessor│───>│ SyncManager  │      │
│  │   (handles   │    │ (Transaction)│    │  (CRUD ops)  │      │
│  │   PUSH)      │    └──────────────┘    └──────┬───────┘      │
│  └──────────────┘                               │               │
│                                                  ▼               │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐       │
│  │CommandSender │    │   Runner    │    │  Database    │       │
│  │   (prepares  │<───│  (Scheduler)│    │  (SQLite)    │       │
│  │    PULL)     │    └─────────────┘    └──────────────┘       │
│  └──────────────┘                                               │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                         SERVER                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Потоки данных

1. **Local Changes (Client → Server)**:
   ```
   CRUD Operation → @sync_aware → CommandQueue → CommandSender → 
   CommandOrderer 🆕 → TransportService → Server SyncProcessor → 
   CommandOrderer 🆕 → BatchProcessor → SyncManager → Database
   ```

2. **Remote Changes (Server → Client)**:
   ```
   Database → CommandQueue → CommandReceiver (periodic) → 
   TransportService → Client SyncProcessor → CommandOrderer 🆕 → 
   BatchProcessor → SyncManager → Database
   ```

---

## Компоненты системы

### 1. Runner (Точка входа)

**Файлы**: `server/dbSync/Runner.py`, `client/dbSync/Runner.py`

**Назначение**: Управление жизненным циклом синхронизации для каждого устройства.

**Основные функции**:
- `start_sync(device_id, host, port, ...)` - запускает процесс синхронизации в отдельном потоке
- `stop_sync(device_id)` - останавливает синхронизацию для устройства
- `create_sync_components()` - инициализирует все компоненты системы

**Ключевые особенности**:
```python
def start_sync(device_id: int, host: str, ...):
    # Создает отдельный поток для каждого устройства
    # Регистрирует планировщик задач (APScheduler)
    # Запускает периодические задачи:
    #   - job_send (отправка pending команд)
    #   - job_fetch (получение команд с сервера)
    #   - job_process_retrying (повтор неудачных команд)
    
    # Запускает цикл обработки очереди
    while device_id in _active_schedulers:
        msg = queue_in.get(timeout=10)
        # Обработка сообщений типа:
        # - "handshake" - согласование схем
        # - "local" - локальные изменения
```

**Планировщик задач**:
- `job_send`: вызывается каждые `scheduler_sender_timeout` секунд (по умолчанию 60)
- `job_fetch`: вызывается каждые `scheduler_receiver_timeout` секунд (по умолчанию 120)
- `job_process_retrying`: обрабатывает команды со статусом "retrying"

---

### 2. Декоратор @sync_aware

**Файл**: `server/dbSync/decorators.py`, `client/dbSync/decorators.py`

**Назначение**: Автоматическое отслеживание изменений в CRUD-операциях и генерация команд синхронизации.

**Принцип работы**:
```python
@sync_aware
def add(self, **kwargs):
    # Метод CRUD-класса
    pass
```

**Логика декоратора**:
1. **Проверка режима**:
   - `dbSync.init_db == True` → выполняется без синхронизации (инициализация БД)
   - `sync_context == True` → выполняется без генерации команды (применение команды из синхронизации)

2. **Дедупликация**:
   - Вычисляет ключ `payload_key` на основе `id`/`index` и данных
   - Проверяет, не выполнялась ли уже эта операция
   - Если да - возвращает сохраненный результат без повторного выполнения

3. **Валидация**:
   - Проверяет данные через `DataTransformer.validate()`

4. **Выполнение**:
   - Вызывает оригинальный CRUD-метод

5. **Постобработка**:
   - Сохраняет результат для дедупликации
   - Формирует команду и кладет в `INBOUND_QUEUES[device_id]`

**Пример команды**:
```python
{
    "type": "local",
    "table": "Tools",
    "operation": "add",
    "data": {
        "index": 42,
        "name": "Инструмент",
        "count": 5
    }
}
```

---

### 3. CommandQueue (Очередь команд)

**Файл**: `server/dbSync/Logic_v2/CommandQueue.py`

**Назначение**: Надежное хранение команд синхронизации с поддержкой персистентности.

**Структура команды**:
```python
class Command(TypedDict):
    id: str                    # UUID команды
    table: str                 # Имя таблицы
    operation: Literal["insert", "update", "delete"]
    data: Dict                 # Полезная нагрузка
    status: Literal["pending", "retrying", "failed", "done"]
    timestamp: str             # ISO 8601 (UTC)
    retry_count: int           # Количество попыток
    last_retry_timestamp: str  # Время последней попытки
```

**Хранение**: JSON-файл `command_queue.json` с атомарной записью через временный файл.

**Основные методы**:
- `add_command(table, operation, data)` → создает команду со статусом "pending"
- `get_pending_commands()` → возвращает команды со статусом "pending"
- `get_retrying_commands()` → возвращает команды для повтора (отсортированы по времени)
- `mark_as_done(command_id)` → помечает команду как успешно выполненную
- `mark_as_failed(command_id)` → помечает команду как неуспешную
- `mark_as_retrying(command_id)` → переводит в режим повтора
- `clear_done()` → удаляет успешно выполненные команды

**Потокобезопасность**: Использует `threading.RLock()` для синхронизации доступа.

---

### 4. CommandSender (Отправка команд)

**Файл**: `server/dbSync/Logic_v2/CommandSender.py`, `client/dbSync/Logic_v2/CommandSender.py`

**Назначение**: Push-процесс - отправка локальных изменений на сервер.

**Процесс отправки** (`send_pending`):

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Handshake (при первом вызове)                            │
│    _ensure_handshake() → получает mapping схемы              │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Обработка retrying команд                                 │
│    retry_manager.retry_all_retrying()                        │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Проверка согласованности                                  │
│    Есть ли retrying/failed команды старше pending?           │
│    Если да → выход (сначала обработать старые)               │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Подготовка payload                                        │
│    - Обогащение данных через DataTransformer.postprocess()  │
│    - Формирование списка ServerCommand                      │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Отправка                                                  │
│    transport.send_push(endpoint, payload)                   │
│    └─> HTTP POST с AES+HMAC шифрованием                     │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Обработка результата                                      │
│    Success: mark_as_done() для всех команд                  │
│    Failure: mark_as_retrying() → планирование повтора       │
└─────────────────────────────────────────────────────────────┘
```

**Структура PushPayload**:
```python
{
    "device": int,           # ID устройства
    "schema_hash": str,      # Хэш схемы для валидации
    "commands": [
        {
            "id": str,       # UUID команды
            "table": str,
            "operation": "INSERT" | "UPDATE" | "DELETE",
            "data": dict,
            "last_modified": str  # ISO timestamp
        }
    ]
}
```

**Особенности**:
- Обогащение данных для таблицы `Tools` (добавление полей из `ToolTypes`)
- Хронологический порядок отправки (сначала старые команды)
- Dev-режим с эмуляцией server-side обработки

---

### 5.5. CommandOrderer (Оптимизация команд) 🆕

**Файл**: `server/dbSync/Logic_v2/CommandOrderer.py`

**Назначение**: Интеллектуальная обработка batch команд - валидация, оптимизация и упорядочивание перед выполнением.

**Проблемы, которые решает**:

1. **Избыточные команды**: ADD + UPDATE + DELETE одной записи в одном batch
2. **Нарушение порядка FK**: Попытка удалить родителя перед дочерними записями
3. **Противоречивые операции**: ADD и DELETE одной записи за короткий промежуток
4. **Неэффективность**: Множественные UPDATE одной записи

**Место в архитектуре**:

```
CommandQueue → CommandSender → CommandOrderer → SyncProcessor → BatchProcessor → DB
```

**Основные возможности**:

#### Сжатие последовательностей (Compression)

Оптимизация избыточных операций для одной записи:

```python
# ADD + UPDATE → ADD (с объединёнными данными)
[ADD {id:1, name:"A"}, UPDATE {id:1, name:"B"}] → [ADD {id:1, name:"B"}]

# ADD + UPDATE + DELETE → DELETE
[ADD {id:1}, UPDATE {id:1}, DELETE {id:1}] → [DELETE {id:1}]

# Множественные UPDATE → последний UPDATE
[UPDATE {id:1, count:5}, UPDATE {id:1, count:10}] → [UPDATE {id:1, count:10}]

# DELETE + ADD → оба сохраняются (воскрешение записи)
[DELETE {id:1}, ADD {id:1}] → [DELETE {id:1}, ADD {id:1}] + warning
```

**Результат**: Сокращение команд на 30-80% в типичных сценариях.

#### Критические таблицы (CRITICAL_STATE_TABLES) 🆕

**Проблема**: Для некоторых таблиц каждое изменение состояния критично для синхронизации и не может быть сжато.

**Пример проблемы с Cell**:
- При массовой загрузке: `status_id` меняется последовательно: `1` (пустая) → `2` (mass_load_init) → `3` (loaded)
- При выдаче: `status_id` меняется: `3` (loaded) → `4` (consumption), `tools_id` → `NULL`
- Если сжать `[UPDATE {status_id:2}, UPDATE {status_id:3}]` → `[UPDATE {status_id:3}]`, теряется промежуточное состояние

**Решение**: Для критических таблиц (например, `Cell`) множественные UPDATE **НЕ сжимаются**:

```python
CRITICAL_STATE_TABLES = {
    "Cell",  # Критично: status_id, tools_id, groups_id меняются при операциях
}

# Для Cell: все UPDATE сохраняются последовательно
[UPDATE Cell {id:2, status_id:2}, UPDATE Cell {id:2, status_id:3}]
  → [UPDATE Cell {id:2, status_id:2}, UPDATE Cell {id:2, status_id:3}] + warning

# Для обычных таблиц: UPDATE сжимаются
[UPDATE ToolTypes {id:1, count:5}, UPDATE ToolTypes {id:1, count:10}]
  → [UPDATE ToolTypes {id:1, count:10}]
```

**Критерии для добавления таблицы в CRITICAL_STATE_TABLES**:
- Таблица имеет поля состояния (`status_id`, `tools_id`, `groups_id` и т.д.)
- Каждое изменение состояния должно быть синхронизировано
- Промежуточные состояния важны для логики приложения
- Потеря промежуточных состояний приводит к неконсистентности данных

**Текущие критические таблицы**:
- `Cell`: каждое изменение `status_id`, `tools_id`, `groups_id` критично при массовой загрузке/выдаче

#### Топологическая сортировка

Упорядочивание команд по FK зависимостям:

```python
TABLE_PRIORITY = {
    "Status": 0,      # Корневые справочники
    "Group": 10,      # Зависят только от справочников
    "ToolTypes": 20,  # Зависят от Group
    "Tools": 21,      # Зависят от ToolTypes
    "Cell": 30,       # Зависят от Tools
    "Load": 40,       # Зависят от Cell
    ...
}

# Для ADD/UPDATE: родители → дочерние (прямой порядок)
[ADD ToolTypes, ADD Group] → [ADD Group, ADD ToolTypes]

# Для DELETE: дочерние → родители (обратный порядок)
[DELETE Group, DELETE ToolTypes, DELETE Cell] → [DELETE Cell, DELETE ToolTypes, DELETE Group]
```

#### Валидация операций

Обнаружение проблемных последовательностей:

```python
# UPDATE без предшествующего ADD
[UPDATE {id:1}] → Warning: "Record may not exist"

# DELETE без предшествующего ADD
[DELETE {id:1}] → Warning: "Deleting non-existent record"

# FK нарушение
[DELETE Group {id:1}, ADD ToolTypes {groups_id:1}] 
  → Warning: "FK violation - parent deleted before child ADD"
```

**Основной метод**:

```python
def order_and_validate(
    commands: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    :param commands: Список команд от клиента
    :return: (validated_commands, warnings)
    
    Последовательность обработки:
    1. Группировка по (table, record_id)
    2. Сжатие последовательностей для каждой записи
    3. Валидация корректности операций
    4. Топологическая сортировка по таблицам и операциям
    5. Финальная проверка зависимостей FK
    """
```

**Интеграция в SyncProcessor**:

```python
# В process_push(), после валидации JSON:
ordered_commands, orderer_warnings = self.command_orderer.order_and_validate(commands)

if orderer_warnings:
    self.diagnostic_logger.log_warning("Command order validation", {
        "warnings_count": len(orderer_warnings),
        "warnings": orderer_warnings[:5]
    })

if len(ordered_commands) < original_count:
    compression_ratio = (original_count - len(ordered_commands)) / original_count
    self.diagnostic_logger.log_info("Commands optimized", {
        "original_count": original_count,
        "optimized_count": len(ordered_commands),
        "compression_ratio": f"{compression_ratio:.1%}"
    })

commands = ordered_commands  # Используем оптимизированные команды
```

**Статистика работы**:

```python
stats = command_orderer.get_statistics()
# {
#     "total_processed": 1500,      # Всего обработано команд
#     "total_compressed": 600,       # Удалено избыточных
#     "total_warnings": 23,          # Количество warnings
#     "compression_ratio": 0.40      # Коэффициент сжатия (40%)
# }
```

**Примеры из production**:

```python
# Инцидент 9 декабря 2025: Пользователь создал и удалил запись
# ДО оптимизации:
[
    {"operation": "ADD", "table": "Group", "data": {"id": 1}},
    {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "groups_id": 1}},
    {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}}
]
# 3 команды, противоречивые операции

# ПОСЛЕ оптимизации:
[
    {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}},
    {"operation": "ADD", "table": "Group", "data": {"id": 1}}
]
# 2 команды, сжатие 33%, корректный порядок
```

**Потокобезопасность**: Использует `threading.RLock()` для синхронизации доступа.

**Тестирование**: 
- 18 unit-тестов в `tests/test_CommandOrderer.py`
- 9 integration-тестов в `tests/test_SyncIntegration.py`
- Покрытие всех edge cases

---

### 5. CommandReceiver (Получение команд)

**Файл**: `server/dbSync/Logic_v2/CommandReceiver.py`, `client/dbSync/Logic_v2/CommandReceiver.py`

**Назначение**: Pull-процесс - получение изменений с сервера.

**Процесс получения** (`fetch_and_apply`):

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Handshake (при первом вызове)                            │
│    _ensure_handshake() → получает mapping и schema_hash     │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Формирование запроса                                      │
│    params = {                                                │
│        "device": device_id,                                  │
│        "since": last_synced,  # ISO timestamp                │
│        "schema_hash": schema_hash                            │
│    }                                                         │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Запрос к серверу                                          │
│    response = transport.send_pull(endpoint, params)         │
│    └─> HTTP GET с AES+HMAC дешифрованием                    │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Применение команд                                         │
│    for cmd in response["commands"]:                         │
│        sync_processor.process_push([cmd])                   │
│        if cmd.last_modified > new_last:                     │
│            new_last = cmd.last_modified                     │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Обновление границы синхронизации                          │
│    if new_last != last_synced:                              │
│        _save_last_synced(new_last)                          │
└─────────────────────────────────────────────────────────────┘
```

**Структура PullResponse**:
```python
{
    "schema_hash": str,
    "commands": [
        {
            "id": int,       # ID команды на сервере
            "table": str,
            "operation": "INSERT" | "UPDATE" | "DELETE",
            "data": dict,
            "last_modified": str  # ISO timestamp
        }
    ]
}
```

**Граница синхронизации**: Хранится в файле `last_synced.txt` в формате ISO 8601.

---

### 6. SyncProcessor (Центральный координатор)

**Файл**: `server/dbSync/Logic_v2/SyncProcessor.py`

**Назначение**: Координация всех этапов синхронизации между устройством и сервером.

**Основные методы**:

#### 6.1. process_schema (Handshake)

Согласование схемы клиента и сервера:

```python
def process_schema(
    src_schema: Dict[str, Dict[str, Any]],  # Схема клиента
    client_schema_hash: str                 # SHA256 хэш схемы
) -> Dict[str, Union[str, Dict]]:           # mapping + schema_hash
```

**Этапы**:
1. Валидация входящей схемы через `JSONSchemaValidator`
2. Поиск mapping в `SchemaCache` по хэшу
3. Если не найден - генерация через `SchemaAnalyzer.generate_mapping()`
4. Сохранение в кэш
5. Валидация ответа
6. Логирование метрик через `SyncMonitor`

#### 6.2. prepare_pull (Подготовка команд для клиента)

```python
def prepare_pull(
    device: int,
    since: str,                  # ISO timestamp
    client_schema_hash: str
) -> Dict[str, Any]:             # schema_hash + commands
```

**Этапы**:
1. Получение mapping схемы
2. Запрос pending команд из БД (`CommandCRUD.get_pending_for_device`)
3. Загрузка данных записей (`RecordCRUD.get_bulk_records`)
4. Для каждой команды:
   - Трансформация данных (`DataMapper.map_outgoing`)
   - Постобработка (`DataTransformer.postprocess`)
   - Получение `last_modified`
5. Формирование ответа
6. Валидация и логирование

#### 6.3. process_push (Применение команд от клиента)

```python
def process_push(
    device: int,
    commands: List[Dict[str, Any]],
    client_schema_hash: str
) -> List[Dict[str, Any]]:       # Статусы команд
```

**Полный цикл обработки**:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Валидация JSON                                            │
│    json_validator.validate(commands, "push_commands")       │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Фильтрация дубликатов ADD-операций                       │
│    if operation == "ADD" and rec_id exists:                 │
│        existing = sync_manager.get_current_data()           │
│        if data == existing: skip                            │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Обработка каждой команды (_process_single)               │
│    a) preprocess (DataTransformer)                          │
│    b) validate (DataTransformer)                            │
│    c) detect_structure_conflict (ConflictManager)           │
│    d) map_incoming (DataMapper)                             │
│    e) postprocess (DataTransformer)                         │
│    f) detect_data_conflict (ConflictManager)                │
│    g) resolve conflict (ConflictManager)                    │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Пакетное выполнение                                       │
│    results = batch_processor.execute_batch(operations)      │
│    └─> Атомарная транзакция для всех операций              │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Обновление статусов                                       │
│    for result in results:                                   │
│        status_crud.add_status(cmd_id, "COMPLETED"/"FAILED")│
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Планирование повторов для неудач                          │
│    if failed:                                               │
│        retry_manager.schedule_retry(cmd, delay)             │
└─────────────────────────────────────────────────────────────┘
```

**Особенности**:
- Сохраняет `current_device_id` для callback'ов (создание связей)
- Транзакционная безопасность через `with cmd_crud.transaction()`
- Поддержка эмуляции server-side в dev-режиме

---

### 7. BatchProcessor (Пакетная обработка)

**Файл**: `server/dbSync/Logic_v2/BatchProcessor.py`

**Назначение**: Атомарное выполнение CRUD-операций в одной транзакции.

**Структура операции**:
```python
class Operation(TypedDict):
    command_id: int          # ID команды из журнала
    table: str               # Целевая таблица
    operation: str           # "insert" | "update" | "delete"
    data: Dict[str, Any]     # Полезная нагрузка
    id: Optional[int]        # PK для update/delete
```

**Процесс** (`execute_batch`):

```python
def execute_batch(operations: List[Operation]) -> List[OperationResult]:
    # 1. Предварительная обработка: связывание Consumption с History
    _link_consumption_to_history(operations)
    
    results = []
    try:
        with session.begin_nested():  # SAVEPOINT
            for op in operations:
                # 2. Применение операции через SyncManager
                result = _apply_single(op)
                
                # 3. Сбор результата
                results.append({
                    "command_id": op["command_id"],
                    "success": True,
                    "new_id": result.get("id")
                })
                
    except SQLAlchemyError:
        # Откат всей транзакции при первой ошибке
        return results
    
    return results
```

**Ключевые особенности**:
- **Атомарность**: Все операции или ни одна
- **Автосвязывание**: Команды `Consumption` автоматически связываются с `History` из того же батча
- **Контекст синхронизации**: Флаг `sync_context=True` для отличия от обычных операций

---

### 8. SyncManager (CRUD-фасад)

**Файл**: `server/dbSync/Logic_v2/SyncManager.py`

**Назначение**: Абстрактный слой над CRUD-классами для выполнения команд синхронизации.

**Основные методы**:

#### 8.1. process_command / process_sync_command

```python
def process_sync_command(
    command: Dict[str, Any],
    sync_context: bool = True
) -> Any:
```

Разбирает команду и вызывает соответствующий обработчик:
- `INSERT/ADD` → `_handle_insert`
- `UPDATE` → `_handle_update`
- `DELETE` → `_handle_delete`

#### 8.2. _handle_insert

```python
def _handle_insert(crud, table, data, rec_id, sync_context=False):
```

**Логика**:
1. **Инкремент count** (только для `Tools`/`Consumption` в non-sync режиме):
   ```python
   if table in ("Tools", "Consumption") and "count" in data and not sync_context:
       existing = crud.get(rec_id)
       if existing:
           return _increment_count(crud, rec_id, data["count"])
   ```

2. **UPSERT**: Если запись существует → обновление через `_upsert_update`

3. **INSERT**: Чистая вставка с обработкой `IntegrityError` (race condition)

4. **Автосвязывание**: 
   - Для `Consumption`: поиск связанной `History` по `tools_id`
   - Для `History`: создание связи через callback `on_new_history`

5. **События**: Вызов `fire_after_insert(table, result)`

#### 8.3. _upsert_update

**Логика**:
- Сравнение существующих и входящих данных
- В режиме синхронизации (`sync_context=True`): всегда обновляет
- В обычном режиме: обновляет только при изменении данных
- Исключает служебные поля: `id`, `index`, `created_at`, `updated_at`

#### 8.4. get_local_schema

```python
def get_local_schema() -> Dict[str, Dict[str, str]]:
    # Возвращает: {table_name: {column_name: type_name}}
```

Сканирует все таблицы из `Base.metadata` и извлекает схему.

---

### 9. RetryManager (Повторы)

**Файл**: `server/dbSync/Logic_v2/RetryManager.py`

**Назначение**: Управление автоматическими повторами неудачных команд.

**Параметры**:
- `max_retries` (по умолчанию 4320) - максимум попыток
- `base_delay` (по умолчанию 30.0 сек) - фиксированная задержка между попытками

**Основные методы**:

#### 9.1. schedule_retry

```python
def schedule_retry(cmd: RetryCommand, delay: Optional[float] = None):
```

- Увеличивает `retry_count`
- Если превышен `max_retries` → `mark_as_failed`
- Иначе команда остается в статусе "retrying"

#### 9.2. retry_all_retrying

```python
def retry_all_retrying() -> int:  # Возвращает количество успешных
```

**Логика**:
```
for cmd in retrying_commands:
    1. Проверка max_retries
       if retry_count >= max_retries:
           mark_as_failed()
           continue
    
    2. Проверка времени с последней попытки
       if time_since_last < base_delay:
           skip  # Еще не прошло достаточно времени
    
    3. Обновление timestamp
       update_last_retry_timestamp(now)
    
    4. Попытка отправки
       if _retry_one(cmd):
           success_count++
       else:
           schedule_retry(cmd)  # Увеличить счетчик и повторить позже
```

#### 9.3. _retry_one

```python
def _retry_one(cmd: RetryCommand) -> bool:
```

- Вызывает `sender.send_single_command(cmd)`
- При успехе: `mark_as_done`
- При неудаче: обновляет `last_retry_timestamp` и увеличивает `retry_count`

**Стратегия**: Фиксированный интервал 30 секунд, 36 часов максимум (4320 × 30 сек).

---

### 10. TransportService (Транспортный слой)

**Файл**: `server/dbSync/Transport/TransportService.py`

**Назначение**: HTTP/WebSocket клиент с шифрованием и подписью.

**Безопасность**:
- **JWT**: Bearer-токен в заголовке `Authorization`
- **HMAC-SHA256**: Подпись тела запроса в заголовке `X-Signature`
- **AES-CBC**: Шифрование/дешифрование тела (16-байтовый IV в начале)

**Основные методы**:

#### 10.1. send_schema (Handshake)

```python
def send_schema(
    endpoint: str,
    schema_json: Dict[str, Any],
    device: int
) -> Dict[str, Any]:  # mapping + schema_hash
```

**Запрос**: `POST /sync/handshake?device={device_id}`

**Тело** (зашифровано AES):
```json
{
    "schema": {
        "Users": {
            "id": "integer",
            "name": "string",
            "email": "string"
        },
        ...
    }
}
```

**Ответ** (зашифровано AES):
```json
{
    "mapping": {
        "Users": {
            "user_id": "id",
            "user_name": "name"
        },
        ...
    },
    "schema_hash": "abc123..."
}
```

#### 10.2. send_push (Отправка команд)

```python
def send_push(
    endpoint: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
```

**Запрос**: `POST /sync/push?device={device_id}`

**Процесс**:
1. Сериализация `payload` в JSON
2. Шифрование AES-CBC (16-байтовый случайный IV + ciphertext)
3. Вычисление HMAC-SHA256 от зашифрованного тела
4. Отправка с заголовками:
   ```
   Authorization: Bearer {jwt_token}
   X-Signature: {hmac_hex}
   Content-Type: application/octet-stream
   ```
5. Получение ответа (зашифрован)
6. Дешифрование
7. Валидация через `JSONSchemaValidator`

#### 10.3. send_pull (Получение команд)

```python
def send_pull(
    endpoint: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
```

**Запрос**: `GET /sync/pull?device={device}&since={iso_timestamp}&schema_hash={hash}`

**Процесс**: Аналогичен `send_push` (шифрование, подпись, дешифрование).

---

### 11. DataMapper (Маппинг полей)

**Файл**: `server/dbSync/Logic_v2/DataMapper.py`

**Назначение**: Преобразование имен полей между клиентом и сервером.

**Загрузка mapping**: Из файла `dbSync/Logic_v2/cache/fields/sync_fields.json`

**Методы**:

```python
def map_outgoing(table: str, data: Dict) -> Dict:
    # Client/Server → Remote: {"local_field": "remote_field"}
    
def map_incoming(table: str, data: Dict, mapping: Dict) -> Dict:
    # Remote → Client/Server: reverse mapping
```

**Пример mapping**:
```json
{
    "Tools": {
        "id": "tool_id",
        "name": "tool_name",
        "count": "quantity"
    }
}
```

**Динамическое обновление**:
```python
def update_field_mappings(new_mappings: Dict):
    # Обновляет маппинг на основе handshake
```

---

### 12. DataTransformer (Трансформация данных)

**Файл**: `server/dbSync/Logic_v2/DataTransformer.py`

**Назначение**: Бизнес-правила для пред- и постобработки данных.

**Регистрация правил**:
```python
transformer = DataTransformer()

# Правило обогащения для исходящих данных
def enrich_tools(record: dict) -> dict:
    tool_type = get_tool_type(record["id"])
    record["name"] = tool_type.name
    record["description"] = tool_type.description
    return record

transformer.register_rule("Tools", "outgoing", enrich_tools)

# Правило для входящих данных
transformer.register_rule(
    'Cell',
    'incoming',
    lambda d: {**d, 'id': d.get('index', d.get('id'))}
)
```

**Специальные правила** (из `setup.py`):

1. **Tools (outgoing)**: Обогащение данными из `ToolTypes`
   ```python
   record["name"] = tool_type.name
   record["description"] = tool_type.description
   record["img"] = tool_type.img
   record["groups_id"] = tool_type.groups_id
   ```

2. **Cell (incoming)**: Нормализация ID
   ```python
   {'id': data.get('index', data.get('id'))}
   ```

3. **History (incoming)**: Извлечение status из вложенного объекта
   ```python
   if 'Status' in record and isinstance(record['Status'], dict):
       record['status'] = record['Status']['id']
       del record['Status']
   ```

**Методы**:
- `preprocess(table, data)` - применяет правила до валидации
- `postprocess(table, data)` - применяет правила после валидации
- `validate(table, data)` - проверка корректности данных

---

### 13. SchemaAnalyzer и SchemaCache

**Файлы**: 
- `server/dbSync/Logic_v2/SchemaAnalyzer.py`
- `server/dbSync/Logic_v2/SchemaCache.py`

**Назначение**: Автоматическая генерация и кэширование маппингов схем.

#### SchemaAnalyzer

```python
def generate_mapping(
    src_schema: Dict[str, Dict[str, str]],  # Клиентская схема
    dst_schema: Dict[str, Dict[str, str]]   # Серверная схема
) -> Dict[str, Dict[str, str]]:             # Маппинг полей
```

**Алгоритм**:
1. Для каждой таблицы в `src_schema`:
   - Найти соответствующую таблицу в `dst_schema` (exact match или fuzzy)
   - Для каждого поля:
     - Найти соответствующее поле по имени (exact, snake_case, camelCase)
     - Проверить совместимость типов
   - Вернуть маппинг: `{src_field: dst_field}`

2. Обработка конфликтов:
   - Неоднозначные поля → вызов `MappingConfigurator.on_conflict()`
   - Несовместимые типы → исключение

#### SchemaCache

```python
class SchemaCache:
    def get(schema_hash: str) -> Optional[Dict]
    def set(schema_hash: str, mapping: Dict)
```

**Хранение**: JSON-файл `dbSync/Logic_v2/cache/schema/schema_cache.json`

**Структура**:
```json
{
    "abc123...": {
        "Users": {"user_id": "id", "user_name": "name"},
        "Tools": {"tool_id": "id", "tool_name": "name"}
    }
}
```

---

### 14. ConflictManager (Разрешение конфликтов)

**Файл**: `server/dbSync/Logic_v2/ConflictManager.py`

**Назначение**: Обнаружение и разрешение конфликтов при синхронизации.

**Типы конфликтов**:

1. **Структурные** (schema mismatch):
   - Отсутствие полей
   - Несовместимые типы
   - Дополнительные поля

2. **Данных** (concurrent modifications):
   - Одновременное изменение записи
   - Решение через стратегию (last-write-wins, custom)

**Методы**:

```python
def detect_structure_conflict(
    incoming_fields: List[str],
    local_schema: List[str]
) -> List[str]:  # Список конфликтных полей
    
def detect_data_conflict(
    existing: Dict,
    incoming: Dict
) -> bool:  # True если есть конфликт
    # Сравнивает значения общих полей
    
def apply_data_strategy(
    existing: Dict,
    incoming: Dict,
    strategy: str = "last_write_wins"
) -> Dict:  # Разрешенные данные
```

**Стратегии**:
- `last_write_wins` (по умолчанию): Приоритет у входящих данных
- `first_write_wins`: Приоритет у существующих данных
- `merge`: Слияние полей (берется непустое значение)
- `custom`: Пользовательская функция

---

### 15. Дополнительные компоненты

#### 15.1. DiagnosticLogger

**Файл**: `server/dbSync/Logic_v2/DiagnosticLogger.py`

Централизованное логирование с контекстом:
```python
logger.log_info("Operation completed", {"device": 1, "count": 10})
logger.log_error("Operation failed", {"error": str(e), "traceback": ...})
logger.log_debug("Step X", {...})
```

#### 15.2. SyncMonitor

**Файл**: `server/dbSync/Logic_v2/SyncMonitor.py`

Сбор метрик:
```python
sync_monitor.record_success(duration)
sync_monitor.record_failure(duration)
sync_monitor.get_stats()  # → {success_count, failure_count, avg_duration}
```

#### 15.3. JSONSchemaValidator

**Файл**: `server/dbSync/Logic_v2/JSONSchemaValidator.py`

Валидация по JSON Schema:
```python
validator.validate(data, "handshake_request")
validator.validate(data, "push_commands")
validator.validate(data, "pull_response")
```

---

## Жизненный цикл синхронизации

### Инициализация

```python
# server/main.py или client/main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    devices = crud.get_all_devices()
    for device in devices:
        start_sync(
            device_id=device.id,
            host=device.ip,
            port=device.port,
            token=device.token,
            secret=device.hmac_secret,
            aes=AES_KEY,
            scheduler_sender_timeout=60,
            scheduler_receiver_timeout=120
        )
    
    yield
    
    # Shutdown
    for device_id in device_ids:
        stop_sync(device_id)
```

### Сценарий 1: Локальное изменение (Client → Server)

```
1. Пользователь добавляет инструмент
   ↓
2. @sync_aware декоратор:
   - Выполняет CRUD.add()
   - Генерирует команду
   - Кладет в INBOUND_QUEUE
   ↓
3. Runner обрабатывает команду:
   - processor.enqueue_local_command()
   - Добавляет в CommandQueue (pending)
   ↓
4. job_send (планировщик):
   - sender.send_pending()
   - Обогащает данные (DataTransformer)
   - Отправляет через TransportService
   ↓
5. Сервер получает PUSH:
   - Handshake (при первом запросе)
   - Валидация JSON
   - Фильтрация дубликатов
   - process_push() → BatchProcessor
   - Применение в БД
   ↓
6. Ответ серверу:
   - Статусы команд
   - Client помечает команды как "done"
```

### Сценарий 2: Удаленное изменение (Server → Client)

```
1. Сервер изменяет данные
   ↓
2. @sync_aware на сервере:
   - Выполняет CRUD операцию
   - Добавляет команду в CommandQueue
   ↓
3. job_fetch на клиенте (планировщик):
   - receiver.fetch_and_apply()
   - Запрашивает изменения с сервера
     GET /sync/pull?device=X&since=...
   ↓
4. Сервер готовит ответ:
   - processor.prepare_pull()
   - Получает pending команды из БД
   - Трансформирует данные
   - Возвращает список команд
   ↓
5. Клиент применяет:
   - Для каждой команды:
     processor.process_push([cmd])
   - Обновляет last_synced
```

### Сценарий 3: Обработка ошибок и повторы

```
1. Отправка команды не удалась
   ↓
2. sender.send_pending():
   - Ловит исключение
   - Помечает команды как "retrying"
   ↓
3. job_process_retrying (планировщик):
   - retry_manager.retry_all_retrying()
   - Для каждой retrying команды:
     * Проверка времени с последней попытки
     * Если прошло >= base_delay:
       - Попытка отправки
       - При неудаче: увеличение retry_count
   ↓
4. Если retry_count >= max_retries:
   - Команда помечается как "failed"
   - Требуется ручное вмешательство
```

---

## Протоколы и форматы данных

### Формат команды в очереди

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "table": "Tools",
    "operation": "insert",
    "data": {
        "index": 42,
        "name": "Отвертка",
        "count": 5,
        "tool_type_id": 1
    },
    "status": "pending",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "retry_count": 0,
    "last_retry_timestamp": null
}
```

### Формат PUSH-запроса

**Запрос**: `POST /sync/push?device=1`

**Заголовки**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Signature: a3b2c1d4e5f6...
Content-Type: application/octet-stream
```

**Тело** (после дешифрования AES):
```json
{
    "device": 1,
    "schema_hash": "abc123...",
    "commands": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "table": "Tools",
            "operation": "INSERT",
            "data": {
                "index": 42,
                "name": "Отвертка",
                "count": 5,
                "tool_type_id": 1,
                "description": "Отвертка крестовая",
                "img": "screwdriver.png"
            },
            "last_modified": ""
        }
    ]
}
```

**Ответ**:
```json
{
    "statuses": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "COMPLETED"
        }
    ]
}
```

### Формат PULL-запроса

**Запрос**: `GET /sync/pull?device=1&since=2024-01-15T10:00:00.000Z&schema_hash=abc123...`

**Ответ** (после дешифрования AES):
```json
{
    "schema_hash": "abc123...",
    "commands": [
        {
            "id": "15",
            "table": "Cell",
            "operation": "UPDATE",
            "data": {
                "index": 10,
                "name": "Ячейка A1",
                "number_cell": 1,
                "tools_id": 42
            },
            "last_modified": "2024-01-15T10:25:00.000Z"
        }
    ]
}
```

### Формат Handshake

**Запрос**: `POST /sync/handshake?device=1`

**Тело**:
```json
{
    "schema": {
        "Tools": {
            "id": "integer",
            "name": "string",
            "count": "integer",
            "tool_type_id": "integer"
        },
        "Cell": {
            "id": "integer",
            "name": "string",
            "number_cell": "integer",
            "tools_id": "integer"
        }
    }
}
```

**Ответ**:
```json
{
    "mapping": {
        "Tools": {
            "id": "index",
            "name": "name",
            "count": "count",
            "tool_type_id": "tool_type_id"
        },
        "Cell": {
            "id": "index",
            "name": "name",
            "number_cell": "number_cell",
            "tools_id": "tools_id"
        }
    },
    "schema_hash": "abc123..."
}
```

---

## Обработка ошибок и повторы

### Стратегия повторов

```
Попытка 1: немедленно
Попытка 2: через 30 сек
Попытка 3: через 30 сек
...
Попытка 4320: через 30 сек
Total: 36 часов (4320 × 30 сек = 129600 сек)

После 4320 попыток: команда помечается как "failed"
```

### Обработка IntegrityError (race condition)

```python
try:
    crud.add(index=rec_id, **clean_data)
except IntegrityError:
    # Запись появилась между проверкой и вставкой
    existing = crud.get(rec_id)
    if existing:
        # Делаем upsert вместо insert
        return _upsert_update(crud, rec_id, data)
    # Если не найдена - пробрасываем ошибку дальше
    raise
```

### Обработка сетевых ошибок

```python
try:
    response = transport.send_push(endpoint, payload)
except requests.exceptions.RequestException as e:
    # Сетевая ошибка - команды переходят в retrying
    for cmd in pending:
        queue.mark_as_retrying(cmd["id"])
    raise
except ConnectionError:
    # Сервер недоступен - пропускаем итерацию
    logger.error(f"Server unavailable: {e}")
    return
```

### Логирование ошибок

```python
diagnostic_logger.log_error("Push failed", {
    "error": str(ex),
    "traceback": traceback.format_exc(),
    "device": device_id,
    "commands": commands
})
```

---

## Безопасность

### JWT (JSON Web Token)

**Использование**: Bearer-токен в заголовке `Authorization`.

**Пример**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### HMAC-SHA256 (Подпись)

**Алгоритм**:
```python
def _sign_hmac(body: bytes) -> str:
    signature = hmac.new(
        key=self.hmac_secret,
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature
```

**Передача**: Заголовок `X-Signature`.

**Проверка на сервере**:
```python
def verify_signature(body: bytes, signature: str) -> bool:
    expected = hmac.new(hmac_secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### AES-CBC Шифрование

**Параметры**:
- Ключ: 16/24/32 байта (AES-128/192/256)
- IV (Initialization Vector): 16 байт (случайный)
- Padding: PKCS7

**Шифрование**:
```python
def _encrypt(data: bytes) -> bytes:
    iv = os.urandom(16)  # Случайный IV
    cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
    padded = pad(data, AES.block_size)
    ciphertext = cipher.encrypt(padded)
    return iv + ciphertext  # IV в начале
```

**Дешифрование**:
```python
def _decrypt(data: bytes) -> bytes:
    iv = data[:16]  # Первые 16 байт - IV
    ciphertext = data[16:]
    cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ciphertext)
    return unpad(padded, AES.block_size)
```

### Полный цикл безопасности

```
Отправка:
1. JSON → bytes
2. AES encrypt (random IV)
3. HMAC sign
4. HTTP POST with headers

Получение:
1. Verify HMAC signature
2. AES decrypt
3. bytes → JSON
4. JSON Schema validation
```

---

## Конфигурация

### Server (server/options.py)

```python
Host = "0.0.0.0"
port = 8000

RECEIVER_TIMEOUT = 120  # Интервал pull-запросов (сек)
SENDER_TIMEOUT = 60     # Интервал push-запросов (сек)

AES_KEY = b"16byteslongkey!!"  # 16/24/32 байта для AES
HMAC_SECRET = b"supersecret"    # Секрет для HMAC
```

### Client (client/config.json)

```json
{
    "device_id": 1,
    "network": {
        "ip": "192.168.1.100",
        "port": 8001
    },
    "server": {
        "ip": "192.168.1.10",
        "port": 8000
    },
    "sync": {
        "token": "<YOUR_JWT_TOKEN>",
        "secret": "supersecret",
        "aes_key": "16byteslongkey!!",
        "sender_timeout": 60,
        "receiver_timeout": 120
    }
}
```

### База данных синхронизации (sync.db)

**Расположение**: `server/dbSync/Model/sync.db`, `client/dbSync/Model/sync.db`

**Таблицы**:
- `Command` - журнал команд синхронизации
- `Record` - данные записей
- `CommandStatus` - статусы выполнения команд
- `SyncConfig` - конфигурация синхронизируемых таблиц

**Инициализация**:
```python
from dbSync.sync_db import init_sync_db

init_sync_db(force_recreate=True)
```

---

## Диагностика и мониторинг

### Логи

**Расположение**:
- `server/logs/sync.log`
- `client/logs/sync.log`

**Формат**:
```
[2024-01-15 10:30:00] [ПОТОК][Thread-1][CommandSender] send_pending. 2024-01-15 10:30:00
[2024-01-15 10:30:01] [ПОТОК][Thread-1][CommandSender] 5 pending команд для отправки. 2024-01-15 10:30:01
[2024-01-15 10:30:02] [ПОТОК][Thread-1][TransportService][send_push] Шаг 1: проверяем device_id. [2024-01-15 10:30:02]
[2024-01-15 10:30:03] [ПОТОК][Thread-1][SyncProcessor] Начало push-этапа. Устройство: 1, Команд: 5. [2024-01-15 10:30:03]
```

### Метрики (SyncMonitor)

```python
stats = sync_monitor.get_stats()
# {
#     "success_count": 150,
#     "failure_count": 5,
#     "avg_duration": 0.25,
#     "last_sync": "2024-01-15T10:30:00.000Z"
# }
```

### Диагностические команды

```python
# Проверка состояния очереди
queue = CommandQueue()
pending = queue.get_pending_commands()
retrying = queue.get_retrying_commands()
failed = queue.get_failed_commands()

print(f"Pending: {len(pending)}")
print(f"Retrying: {len(retrying)}")
print(f"Failed: {len(failed)}")

# Проверка границы синхронизации
with open("last_synced.txt") as f:
    last_synced = f.read().strip()
    print(f"Last synced: {last_synced}")

# Проверка кэша схем
from dbSync.Logic_v2.SchemaCache import SchemaCache
cache = SchemaCache()
mapping = cache.get("abc123...")
print(f"Mapping: {mapping}")
```

### Мониторинг активных синхронизаций

```python
from dbSync.Runner import _active_schedulers

print(f"Active devices: {list(_active_schedulers.keys())}")
for device_id, scheduler in _active_schedulers.items():
    jobs = scheduler.get_jobs()
    print(f"Device {device_id}: {len(jobs)} jobs")
    for job in jobs:
        print(f"  - {job.id}: next run at {job.next_run_time}")
```

---

## Рекомендации по использованию

### 1. Настройка интервалов

- **Высокочастотная синхронизация** (реальное время):
  ```python
  scheduler_sender_timeout = 10    # 10 секунд
  scheduler_receiver_timeout = 15  # 15 секунд
  ```

- **Низкочастотная синхронизация** (экономия ресурсов):
  ```python
  scheduler_sender_timeout = 300   # 5 минут
  scheduler_receiver_timeout = 600 # 10 минут
  ```

### 2. Обработка больших объемов данных

- Используйте batch операции в `SyncManager.bulk_process()`
- Разбивайте большие списки команд на чанки
- Настройте `max_commands_per_push` в конфигурации

### 3. Отладка

- Включите подробное логирование:
  ```python
  logging.getLogger("sync").setLevel(logging.DEBUG)
  ```

- Проверяйте diagnostic logger:
  ```python
  diagnostic_logger.log_debug("Step details", {...})
  ```

### 4. Производительность

- Увеличьте `base_delay` для RetryManager при высокой нагрузке
- Используйте WebSocket вместо HTTP для real-time синхронизации
- Настройте индексы в БД для ускорения запросов

### 5. Безопасность

- Регулярно обновляйте JWT токены
- Используйте HTTPS в production
- Храните ключи шифрования в безопасном месте (env variables)

---

## Troubleshooting

### Проблема: Команды не отправляются

**Симптомы**: Команды накапливаются в `command_queue.json` со статусом "pending".

**Решение**:
1. Проверьте, запущен ли scheduler:
   ```python
   device_id in _active_schedulers
   ```
2. Проверьте доступность сервера:
   ```bash
   curl http://server:8000/sync/push
   ```
3. Проверьте логи на наличие ошибок:
   ```bash
   tail -f logs/sync.log | grep ERROR
   ```

### Проблема: Дублирование записей

**Симптомы**: Одна и та же запись создается несколько раз.

**Решение**:
1. Проверьте дедупликацию в `@sync_aware`
2. Убедитесь, что `id`/`index` передается корректно
3. Проверьте фильтрацию дубликатов в `SyncProcessor.process_push()`

### Проблема: IntegrityError при синхронизации

**Симптомы**: Ошибка `UNIQUE constraint failed`.

**Решение**:
- Обработка реализована автоматически через upsert
- Если ошибка повторяется, проверьте constraint'ы в БД

### Проблема: Команды переходят в "failed"

**Симптомы**: После 4320 попыток команда помечается как "failed".

**Решение**:
1. Проверьте причину в логах
2. Исправьте проблему на сервере
3. Вручную переведите команду обратно в "pending":
   ```python
   queue._update_status(command_id, "pending")
   ```

---

## Заключение

Система синхронизации AutoSklad представляет собой полнофункциональную двустороннюю синхронизацию с:

✅ Автоматическим отслеживанием изменений через декораторы  
✅ Надежной доставкой команд с персистентностью  
✅ Автоматическим согласованием схем  
✅ Разрешением конфликтов  
✅ Повторами при сбоях  
✅ **Интеллектуальной оптимизацией команд (сжатие 30-80%)** 🆕  
✅ **Топологической сортировкой по FK зависимостям** 🆕  
✅ Шифрованием и подписью данных  
✅ Подробным логированием и мониторингом  
✅ **27 автоматическими тестами (unit + integration)** 🆕  

Архитектура позволяет масштабировать систему на множество клиентских устройств с минимальными накладными расходами.

