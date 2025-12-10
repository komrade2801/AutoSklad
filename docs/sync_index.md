# Индекс документации системы синхронизации

Быстрый поиск по ключевым темам и компонентам.

---

## 🔍 Поиск по компонентам

### Runner
- [Описание и назначение](sync_system_architecture.md#1-runner-точка-входа)
- [Инициализация (server)](sync_system_examples.md#server-инициализация-для-нескольких-устройств)
- [Инициализация (client)](sync_system_examples.md#client-инициализация)
- [Диаграмма последовательности](sync_system_sequence_diagrams.md#сценарий-пользователь-добавляет-инструмент)

### @sync_aware декоратор
- [Описание и принцип работы](sync_system_architecture.md#2-декоратор-sync_aware)
- [Примеры использования](sync_system_examples.md#примеры-crud-операций-с-синхронизацией)
- [Код](server/dbSync/decorators.py)

### CommandQueue
- [Описание и структура](sync_system_architecture.md#3-commandqueue-очередь-команд)
- [Проверка состояния](sync_system_examples.md#1-проверка-состояния-очереди)
- [Troubleshooting](sync_system_examples.md#проблема-1-команды-накапливаются-в-pending)

### CommandSender (Push)
- [Описание процесса](sync_system_architecture.md#4-commandsender-отправка-команд)
- [Диаграмма последовательности](sync_system_sequence_diagrams.md#push---отправка-локальных-изменений)
- [API endpoint](sync_system_api.md#2-push-отправка-локальных-изменений)

### CommandReceiver (Pull)
- [Описание процесса](sync_system_architecture.md#5-commandreceiver-получение-команд)
- [Диаграмма последовательности](sync_system_sequence_diagrams.md#pull---получение-удаленных-изменений)
- [API endpoint](sync_system_api.md#3-pull-получение-удаленных-изменений)

### CommandOrderer
- [Описание оптимизации команд](sync_system_architecture.md#55-commandorderer-оптимизация-команд)
- [Сжатие последовательностей](sync_system_architecture.md#сжатие-последовательностей)
- [Топологическая сортировка](sync_system_architecture.md#топологическая-сортировка)
- [Валидация FK зависимостей](sync_system_architecture.md#проверка-fk-зависимостей)

### SyncProcessor
- [Описание координатора](sync_system_architecture.md#6-syncprocessor-центральный-координатор)
- [process_schema (Handshake)](sync_system_architecture.md#61-process_schema-handshake)
- [prepare_pull](sync_system_architecture.md#62-prepare_pull-подготовка-команд-для-клиента)
- [process_push](sync_system_architecture.md#63-process_push-применение-команд-от-клиента)

### BatchProcessor
- [Описание пакетной обработки](sync_system_architecture.md#7-batchprocessor-пакетная-обработка)
- [Атомарность транзакций](sync_system_architecture.md#ключевые-особенности)

### SyncManager
- [Описание CRUD-фасада](sync_system_architecture.md#8-syncmanager-crud-фасад)
- [_handle_insert](sync_system_architecture.md#82-_handle_insert)
- [_handle_update](sync_system_architecture.md#83-_upsert_update)

### RetryManager
- [Описание и стратегия](sync_system_architecture.md#9-retrymanager-повторы)
- [Диаграмма обработки ошибок](sync_system_sequence_diagrams.md#обработка-ошибок-и-повторы)
- [Troubleshooting](sync_system_examples.md#проблема-3-команды-переходят-в-failed)

### TransportService
- [Описание транспортного слоя](sync_system_architecture.md#10-transportservice-транспортный-слой)
- [Безопасность](sync_system_api.md#аутентификация-и-безопасность)
- [Примеры использования](sync_system_api.md#примеры-запросов)

### DataMapper
- [Описание маппинга полей](sync_system_architecture.md#11-datamapper-маппинг-полей)
- [Примеры mapping](sync_system_architecture.md#пример-mapping)

### DataTransformer
- [Описание трансформации](sync_system_architecture.md#12-datatransformer-трансформация-данных)
- [Регистрация правил](sync_system_examples.md#создание-кастомных-правил-трансформации)

### ConflictManager
- [Описание разрешения конфликтов](sync_system_architecture.md#14-conflictmanager-разрешение-конфликтов)
- [Кастомные стратегии](sync_system_examples.md#2-кастомная-стратегия-разрешения-конфликтов)
- [Обнаружение конфликтов](sync_system_examples.md#3-обнаружение-и-логирование-конфликтов)

---

## 🔍 Поиск по темам

### Установка и настройка
- [Быстрый старт](README_SYNC.md#быстрый-старт)
- [Server конфигурация](sync_system_architecture.md#server-serveroptions)
- [Client конфигурация](sync_system_architecture.md#client-clientconfig)
- [Инициализация БД sync.db](sync_system_architecture.md#база-данных-синхронизации-syncdb)

### Handshake (согласование схем)
- [Описание процесса](sync_system_architecture.md#handshake)
- [Диаграмма (первый запрос)](sync_system_sequence_diagrams.md#инициация-handshake-первый-запрос)
- [Диаграмма (кэширование)](sync_system_sequence_diagrams.md#повторный-запрос-mapping-в-кэше)
- [API endpoint](sync_system_api.md#1-handshake-согласование-схем)
- [Примеры](sync_system_api.md#1-handshake)

### Push (отправка изменений)
- [Описание процесса](sync_system_architecture.md#push-процесс)
- [Полная диаграмма](sync_system_sequence_diagrams.md#сценарий-пользователь-добавляет-инструмент)
- [API endpoint](sync_system_api.md#2-push-отправка-локальных-изменений)
- [Примеры запросов](sync_system_api.md#2-push)

### Pull (получение изменений)
- [Описание процесса](sync_system_architecture.md#pull-процесс)
- [Полная диаграмма](sync_system_sequence_diagrams.md#сценарий-сервер-изменяет-ячейку-клиент-получает-обновление)
- [API endpoint](sync_system_api.md#3-pull-получение-удаленных-изменений)
- [Граница синхронизации](sync_system_architecture.md#граница-синхронизации)

### CRUD операции
- [INSERT с синхронизацией](sync_system_examples.md#1-добавление-инструмента-insert)
- [UPDATE с синхронизацией](sync_system_examples.md#2-обновление-ячейки-update)
- [DELETE с синхронизацией](sync_system_examples.md#3-удаление-записи-delete)
- [Операции БЕЗ синхронизации](sync_system_examples.md#4-операция-без-синхронизации-sync_context)
- [Инкрементальные операции](sync_system_examples.md#5-инкрементальные-операции-специальная-обработка-count)

### Безопасность
- [JWT токены](sync_system_api.md#jwt-token)
- [HMAC подпись](sync_system_api.md#hmac-signature)
- [AES шифрование](sync_system_api.md#aes-encryption)
- [Полный цикл](sync_system_architecture.md#полный-цикл-безопасности)

### Обработка ошибок
- [Стратегия повторов](sync_system_architecture.md#стратегия-повторов)
- [IntegrityError](sync_system_architecture.md#обработка-integrityerror-race-condition)
- [Сетевые ошибки](sync_system_architecture.md#обработка-сетевых-ошибок)
- [Диаграмма ошибок](sync_system_sequence_diagrams.md#сценарий-сетевая-ошибка-при-отправке-команды)
- [Превышение max_retries](sync_system_sequence_diagrams.md#сценарий-превышение-max_retries)

### Конфликты
- [Типы конфликтов](sync_system_architecture.md#типы-конфликтов)
- [Стратегии разрешения](sync_system_architecture.md#стратегии)
- [Кастомные стратегии](sync_system_examples.md#2-кастомная-стратегия-разрешения-конфликтов)
- [Диаграмма конфликтов](sync_system_sequence_diagrams.md#сценарий-одновременные-изменения-на-клиенте-и-сервере)
- [Правильный подход](sync_system_sequence_diagrams.md#правильный-сценарий-с-инкрементальными-операциями)

### Трансформация данных
- [Обогащение Tools](sync_system_architecture.md#специальные-правила-из-setuppy)
- [Нормализация Cell](sync_system_architecture.md#2-cell-incoming-нормализация-id)
- [Извлечение status из History](sync_system_architecture.md#3-history-incoming-извлечение-status-из-вложенного-объекта)
- [Кастомные правила](sync_system_examples.md#создание-кастомных-правил-трансформации)
- [Валидация](sync_system_examples.md#3-валидация-данных)

### Мониторинг
- [Проверка очереди](sync_system_examples.md#1-проверка-состояния-очереди)
- [Активные синхронизации](sync_system_examples.md#2-мониторинг-активных-синхронизаций)
- [Анализ логов](sync_system_examples.md#3-анализ-логов)
- [Dashboard API](sync_system_examples.md#4-dashboard-для-мониторинга-fastapi-endpoint)
- [Метрики](sync_system_architecture.md#метрики-syncmonitor)

### Troubleshooting
- [Команды в pending](sync_system_examples.md#проблема-1-команды-накапливаются-в-pending)
- [Дублирование записей](sync_system_examples.md#проблема-2-дублирование-записей)
- [Команды в failed](sync_system_examples.md#проблема-3-команды-переходят-в-failed)
- [IntegrityError](sync_system_examples.md#проблема-4-integrityerror-при-синхронизации)
- [Конфликты данных](sync_system_examples.md#проблема-5-конфликты-при-одновременных-изменениях)

---

## 🔍 Поиск по API

### HTTP Endpoints
- [POST /sync/handshake](sync_system_api.md#1-handshake-согласование-схем)
- [POST /sync/push](sync_system_api.md#2-push-отправка-локальных-изменений)
- [GET /sync/pull](sync_system_api.md#3-pull-получение-удаленных-изменений)

### Структуры данных
- [Command](sync_system_api.md#command-команда-синхронизации)
- [Schema](sync_system_api.md#schema-схема-базы-данных)
- [Mapping](sync_system_api.md#mapping-маппинг-полей)
- [CommandStatus](sync_system_api.md#commandstatus-статус-команды)

### Коды ошибок
- [HTTP Status Codes](sync_system_api.md#http-status-codes)
- [Application Error Codes](sync_system_api.md#application-error-codes)

### Примеры запросов
- [Python (TransportService)](sync_system_api.md#python-с-использованием-transportservice)
- [JavaScript (Node.js)](sync_system_api.md#javascript-nodejs)
- [cURL с шифрованием](sync_system_api.md#curl-с-шифрованием-bash-скрипт)
- [WebSocket API](sync_system_api.md#websocket-api-опционально)

---

## 🔍 Поиск по сценариям

### Первый запуск
1. [Настройка конфигурации](README_SYNC.md#конфигурация)
2. [Запуск сервера](sync_system_examples.md#server-инициализация-для-нескольких-устройств)
3. [Запуск клиента](sync_system_examples.md#client-инициализация)
4. [Handshake](sync_system_sequence_diagrams.md#handshake---согласование-схем)
5. [Проверка работоспособности](README_SYNC.md#проверка-работоспособности)

### Добавление нового CRUD класса
1. [Создание CRUD с @sync_aware](sync_system_examples.md#1-добавление-инструмента-insert)
2. [Регистрация в crud_registry](sync_system_architecture.md#syncmanager)
3. [Настройка трансформации](sync_system_examples.md#создание-кастомных-правил-трансформации)
4. [Тестирование](sync_system_examples.md#примеры-crud-операций-с-синхронизацией)

### Отладка проблем
1. [Проверка логов](README_SYNC.md#проверка-логов)
2. [Проверка очереди](README_SYNC.md#проверка-очереди)
3. [Проверка синхронизации](README_SYNC.md#проверка-синхронизации)
4. [Типичные проблемы](sync_system_examples.md#типичные-проблемы-и-решения)

### Настройка кастомного поведения
1. [Правила трансформации](sync_system_examples.md#создание-кастомных-правил-трансформации)
2. [Стратегии конфликтов](sync_system_examples.md#обработка-конфликтов)
3. [Валидация](sync_system_examples.md#3-валидация-данных)
4. [Мониторинг](sync_system_examples.md#мониторинг-и-диагностика)

---

## 🔍 Поиск по файлам

### Исходный код (Server)
```
server/
├── main.py                              # Точка входа сервера
├── options.py                           # Конфигурация
└── dbSync/
    ├── Runner.py                        # Запуск синхронизации
    ├── setup.py                         # Инициализация компонентов
    ├── decorators.py                    # @sync_aware декоратор
    ├── sync_db.py                       # Управление БД sync.db
    ├── Transport/
    │   └── TransportService.py          # HTTP клиент с шифрованием
    ├── Logic_v2/
    │   ├── CommandQueue.py              # Очередь команд
    │   ├── CommandSender.py             # Push процесс
    │   ├── CommandReceiver.py           # Pull процесс
    │   ├── CommandOrderer.py            # 🆕 Оптимизация команд
    │   ├── SyncProcessor.py             # Центральный координатор
    │   ├── BatchProcessor.py            # Пакетная обработка
    │   ├── SyncManager.py               # CRUD фасад
    │   ├── RetryManager.py              # Повторы
    │   ├── DataMapper.py                # Маппинг полей
    │   ├── DataTransformer.py           # Трансформация данных
    │   ├── ConflictManager.py           # Разрешение конфликтов
    │   ├── SchemaAnalyzer.py            # Анализ схем
    │   ├── SchemaCache.py               # Кэширование схем
    │   ├── DiagnosticLogger.py          # Логирование
    │   ├── SyncMonitor.py               # Метрики
    │   ├── JSONSchemaValidator.py       # Валидация JSON
    │   └── tests/                       # 🆕 Unit и integration тесты
    │       ├── test_CommandOrderer.py   # 18 unit-тестов
    │       └── test_SyncIntegration.py  # 9 integration-тестов
    └── Engines/
        ├── CommandEngine.py             # CRUD для Command
        ├── RecordEngine.py              # CRUD для Record
        ├── CommandStatusEngine.py       # CRUD для CommandStatus
        └── SyncConfigEngine.py          # CRUD для SyncConfig
```

### Исходный код (Client)
```
client/
├── main.py                              # Точка входа клиента
├── config.json                          # Конфигурация
└── dbSync/
    └── (аналогично server/dbSync/)
```

### Файлы данных
```
command_queue.json                       # Очередь команд
last_synced.txt                          # Граница синхронизации
sync.db                                  # БД синхронизации
logs/sync.log                            # Логи
```

### Документация
```
docs/
├── README_SYNC.md                       # Главная страница
├── sync_index.md                        # Этот индекс
├── sync_system_architecture.md          # Архитектура
├── sync_system_sequence_diagrams.md     # Диаграммы
├── sync_system_examples.md              # Примеры
├── sync_system_api.md                   # API
├── sync_fixes.md                        # 🆕 План исправлений
└── manual_testing_guide.md              # 🆕 Руководство по тестированию
```

---

## 📌 Быстрые ссылки

### Основные документы
- [Главная страница](README_SYNC.md)
- [Архитектура](sync_system_architecture.md)
- [Диаграммы](sync_system_sequence_diagrams.md)
- [Примеры](sync_system_examples.md)
- [API](sync_system_api.md)

### Быстрый старт
- [Минимальная настройка](README_SYNC.md#минимальная-настройка)
- [Проверка работоспособности](README_SYNC.md#проверка-работоспособности)

### Помощь
- [Типичные проблемы](sync_system_examples.md#типичные-проблемы-и-решения)
- [Диагностика](README_SYNC.md#диагностика)
- [Глоссарий](README_SYNC.md#глоссарий)

---

**Последнее обновление**: 2024-01-15  
**Версия индекса**: 1.0

