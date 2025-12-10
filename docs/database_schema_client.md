# Документация структуры базы данных AutoSklad (client)

> Локальная SQLite, создаётся скриптом `client/DB/Create_db.py`. Клиентская схема — **подмножество** серверной: в ней нет таблиц устройств, связок с устройствами, настроек и очередей синхронизации.

## Что есть в клиентской БД (по `client/DB/Create_db.py`)

- Пользователи и доступ: `User`, `Role`, `Rights`, `Page`, `Identification`
- Справочники и статусы: `Help`, `Error`, `History`, `Status`, `Group`, `Plan`, `PlanToolTypes`
- Инструменты и ячейки: `ToolTypes`, `Tools`, `Cell`
- Операции выдачи/приёма: `Load`, `MassLoad`, `LoadOperations`, `OperationsConsumption`
- Операции возврата/списания: `Drop`, `MassDrop`, `DropOperations`, `Consumption`

## Чего нет (только на сервере)

`Device`, `DeviceDefaults`, `ToolLocation`, `ToolsHasDevice`, `LoadOperationsHasDevice`, `DropOperationsHasDevice`, `MassLoadHasDevice`, `MassDropHasDevice`, `Command`, `Settings` и прочие таблицы, связанные с устройствами и синхронизацией.

---

## Описание таблиц (клиентская выборка)

### User (Пользователи)
- Поля: `id`, `barcode`, `code`, `first_name`, `second_name`, `family`, `password`, `role_id`
- Связи: многие-к-одному `Role`; используется в `Identification`, `History`

### Role (Роли)
- Поля: `id`, `name`, `description`, `parent_role_id`
- Связи: самоссылка по иерархии; один-ко-многим `User`, `Rights`

### Rights (Права доступа)
- Поля: `id`, `name`, `description`, `role_id`, `page_id`
- Связи: многие-к-одному `Role`, `Page`

### Page (Страницы)
- Поля: `id`, `name`, `description`
- Связи: один-ко-многим `Rights`

### Identification (Идентификация)
- Поля: `id`, `datetime`, `status`, `description`, `user_id`
- Связи: многие-к-одному `User`

### Help (Подсказки)
- Поля: `id`, `title`, `description`, `status`

### Error (Ошибки)
- Поля: `id`, `datetime`, `description`, `code`, `stacktrace`, `user_id`
- Связи: многие-к-одному `User`

### History (История действий)
- Поля: `id`, `datetime`, `description`, `user_id`, `role_id`, `status_id`
- Связи: многие-к-одному `User`, `Role`, `Status`; опционально ссылки на `ToolTypes`/`Tools`/`Cell`

### Status (Статусы)
- Поля: `id`, `stype`, `description`
- Связи: один-ко-многим `History`, `Load`, `Drop`, `MassLoad`, `MassDrop`, `Cell`, `LoadOperations`, `DropOperations`

### Group (Группы инструментов)
- Поля: `id`, `name`, `parent_id` (если поддерживается)
- Связи: один-ко-многим `ToolTypes`, `Tools`, `Cell`, `Consumption`

### Plan (Планы)
- Поля: `id`, `name`, `description`
- Связи: используется через `PlanToolTypes`

### PlanToolTypes (Плановые типы инструментов)
- Поля: `id`, `plan_id`, `tool_type_id`, дополнительные плановые атрибуты
- Связи: многие-к-одному `Plan`, `ToolTypes`

### ToolTypes (Типы инструментов)
- Поля: `id`, `name`, `description`, `groups_id`, габариты/штрихкоды при наличии
- Связи: многие-к-одному `Group`; один-ко-многим `Tools`, `PlanToolTypes`

### Tools (Инструменты)
- Поля: `id`, `tool_types_id`, `serial`/`inventory_number`, `status_id`, `cell_id`, `groups_id`, `plan_id`
- Связи: многие-к-одному `ToolTypes`, `Status`, `Cell`, `Group`, (опц.) `Plan`

### Cell (Ячейки)
- Поля: `id`, `number`, `status_id`, `tools_id`, `groups_id`, `description`
- Связи: многие-к-одному `Status`, `Tools`, `Group`

### Load (Загрузка/выдача)
- Поля: `id`, `user_id`, `status_id`, `datetime`, `description`
- Связи: многие-к-одному `User`, `Status`

### MassLoad (Массовая загрузка)
- Поля: `id`, `user_id`, `status_id`, `datetime`, `description`
- Связи: многие-к-одному `User`, `Status`

### LoadOperations (Операции загрузки)
- Поля: `id`, `load_id`, `tools_id`, `cell_id`, `status_id`, `quantity`
- Связи: многие-к-одному `Load`, `Tools`, `Cell`, `Status`

### OperationsConsumption (Списание при операциях)
- Поля: `id`, `load_operations_id`, `consumption_id`, `quantity`
- Связи: многие-к-одному `LoadOperations`, `Consumption`

### Drop (Возврат/сдача)
- Поля: `id`, `user_id`, `status_id`, `datetime`, `description`
- Связи: многие-к-одному `User`, `Status`

### MassDrop (Массовый возврат)
- Поля: `id`, `user_id`, `status_id`, `datetime`, `description`
- Связи: многие-к-одному `User`, `Status`

### DropOperations (Операции возврата)
- Поля: `id`, `drop_id`, `tools_id`, `cell_id`, `status_id`, `quantity`
- Связи: многие-к-одному `Drop`, `Tools`, `Cell`, `Status`

### Consumption (Потребление инструмента)
- Поля: `id`, `name`, `description`, `quantity`, `groups_id`
- Связи: многие-к-одному `Group`; связана через `OperationsConsumption`

---

## Структура базы данных (только клиент)

### Пользователи и доступ
- **User** — `id`, `barcode`, `code`, `first_name`, `second_name`, `family`, `password`, `role_id`; m:1 `Role`; 1:m `Identification`, `History`, `Load`, `Drop`.
- **Role** — `id`, `name`, `description`, `parent_role_id`; самоссылка; 1:m `User`, 1:m `Rights`.
- **Rights** — `id`, `name`, `description`, `role_id`, `page_id`; m:1 `Role`, m:1 `Page`.
- **Page** — `id`, `name`, `description`; 1:m `Rights`.
- **Identification** — `id`, `datetime`, `status`, `description`, `user_id`; m:1 `User`.

### Справочники и статусы
- **Status** — `id`, `stype`, `description`; 1:m `History`, `Load`, `Drop`, `MassLoad`, `MassDrop`, `Cell`, `LoadOperations`, `DropOperations`.
- **Help** — `id`, `title`, `description`, `status`.
- **Error** — `id`, `datetime`, `description`, `code`, `stacktrace`, `user_id`; m:1 `User`.
- **History** — `id`, `datetime`, `description`, `user_id`, `role_id`, `status_id`; m:1 `User`, `Role`, `Status`; (опц.) ссылки на `ToolTypes`/`Tools`/`Cell`.
- **Group** — `id`, `name`, `description`, `paren_group_id`; 1:m `ToolTypes`, 1:m `Tools`, 1:m `Cell`, 1:m `Consumption`.
- **Plan** — `id`, `name`, `description`; 1:m `PlanToolTypes`.
- **PlanToolTypes** — `id`, `plan_id`, `tool_type_id`; m:1 `Plan`, m:1 `ToolTypes`.

### Инструменты и ячейки
- **ToolTypes** — `id`, `name`, `description`, `groups_id`; m:1 `Group`; 1:m `Tools`; участвуют в `PlanToolTypes`.
- **Tools** — `id`, `tool_types_id`, `serial`/`inventory_number`, `status_id`, `cell_id`, `groups_id`, `plan_id`; m:1 `ToolTypes`, m:1 `Group`, m:1 `Status`, m:1 `Plan` (если задан); участвуют в `LoadOperations`, `DropOperations`, связаны с `Cell`.
- **Cell** — `id`, `number`, `status_id`, `tools_id`, `groups_id`, `description`; m:1 `Status`, m:1 `Tools`, m:1 `Group`; используется в операциях загрузки/возврата.

### Операции загрузки / возврата и расходники
- **Load** — `id`, `user_id`, `status_id`, `datetime`, `description`; m:1 `User`, m:1 `Status`; 1:m `LoadOperations`.
- **MassLoad** — `id`, `user_id`, `status_id`, `datetime`, `description`; m:1 `User`, m:1 `Status`.
- **LoadOperations** — `id`, `load_id`, `tools_id`, `cell_id`, `status_id`, `quantity`; m:1 `Load`, `Tools`, `Cell`, `Status`; 1:m `OperationsConsumption`.
- **OperationsConsumption** — `id`, `load_operations_id`, `consumption_id`, `quantity`; m:1 `LoadOperations`, m:1 `Consumption`.
- **Consumption** — `id`, `name`, `description`, `quantity`, `groups_id`; m:1 `Group`; 1:m в `OperationsConsumption`.
- **Drop** — `id`, `user_id`, `status_id`, `datetime`, `description`; m:1 `User`, m:1 `Status`; 1:m `DropOperations`.
- **MassDrop** — `id`, `user_id`, `status_id`, `datetime`, `description`; m:1 `User`, m:1 `Status`.
- **DropOperations** — `id`, `drop_id`, `tools_id`, `cell_id`, `status_id`, `quantity`; m:1 `Drop`, `Tools`, `Cell`, `Status`.

### Ключевые связи (текстовая диаграмма)
- User → Role (m:1); User → Identification/History/Load/Drop (1:m)
- Role → Rights (1:m); Rights → Page (m:1)
- Group → ToolTypes/Tools/Cell/Consumption (1:m)
- ToolTypes → Tools (1:m); ToolTypes ↔ PlanToolTypes (1:m / m:1)
- Tools → LoadOperations/DropOperations (1:m); Tools → Cell (m:1)
- Cell → LoadOperations/DropOperations (m:1); Status → Cell/Load/Drop/... (1:m)
- Load → LoadOperations (1:m) → OperationsConsumption (1:m) → Consumption (m:1)
- Drop → DropOperations (1:m)

---

Если таблицы не указаны выше — их нет в клиентской БД.

