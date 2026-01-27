# Стратегии синхронизации для системы AutoSklad

Документ описывает правильные стратегии разрешения конфликтов и приоритеты синхронизации для каждой таблицы в системе с множеством вендинговых аппаратов, работающих в офлайн-режиме.

**ВАЖНО:** Документ исправлен с учетом проблемы, когда данные с клиента стирались при попытке принять массовую выгрузку.

---

## Оглавление

1. [Статусы ячеек](#статусы-ячеек)
2. [Принципы защиты данных](#принципы-защиты-данных)
3. [Стратегии по таблицам](#стратегии-по-таблицам)
4. [Детальная логика для Cell](#детальная-логика-для-cell)
5. [Приоритеты синхронизации](#приоритеты-синхронизации)
6. [План реализации](#план-реализации)

---

## Статусы ячеек

Система использует **8 статусов** для ячеек (таблица `Cell`):

| ID | stype | Описание | Источник | Защита |
|----|-------|----------|----------|--------|
| 1 | `start_system` | Инициализация системы! (пустая ячейка) | Локальный/Сервер | Низкая |
| 2 | `mass_drop_ready` | Инструмент извлечён из аппарата (после массовой выгрузки) | Сервер | Средняя |
| 3 | `mass_load_ready` | Инструмент готов к выдаче (после массовой загрузки) | Локальный/Сервер | **ВЫСОКАЯ** |
| 4 | `mass_drop_init` | Объявлена массовая выгрузка | Сервер | Средняя |
| 5 | `mass_load_init` | Объявлена массовая загрузка | Сервер | Средняя |
| 6 | `drop_ready` | Инструмент извлечён из аппарата (обычная выгрузка) | Локальный/Сервер | Средняя |
| 7 | `load_ready` | Инструмент готов к выдаче (обычная загрузка) | Локальный | **ВЫСОКАЯ** |
| 8 | `consumption` | Инструмент выдан! (статус для History, не для Cell) | Локальный | - |

**Примечание:** `consumption` используется в таблице `History`, а не в `Cell`. При выдаче инструмента ячейка переходит в `status_id=1` (start_system).

---

## Принципы защиты данных

### 1. Локальные активные операции (НЕЛЬЗЯ ЗАТИРАТЬ)

Эти статусы означают, что на клиенте происходит активная операция выдачи инструмента:

- **`load_ready` (7)** — пользователь выбрал инструмент, но еще не получил его (активная операция выдачи)
- **`mass_load_ready` (3)** — инструмент готов к выдаче после массовой загрузки (локальная операция завершена, инструмент доступен для выдачи)

**Правило:** Если локальная ячейка имеет статус `load_ready` (7) или `mass_load_ready` (3), и сервер отправляет другой статус — **сохраняем локальные данные**.

**Исключение:** Если сервер отправляет статус массовой операции (`mass_load_init`, `mass_drop_init`), то принимаем его (это уже реализовано).

---

### 2. Операции с сервера (НУЖНО ПРИНИМАТЬ)

Эти статусы означают массовые операции, инициированные на сервере:

- **`mass_load_init` (5)** — объявлена массовая загрузка (с сервера)
- **`mass_drop_init` (4)** — объявлена массовая выгрузка (с сервера)
- **`mass_load_ready` (3)** — может быть с сервера после завершения массовой загрузки
- **`mass_drop_ready` (2)** — может быть с сервера после завершения массовой выгрузки

**Правило:** Если сервер отправляет статус массовой операции — **принимаем данные с сервера**.

---

### 3. Нейтральные статусы (можно затирать)

- **`start_system` (1)** — пустая ячейка (начальное состояние)
- **`drop_ready` (6)** — инструмент извлечен (обычная выгрузка, не массовая)

**Правило:** Эти статусы можно затирать данными с сервера, если нет активных операций.

---

## Стратегии по таблицам

### Таблица Cell (Ячейки)

**Стратегия:** **STATUS_AWARE_LWW** (Last-Write-Wins с учетом статусов)

**Логика разрешения конфликтов:**

```python
def resolve_cell_conflict(local, remote, **kwargs):
    """
    Разрешает конфликт для таблицы Cell с учетом статусов.
    
    Правила:
    1. Массовые операции с сервера имеют приоритет
    2. Локальные активные операции (load_ready, mass_load_ready) защищены
    3. В остальных случаях — более новая версия
    """
    local_status_id = local.get("status_id")
    remote_status_id = remote.get("status_id")
    remote_status_stype = kwargs.get("remote_status_stype")
    
    # 1. Массовые операции с сервера имеют приоритет
    if remote_status_stype in ("mass_load_init", "mass_load_ready", 
                                "mass_drop_init", "mass_drop_ready"):
        merged = dict(local)
        merged.update(remote)
        return merged
    
    # 2. Защита локальных активных операций
    if local_status_id:
        local_status = get_status_by_id(local_status_id)
        if local_status:
            local_stype = local_status.stype
            
            # Если локальная операция активна — сохраняем локальные данные
            if local_stype in ("load_ready", "mass_load_ready"):
                # НО: если сервер отправляет массовую операцию — принимаем её
                if remote_status_stype not in ("mass_load_init", "mass_drop_init"):
                    return local  # Защищаем локальные данные
    
    # 3. Если удаленная операция активна и локальная нет — принимаем удаленные
    if remote_status_id:
        remote_status = get_status_by_id(remote_status_id)
        if remote_status:
            remote_stype = remote_status.stype
            if remote_stype in ("load_ready", "mass_load_ready"):
                # Проверяем, не активна ли локальная операция
                if local_status_id:
                    local_status = get_status_by_id(local_status_id)
                    if local_status and local_status.stype not in ("load_ready", "mass_load_ready"):
                        return remote  # Принимаем удаленные данные
    
    # 4. В остальных случаях — более новая версия (TIMESTAMP_WINS)
    return resolve_timestamp_wins(local, remote, **kwargs)
```

**Ключевые моменты:**
- `load_ready` (7) и `mass_load_ready` (3) защищены от затирания
- Массовые операции (`mass_load_init`, `mass_drop_init`) принимаются с сервера
- Статусы `start_system` (1) и `drop_ready` (6) можно затирать

---

### Таблицы Load, Drop, MassLoad, MassDrop

**Стратегия:** **STATUS_AWARE_LWW** (аналогично Cell)

**Логика:** Та же, что и для Cell, так как эти таблицы связаны с ячейками и имеют статусы операций.

---

### Таблицы LoadOperations, DropOperations, Consumption, OperationsConsumption

**Стратегия:** **STATUS_AWARE_LWW** (аналогично Cell)

**Логика:** Эти таблицы содержат детали операций и должны синхронизироваться с учетом статусов родительских операций (Load, Drop).

---

### Таблица History

**Стратегия:** **APPEND_MERGE** (добавление без перезаписи)

**Логика:**
```python
def resolve_history_conflict(local, remote, **kwargs):
    """
    Разрешает конфликт для таблицы History.
    История не должна перезаписываться — только добавляться.
    """
    # Если запись уже существует локально — не перезаписываем
    if local and local.get("id"):
        # Проверяем, не является ли это дубликатом
        if is_duplicate_history(local, remote):
            return local  # Сохраняем локальную версию
        else:
            # Разные записи — добавляем удаленную как новую
            return create_new_record(remote)
    
    # Записи нет — добавляем
    return remote

def is_duplicate_history(local, remote):
    """Проверяет, является ли запись истории дубликатом."""
    key_fields = ["user_id", "tools_id", "datetime", "description", "status"]
    
    for field in key_fields:
        local_val = local.get(field)
        remote_val = remote.get(field)
        
        # Нормализация datetime для сравнения
        if field == "datetime":
            local_val = normalize_datetime(local_val)
            remote_val = normalize_datetime(remote_val)
        
        if local_val != remote_val:
            return False
    
    return True
```

---

### Справочники (Status, Role, Group, Plan, User, Rights, Page, Help, Type)

**Стратегия:** **SERVER_WINS** (сервер всегда имеет приоритет)

**Логика:** Эти данные управляются централизованно на сервере и должны быть одинаковыми на всех устройствах.

---

### Таблицы ToolTypes, Tools

**Стратегия:**
- `ToolTypes`: **SERVER_WINS**
- `Tools`: **TIMESTAMP_WINS** (более новая версия)

**Логика:** Типы инструментов — справочник. Конкретные инструменты могут изменяться на клиенте (выдача), но при конфликте приоритет у более новой версии.

---

### Таблицы связей с устройствами (*HasDevice)

**Стратегия:** **DEVICE_SPECIFIC_MERGE**

**Логика:** Записи для текущего устройства сохраняются локально, записи для других устройств принимаются с сервера.

---

## Детальная логика для Cell

### Полная логика разрешения конфликтов для Cell

```python
def resolve_cell_conflict_detailed(local, remote, **kwargs):
    """
    Детальная логика разрешения конфликтов для таблицы Cell.
    
    Параметры:
    - local: локальные данные ячейки
    - remote: удаленные данные ячейки (с сервера)
    - kwargs: дополнительные параметры (remote_status_stype, device_id, timestamp)
    """
    local_status_id = local.get("status_id")
    remote_status_id = remote.get("status_id")
    remote_status_stype = kwargs.get("remote_status_stype")
    
    # === ПРАВИЛО 1: Массовые операции с сервера имеют приоритет ===
    if remote_status_stype in ("mass_load_init", "mass_load_ready", 
                                "mass_drop_init", "mass_drop_ready"):
        merged = dict(local)
        merged.update(remote)
        log_info("LWW: accepting remote (mass operation)", {
            "remote_status_stype": remote_status_stype,
            "local_status_id": local_status_id,
            "remote_status_id": remote_status_id
        })
        return merged
    
    # === ПРАВИЛО 2: Защита локальных активных операций ===
    if local_status_id:
        local_status = get_status_by_id(local_status_id)
        if local_status:
            local_stype = local_status.stype
            
            # Активные операции выдачи (НЕЛЬЗЯ ЗАТИРАТЬ)
            if local_stype in ("load_ready", "mass_load_ready"):
                # Исключение: если сервер отправляет массовую операцию — принимаем её
                if remote_status_stype in ("mass_load_init", "mass_drop_init"):
                    merged = dict(local)
                    merged.update(remote)
                    log_info("LWW: accepting remote (mass operation overrides local active)", {
                        "local_stype": local_stype,
                        "remote_status_stype": remote_status_stype
                    })
                    return merged
                else:
                    # Защищаем локальные данные
                    log_info("LWW: keeping local data (active operation)", {
                        "local_stype": local_stype,
                        "remote_status_id": remote_status_id
                    })
                    return local
    
    # === ПРАВИЛО 3: Если удаленная операция активна и локальная нет — принимаем удаленные ===
    if remote_status_id:
        remote_status = get_status_by_id(remote_status_id)
        if remote_status:
            remote_stype = remote_status.stype
            if remote_stype in ("load_ready", "mass_load_ready"):
                # Проверяем, не активна ли локальная операция
                if local_status_id:
                    local_status = get_status_by_id(local_status_id)
                    if local_status and local_status.stype not in ("load_ready", "mass_load_ready"):
                        log_info("LWW: accepting remote (active operation)", {
                            "remote_stype": remote_stype,
                            "local_stype": local_status.stype
                        })
                        return remote
                else:
                    # Локальной записи нет — принимаем удаленные
                    return remote
    
    # === ПРАВИЛО 4: Нейтральные статусы можно затирать ===
    if local_status_id in (1, 6):  # start_system, drop_ready
        if remote_status_id and remote_status_id not in (1, 6):
            # Удаленная версия более информативна
            merged = dict(local)
            merged.update(remote)
            log_info("LWW: accepting remote (neutral local status)", {
                "local_status_id": local_status_id,
                "remote_status_id": remote_status_id
            })
            return merged
    
    # === ПРАВИЛО 5: В остальных случаях — более новая версия (TIMESTAMP_WINS) ===
    return resolve_timestamp_wins(local, remote, **kwargs)
```

---

## Приоритеты синхронизации

### Уровень 1: Критически важные (синхронизируются первыми)

1. **Status** — справочник статусов (необходим для всех операций)
2. **Cell** — состояние ячеек (критично для работы аппарата)
3. **Load**, **Drop** — текущие операции загрузки/выдачи

**Порядок:** Status → Cell → Load/Drop

---

### Уровень 2: Важные (синхронизируются вторыми)

4. **MassLoad**, **MassDrop** — массовые операции
5. **LoadOperations**, **DropOperations** — детали операций
6. **User**, **Role** — пользователи и роли (для авторизации)

**Порядок:** User/Role → MassLoad/MassDrop → LoadOperations/DropOperations

---

### Уровень 3: Справочники (синхронизируются третьими)

7. **Group**, **Plan**, **PlanToolTypes** — справочники
8. **ToolTypes**, **Tools** — каталог инструментов
9. **Page**, **Rights** — права доступа

**Порядок:** Group → Plan → ToolTypes → Tools → Page/Rights

---

### Уровень 4: История (синхронизируются последними)

10. **History** — история операций
11. **Error** — история ошибок
12. **Identification** — история идентификаций

**Порядок:** History → Error → Identification

---

### Уровень 5: Связи (синхронизируются параллельно)

13. Все таблицы `*HasDevice` — связи с устройствами

**Порядок:** Параллельно с соответствующими основными таблицами

---

## План реализации

### ✅ Этап 1: Исправление ConflictManager для Cell (ВЫПОЛНЕНО)

**Файл:** `client/dbSync/Logic_v2/ConflictManager.py`

**Реализованные изменения:**

1. ✅ Добавлена проверка локальных активных операций перед принятием удаленных данных
2. ✅ Добавлена защита для статусов `load_ready` (7) и `mass_load_ready` (3)
3. ✅ Массовые операции с сервера имеют приоритет даже над активными операциями
4. ✅ Fallback проверка по `status_id` (3 или 7), если `stype` недоступен

**Ключевые изменения в коде:**

```python
# === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Для Cell добавляем защиту локальных активных операций ===
if table == "Cell":
    local_status_id = local_data.get("status_id")
    remote_status_id = remote_norm.get("status_id")
    local_status_stype = kwargs.get("local_status_stype")
    
    # 1. Массовые операции с сервера имеют приоритет (даже над активными операциями)
    if remote_status_stype in ("mass_load_init", "mass_load_ready", 
                                "mass_drop_init", "mass_drop_ready"):
        merged = dict(local_data)
        merged.update(remote_norm)
        return merged
    
    # 2. Защита локальных активных операций (load_ready, mass_load_ready)
    if local_status_id:
        is_active_operation = False
        if local_status_stype:
            is_active_operation = local_status_stype in ("load_ready", "mass_load_ready")
        elif local_status_id in (3, 7):  # Fallback по status_id
            is_active_operation = True
        
        if is_active_operation:
            return local_data  # Защищаем локальные данные
```

---

### ✅ Этап 2: Модификация SyncProcessor (ВЫПОЛНЕНО)

**Файл:** `client/dbSync/Logic_v2/SyncProcessor.py`

**Реализованные изменения:**

1. ✅ Передача `table` в `apply_data_strategy` для специальной логики Cell
2. ✅ Получение `local_status_stype` для Cell через `sync_manager.get_status_stype()`
3. ✅ Передача `local_status_stype` в `apply_data_strategy`

**Ключевые изменения в коде:**

```python
# Для Cell также получаем локальный stype для защиты активных операций
local_stype = None
if table == "Cell" and existing.get("status_id"):
    local_stype = self.sync_manager.get_status_stype(existing.get("status_id"))

local = self.conflict_manager.apply_data_strategy(
    existing, local, 
    remote_status_stype=remote_stype,
    table=table,  # Передаем имя таблицы для специальной логики Cell
    local_status_stype=local_stype  # Передаем локальный stype для защиты активных операций
)
```

---

### ✅ Этап 3: Тестирование (ГОТОВО К ТЕСТИРОВАНИЮ)

**Тестовые сценарии:**

1. **Сценарий 1:** Клиент имеет ячейку со статусом `load_ready` (7), сервер отправляет `mass_drop_init` (4)
   - **Ожидаемый результат:** Принимаем данные с сервера (массовая операция имеет приоритет)

2. **Сценарий 2:** Клиент имеет ячейку со статусом `load_ready` (7), сервер отправляет `start_system` (1)
   - **Ожидаемый результат:** Сохраняем локальные данные (активная операция защищена)

3. **Сценарий 3:** Клиент имеет ячейку со статусом `mass_load_ready` (3), сервер отправляет `mass_drop_init` (4)
   - **Ожидаемый результат:** Принимаем данные с сервера (массовая операция имеет приоритет)

4. **Сценарий 4:** Клиент имеет ячейку со статусом `mass_load_ready` (3), сервер отправляет `start_system` (1)
   - **Ожидаемый результат:** Сохраняем локальные данные (активная операция защищена)

5. **Сценарий 5:** Клиент имеет ячейку со статусом `start_system` (1), сервер отправляет `mass_load_init` (5)
   - **Ожидаемый результат:** Принимаем данные с сервера (нейтральный статус можно затирать)

---

## Итоговая таблица стратегий

| Таблица | Стратегия | Защита локальных активных операций | Приоритет массовых операций | Примечания |
|---------|-----------|-------------------------------------|----------------------------|------------|
| **Cell** | STATUS_AWARE_LWW | ✅ `load_ready`, `mass_load_ready` | ✅ `mass_load_init`, `mass_drop_init` | Критично важно |
| **Load** | STATUS_AWARE_LWW | ✅ По статусу родительской операции | ✅ Массовые операции | Связана с Cell |
| **Drop** | STATUS_AWARE_LWW | ✅ По статусу родительской операции | ✅ Массовые операции | Связана с Cell |
| **MassLoad** | STATUS_AWARE_LWW | ✅ По статусу операции | ✅ Всегда принимаем с сервера | Массовая операция |
| **MassDrop** | STATUS_AWARE_LWW | ✅ По статусу операции | ✅ Всегда принимаем с сервера | Массовая операция |
| **LoadOperations** | STATUS_AWARE_LWW | ✅ По статусу операции | ✅ Массовые операции | Детали операций |
| **DropOperations** | STATUS_AWARE_LWW | ✅ По статусу операции | ✅ Массовые операции | Детали операций |
| **Consumption** | STATUS_AWARE_LWW | ✅ По статусу операции | ✅ Массовые операции | Операции расхода |
| **OperationsConsumption** | STATUS_AWARE_LWW | ✅ По статусу операции | ✅ Массовые операции | Детали расхода |
| **History** | APPEND_MERGE | ✅ Всегда сохраняем локальные | ❌ | История не перезаписывается |
| **Error** | APPEND_MERGE | ✅ Всегда сохраняем локальные | ❌ | История ошибок |
| **Status** | SERVER_WINS | ❌ | ❌ | Справочник |
| **Role** | SERVER_WINS | ❌ | ❌ | Справочник |
| **User** | SERVER_WINS | ❌ | ❌ | Управляется на сервере |
| **Group** | SERVER_WINS | ❌ | ❌ | Справочник |
| **Plan** | SERVER_WINS | ❌ | ❌ | Справочник |
| **ToolTypes** | SERVER_WINS | ❌ | ❌ | Справочник |
| **Tools** | TIMESTAMP_WINS | ❌ | ❌ | Более новая версия |
| ***HasDevice** | DEVICE_SPECIFIC_MERGE | ✅ Для текущего устройства | ❌ | Связи с устройствами |

---

## Ключевые правила защиты данных

### Правило 1: Защита локальных активных операций

**Статусы, которые НЕЛЬЗЯ затирать:**
- `load_ready` (7) — пользователь выбрал инструмент
- `mass_load_ready` (3) — инструмент готов к выдаче после массовой загрузки

**Исключение:** Массовые операции с сервера (`mass_load_init`, `mass_drop_init`) имеют приоритет даже над активными операциями.

---

### Правило 2: Приоритет массовых операций

**Статусы массовых операций, которые ВСЕГДА принимаются с сервера:**
- `mass_load_init` (5) — объявлена массовая загрузка
- `mass_drop_init` (4) — объявлена массовая выгрузка
- `mass_load_ready` (3) — если приходит с сервера после массовой загрузки
- `mass_drop_ready` (2) — если приходит с сервера после массовой выгрузки

---

### Правило 3: Нейтральные статусы

**Статусы, которые можно затирать:**
- `start_system` (1) — пустая ячейка
- `drop_ready` (6) — обычная выгрузка (не массовая)

---

## Заключение

Предложенные стратегии обеспечивают:

1. **Защиту локальных активных операций** — данные клиента не стираются при активных операциях выдачи
2. **Приоритет массовых операций** — массовые операции с сервера принимаются даже при активных локальных операциях
3. **Консистентность** — критически важные данные синхронизируются правильно
4. **Целостность истории** — история сохраняется полностью без потерь

**Критическое исправление:** Добавлена защита для статусов `load_ready` (7) и `mass_load_ready` (3), чтобы предотвратить затирание данных клиента при синхронизации.

---

*Документ создан на основе анализа проблемы с массовой выгрузкой. Последнее обновление: 2026-01-27*
