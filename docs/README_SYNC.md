# Документация системы синхронизации AutoSklad

Добро пожаловать в документацию системы синхронизации AutoSklad - полнофункциональной двусторонней системы синхронизации данных между центральным сервером и множеством клиентских устройств.

## 📚 Содержание документации

### 1. [Архитектура системы синхронизации](sync_system_architecture.md)
**Основной документ** - полное описание архитектуры, компонентов и принципов работы.

**Содержание**:
- Общая архитектура и диаграммы
- Детальное описание всех компонентов:
  - Runner (точка входа)
  - @sync_aware декоратор
  - CommandQueue (очередь команд)
  - CommandSender (Push-процесс)
  - CommandReceiver (Pull-процесс)
  - CommandOrderer (оптимизация команд) 🆕
  - SyncProcessor (центральный координатор)
  - BatchProcessor (пакетная обработка)
  - SyncManager (CRUD-фасад)
  - RetryManager (повторы)
  - TransportService (транспортный слой)
  - DataMapper и DataTransformer
  - ConflictManager (разрешение конфликтов)
- Жизненный цикл синхронизации
- Протоколы и форматы данных
- Обработка ошибок и повторы
- Безопасность (JWT, HMAC, AES)
- Конфигурация
- Диагностика и мониторинг

### 2. [Диаграммы последовательностей](sync_system_sequence_diagrams.md)
Визуальное представление потоков данных в системе.

**Содержание**:
- Handshake - согласование схем
- Push - отправка локальных изменений (полный цикл)
- Pull - получение удаленных изменений
- Обработка ошибок и повторы
- Полный цикл двусторонней синхронизации
- Диаграмма компонентов и взаимодействия

### 3. [Примеры использования](sync_system_examples.md)
Практические примеры и решение типичных проблем.

**Содержание**:
- Настройка синхронизации (server и client)
- Примеры CRUD операций с синхронизацией:
  - Добавление инструмента (INSERT)
  - Обновление ячейки (UPDATE)
  - Удаление записи (DELETE)
  - Операции БЕЗ синхронизации
  - Инкрементальные операции
- Создание кастомных правил трансформации:
  - Обогащение исходящих данных
  - Нормализация входящих данных
  - Валидация данных
- Обработка конфликтов:
  - Настройка ConflictManager
  - Кастомные стратегии
  - Обнаружение и логирование
- Мониторинг и диагностика:
  - Проверка состояния очереди
  - Мониторинг активных синхронизаций
  - Анализ логов
  - Dashboard для мониторинга
- Типичные проблемы и решения:
  - Команды накапливаются в pending
  - Дублирование записей
  - Команды переходят в failed
  - IntegrityError при синхронизации
  - Конфликты при одновременных изменениях

### 4. [API документация](sync_system_api.md)
Описание HTTP API для синхронизации.

**Содержание**:
- Общая информация (Base URL, Content-Type)
- Аутентификация и безопасность (JWT, HMAC, AES)
- Endpoints:
  - POST /sync/handshake - согласование схем
  - POST /sync/push - отправка локальных изменений
  - GET /sync/pull - получение удаленных изменений
- Структуры данных (Command, Schema, Mapping, CommandStatus)
- Коды ошибок (HTTP и application-level)
- Примеры запросов:
  - Python (TransportService)
  - JavaScript (Node.js)
  - cURL с шифрованием
  - WebSocket API (опционально)

---

## 🚀 Быстрый старт

### Минимальная настройка

**Server** (`server/main.py`):
```python
from dbSync.Runner import start_sync, stop_sync

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск синхронизации для устройства
    start_sync(
        device_id=1,
        host="192.168.1.101",
        port=8001,
        token="<JWT_TOKEN>",
        secret=b"supersecret",
        aes=b"16byteslongkey!!",
        scheduler_sender_timeout=60,
        scheduler_receiver_timeout=120
    )
    
    yield
    
    stop_sync(1)
```

**Client** (`client/main.py`):
```python
from dbSync.Runner import start_sync, stop_sync
from Core.sync_config import SyncConfig

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = SyncConfig()
    
    start_sync(
        device_id=cfg.device_id,
        host=cfg.ip,
        port=cfg.port,
        token=cfg.token,
        secret=cfg.secret,
        aes=cfg.aes,
        scheduler_sender_timeout=cfg.sender_timeout,
        scheduler_receiver_timeout=cfg.receiver_timeout
    )
    
    yield
    
    stop_sync(cfg.device_id)
```

**CRUD с синхронизацией**:
```python
from dbSync.decorators import sync_aware
from DB.BaseCRUD import BaseCRUD

class EngineTools(BaseCRUD):
    @sync_aware
    def add(self, **kwargs):
        # Автоматически создаст команду синхронизации
        tool = Tools(**kwargs)
        self.session.add(tool)
        self.session.commit()
        return tool
```

### Проверка работоспособности

```python
# Проверка состояния очереди
from dbSync.Logic_v2.CommandQueue import CommandQueue

queue = CommandQueue()
pending = queue.get_pending_commands()
print(f"Pending: {len(pending)}")

# Проверка активных синхронизаций
from dbSync.Runner import _active_schedulers
print(f"Active devices: {list(_active_schedulers.keys())}")

# Проверка последней синхронизации
with open("last_synced.txt") as f:
    print(f"Last synced: {f.read().strip()}")
```

---

## 🏗️ Архитектура (краткий обзор)

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT DEVICE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Application → @sync_aware → CommandQueue → CommandSender       │
│                                                ↓                  │
│                                         TransportService          │
│                                                ↓                  │
│                                    (HTTP + AES + HMAC)            │
│                                                ↓                  │
│                                         Server API                │
│                                                ↓                  │
│                                       SyncProcessor               │
│                                                ↓                  │
│                                      BatchProcessor               │
│                                                ↓                  │
│                                        Database                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Ключевые особенности

✅ **Двусторонняя синхронизация**: Push и Pull процессы  
✅ **Автоматическое отслеживание изменений**: Декоратор @sync_aware  
✅ **Надежная доставка**: Персистентная очередь с повторами  
✅ **Согласование схем**: Автоматический handshake  
✅ **Разрешение конфликтов**: Настраиваемые стратегии  
✅ **Оптимизация команд**: Сжатие и упорядочивание (CommandOrderer) 🆕  
✅ **Безопасность**: JWT + HMAC-SHA256 + AES-CBC  
✅ **Атомарность**: Пакетная обработка в транзакциях  
✅ **Мониторинг**: Логи, метрики, диагностика  

---

## 📊 Потоки данных

### 1. Local Changes (Client → Server)
```
CRUD Operation → @sync_aware → CommandQueue → 
CommandSender → TransportService → Server → Database
```

**Время**: ~60 секунд (scheduler_sender_timeout)

### 2. Remote Changes (Server → Client)
```
Server Database → CommandQueue → CommandReceiver (periodic) → 
TransportService → SyncProcessor → Database
```

**Время**: ~120 секунд (scheduler_receiver_timeout)

### 3. Handshake (согласование схем)
```
Client → send_schema → Server → generate_mapping → 
SchemaCache → Client (mapping + schema_hash)
```

**Время**: При первом запросе (~1-2 секунды)

---

## 🔧 Конфигурация

### Server (`server/options.py`)
```python
Host = "0.0.0.0"
port = 8000

RECEIVER_TIMEOUT = 120  # Pull interval (seconds)
SENDER_TIMEOUT = 60     # Push interval (seconds)

AES_KEY = b"16byteslongkey!!"  # 16/24/32 bytes
HMAC_SECRET = b"supersecret"
```

### Client (`client/config.json`)
```json
{
  "device_id": 1,
  "network": {"ip": "192.168.1.101", "port": 8001},
  "server": {"ip": "192.168.1.10", "port": 8000},
  "sync": {
    "token": "<JWT_TOKEN>",
    "secret": "supersecret",
    "aes_key": "16byteslongkey!!",
    "sender_timeout": 60,
    "receiver_timeout": 120
  }
}
```

---

## 🐛 Диагностика

### Проверка логов
```bash
# Server
tail -f server/logs/sync.log | grep ERROR

# Client
tail -f client/logs/sync.log | grep ERROR
```

### Проверка очереди
```bash
# Посмотреть command_queue.json
cat command_queue.json | python -m json.tool
```

### Проверка синхронизации
```bash
# Посмотреть last_synced.txt
cat last_synced.txt
```

### Скрипты для мониторинга
См. [Примеры использования - Мониторинг и диагностика](sync_system_examples.md#мониторинг-и-диагностика)

---

## 📖 Глоссарий

**@sync_aware** - Декоратор для CRUD-методов, автоматически создающий команды синхронизации  
**CommandQueue** - Персистентная очередь команд (JSON-файл)  
**CommandSender** - Компонент Push-процесса (отправка команд)  
**CommandReceiver** - Компонент Pull-процесса (получение команд)  
**SyncProcessor** - Центральный координатор синхронизации  
**BatchProcessor** - Атомарная пакетная обработка операций  
**SyncManager** - Фасад для CRUD-операций  
**RetryManager** - Управление повторными попытками  
**TransportService** - HTTP-клиент с шифрованием  
**DataMapper** - Маппинг полей между схемами  
**DataTransformer** - Бизнес-правила трансформации  
**ConflictManager** - Обнаружение и разрешение конфликтов  
**Handshake** - Согласование схемы между клиентом и сервером  
**Push** - Отправка локальных изменений на сервер  
**Pull** - Получение изменений с сервера  
**sync_context** - Флаг контекста синхронизации (True = команда из синхронизации)  

---

## 🔗 Дополнительные ресурсы

### Файлы кода

**Server**:
- `server/dbSync/Runner.py` - Запуск синхронизации
- `server/dbSync/setup.py` - Инициализация компонентов
- `server/dbSync/decorators.py` - Декоратор @sync_aware
- `server/dbSync/Logic_v2/` - Все компоненты синхронизации

**Client**:
- `client/dbSync/Runner.py` - Запуск синхронизации
- `client/dbSync/decorators.py` - Декоратор @sync_aware
- `client/dbSync/Logic_v2/` - Все компоненты синхронизации

### Базы данных

- `sync.db` - База синхронизации (Command, Record, CommandStatus, SyncConfig)
- `vending.db` / `main.db` - Основная база данных приложения

### Конфигурация

- `command_queue.json` - Очередь команд синхронизации
- `last_synced.txt` - Граница последней синхронизации
- `config.json` (client) - Конфигурация клиента
- `options.py` (server) - Конфигурация сервера

---

## 📝 Changelog

### Version 2.1 (Текущая) 🆕
- ✅ Оптимизация команд (CommandOrderer)
- ✅ Сжатие последовательностей (30-80% экономии)
- ✅ Топологическая сортировка по FK
- ✅ 27 автоматических тестов (unit + integration)

### Version 2.0
- ✅ Двусторонняя синхронизация (Push + Pull)
- ✅ Автоматическое согласование схем (Handshake)
- ✅ Разрешение конфликтов (ConflictManager)
- ✅ Обогащение данных (DataTransformer)
- ✅ Атомарная пакетная обработка (BatchProcessor)
- ✅ Автоматические повторы (RetryManager)
- ✅ Шифрование и подпись (AES + HMAC)
- ✅ Дедупликация операций
- ✅ Автосвязывание (Consumption ↔ History)

### Version 1.0 (Legacy)
- Односторонняя синхронизация
- Ручное согласование схем
- Базовая обработка ошибок

---

## 🤝 Поддержка

Если у вас возникли проблемы или вопросы:

1. Изучите [Примеры использования](sync_system_examples.md) - раздел "Типичные проблемы и решения"
2. Проверьте логи: `logs/sync.log`
3. Проверьте состояние очереди: `command_queue.json`
4. Проверьте конфигурацию: `config.json` / `options.py`

---

## 📄 Лицензия

© 2024 AutoSklad. Все права защищены.

---

**Последнее обновление**: 2024-01-15  
**Версия документации**: 2.0

