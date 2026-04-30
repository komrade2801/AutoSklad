# Документация структуры базы данных AutoSklad (server)

> Основано на серверном скрипте инициализации `server/Core/Create_db.py` (центральная БД, SQLite/MySQL).

## Обзор

Система AutoSklad использует реляционную базу данных, построенную на SQLAlchemy ORM. База данных поддерживает два движка:
- **SQLite** - для локальных инсталляций и синхронизации
- **MySQL** - для корпоративных развертываний

База данных состоит из **37 таблиц**, организованных в несколько функциональных групп.

---

## Структура базы данных

### 1. Управление пользователями и доступом

#### 1.1 User (Пользователи)
Хранит информацию о пользователях системы.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор пользователя
- `barcode` (Integer, UNIQUE) - Штрих-код пользователя для идентификации
- `code` (Integer, UNIQUE) - Код пользователя
- `first_name` (String(50)) - Имя
- `password` (String(45)) - Пароль
- `second_name` (String(50)) - Отчество
- `family` (String(50)) - Фамилия
- `role_id` (Integer, FK → Role.id) - Роль пользователя

**Связи:**
- Role (многие-к-одному) - Роль пользователя
- Identification (один-ко-многим) - История идентификаций
- History (один-ко-многим) - История действий
- ActualNorm (один-ко-многим) - Нормы пользователя
- Command (один-ко-многим) - Команды пользователя

**Индексы:**
- `id_user` на `id`
- `fk_user_role_idx` на `role_id`

---

#### 1.2 Role (Роли)
Определяет роли пользователей с поддержкой иерархии.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор роли
- `name` (String(45)) - Название роли
- `description` (String(450)) - Описание роли
- `parent_role_id` (Integer, FK → Role.id) - Родительская роль для иерархии

**Связи:**
- Role (самосвязь) - Иерархия ролей
- Rights (один-ко-многим) - Права доступа роли
- User (один-ко-многим) - Пользователи с этой ролью
- History (один-ко-многим) - История по ролям

**Индексы:**
- `idx_role_name` на `name`
- `fk_role_parent_idx` на `parent_role_id`

---

#### 1.3 Rights (Права доступа)
Управляет правами доступа для ролей к страницам системы.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор права
- `name` (String(45)) - Название права
- `description` (String(450)) - Описание права
- `role_id` (Integer, FK → Role.id) - Роль
- `page_id` (Integer, FK → Page.id) - Страница

**Связи:**
- Role (многие-к-одному) - Роль
- Page (многие-к-одному) - Страница

---

#### 1.4 Page (Страницы)
Реестр HTML-страниц системы для управления доступом.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор страницы
- `name` (String(45)) - Имя HTML-файла (например, screen_2_mass_load.html)
- `description` (String(150)) - Описание страницы

**Связи:**
- Rights (один-ко-многим) - Права доступа к странице

---

#### 1.5 Identification (Идентификация)
Журнал событий идентификации пользователей в системе.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор записи
- `datetime` (DateTime) - Дата и время идентификации
- `status` (Integer) - Статус идентификации (успешная/неуспешная)
- `description` (String(450)) - Дополнительное описание
- `user_id` (Integer, FK → User.id) - Пользователь

**Связи:**
- User (многие-к-одному) - Пользователь

**Индексы:**
- `idx_identification_user` на `user_id`
- `idx_identification_datetime` на `datetime`
- `idx_identification_status` на `status`

---

### 2. Управление инструментами

#### 2.1 ToolTypes (Типы инструментов)
Каталог типов инструментов (шаблоны).

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор типа
- `name` (String(45)) - Название инструмента
- `description` (String(450)) - Описание инструмента
- `count` (Integer) - Количество инструментов данного типа
- `img` (String(45)) - Путь к изображению
- `groups_id` (Integer, FK → Group.id) - Группа инструмента

**Связи:**
- Group (многие-к-одному) - Группа инструментов
- Tools (один-ко-многим) - Конкретные экземпляры инструментов
- Cell (один-ко-многим) - Ячейки с этим типом
- History (один-ко-многим) - История операций
- Load, Drop, Consumption (один-ко-многим) - Операции с инструментами
- LoadOperations, DropOperations, OperationsConsumption (один-ко-многим)
- PlanToolTypes (один-ко-многим) - Связь с чертежами

**Назначение:** Типы инструментов используются как шаблоны для конкретных экземпляров (Tools).

---

#### 2.2 Tools (Инструменты)
Конкретные экземпляры инструментов с инвентарными номерами.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор инструмента
- `inventory_number` (String) - Инвентарный номер
- `barcode` (String(45)) - Штрих-код инструмента
- `plan_id` (Integer, FK → Plan.id) - Чертеж
- `tool_type_id` (Integer, FK → ToolTypes.id) - Тип инструмента
- `name` (String(45)) - Название
- `description` (String(450)) - Описание
- `count` (Integer) - Количество
- `img` (String(45)) - Изображение
- `groups_id` (Integer, FK → Group.id) - Группа

**Связи:**
- Plan (многие-к-одному) - Чертеж
- ToolTypes (многие-к-одному) - Тип инструмента
- Group (многие-к-одному) - Группа
- Cell (один-ко-многим) - Ячейки с инструментом
- History (один-ко-многим) - История
- ToolsHasDevice (один-ко-многим) - Связь с устройствами
- ToolsNorm (один-ко-многим) - Нормы использования
- ToolLocation (один-ко-многим) - Местоположение инструментов

---

#### 2.3 Group (Группы инструментов)
Иерархическая классификация инструментов.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор группы
- `name` (String(100)) - Название группы
- `description` (String(450)) - Описание группы
- `paren_group_id` (Integer) - ID родительской группы

**Связи:**
- Cell (один-ко-многим) - Ячейки группы
- Tools (один-ко-многим) - Инструменты группы
- ToolTypes (один-ко-многим) - Типы инструментов группы

**Индексы:**
- `idx_group_name` на `name`
- `idx_group_paren_group_id` на `paren_group_id`

---

#### 2.4 ToolsNorm (Нормы инструментов)
Нормы использования инструментов пользователями.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор нормы
- `summa` (Integer) - Сумма/лимит
- `summa_of_periods` (Integer) - Сумма за периоды
- `description` (String(450)) - Описание
- `type_periods` (String(45)) - Тип периода (день, неделя, месяц)
- `summa_of_use` (String(45)) - Сумма использования
- `start_date` (DateTime) - Дата начала действия нормы
- `tools_id` (Integer, FK → Tools.id) - Инструмент
- `actual_norm_id` (Integer, FK → ActualNorm.id) - Актуальная норма

**Связи:**
- Tools (многие-к-одному) - Инструмент
- ActualNorm (многие-к-одному) - Актуальная норма

**Индексы:**
- `fk_ToolsNorm_Tools1_idx` на `tools_id`
- `fk_ToolsNorm_ActualNorm1_idx` на `actual_norm_id`

---

#### 2.5 ActualNorm (Актуальные нормы)
Активные нормы пользователей на конкретную дату.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор квоты
- `user_id` (Integer, FK → User.id) - Пользователь
- `day` (DateTime) - Дата

**Связи:**
- User (многие-к-одному) - Пользователь
- Device (многие-ко-многим через ActualNormHasDevice) - Устройства
- ToolsNorm (один-ко-многим) - Нормы инструментов

**Индексы:**
- `fk_ActualNorm_User1_idx` на `user_id`

---

### 3. Управление складом

#### 3.1 Cell (Ячейки)
Физические ячейки склада для хранения инструментов.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор ячейки
- `number` (Integer, UNIQUE) - Номер ячейки
- `description` (String(255)) - Описание ячейки
- `groups_id` (Integer, FK → Group.id) - Группа
- `tools_id` (Integer, FK → ToolTypes.id) - Тип инструмента в ячейке
- `status_id` (Integer, FK → Status.id) - Статус ячейки
- `hal_x` (Integer, nullable) - Координата X для HAL-сценария выдачи
- `hal_z` (Integer, nullable) - Координата Z для HAL-сценария выдачи

**Связи:**
- Group (многие-к-одному) - Группа
- ToolTypes (многие-к-одному) - Тип инструмента
- Status (многие-к-одному) - Статус
- CellHasDevice (один-ко-многим) - Связь с устройствами
- Load (один-ко-многим) - Операции загрузки
- Drop (один-ко-многим) - Операции выдачи
- Consumption (один-ко-многим) - Операции расхода

**Индексы:**
- `idx_cell_groups_id` на `groups_id`
- `idx_cell_tools_id` на `tools_id`

---

#### 3.2 Status (Статусы)
Справочник статусов для различных объектов системы.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор статуса
- `stype` (String(100), UNIQUE) - Тип статуса (Active, Inactive, Pending и т.д.)
- `description` (String(255)) - Описание статуса
- `created_at` (DateTime) - Дата создания записи

**Связи:**
- Cell (один-ко-многим) - Статусы ячеек
- DropOperations (один-ко-многим) - Статусы операций выдачи
- LoadOperations (один-ко-многим) - Статусы операций загрузки
- OperationsConsumption (один-ко-многим) - Статусы операций расхода
- MassLoad (один-ко-многим) - Статусы массовой загрузки
- Load, Drop, Consumption (один-ко-многим) - Статусы операций
- Command (один-ко-многим) - Статусы команд
- ToolLocation (один-ко-многим) - Статусы местоположений

**Индексы:**
- `idx_type_status` на `stype`
- `idx_created_at_status` на `created_at`

---

#### 3.3 ToolLocation (Местоположение инструментов)
Отслеживание текущего местоположения инструментов.

**Поля:**
- `tools_id` (Integer, PK, FK → Tools.id) - Инструмент
- `status_id` (Integer, FK → Status.id) - Статус местоположения

**Связи:**
- Tools (многие-к-одному) - Инструмент
- Status (многие-к-одному) - Статус

---

### 4. Устройства и синхронизация

#### 4.1 Device (Устройства)
Вендинговые устройства (автоматы) в системе.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор устройства
- `number` (Integer, UNIQUE) - Уникальный номер устройства
- `name` (String(45)) - Название устройства
- `description` (String(150)) - Краткое описание
- `details` (String(450)) - Подробная информация
- `create` (Date) - Дата создания записи

**Связи:**
- CellHasDevice (один-ко-многим) - Ячейки устройства
- Drop (один-ко-многим) - Операции выдачи
- Error (многие-ко-многим через ErrorHasDevice) - Ошибки устройства
- MassDrop (многие-ко-многим через MassDropHasDevice) - Массовые выдачи
- MassLoad (многие-ко-многим через MassLoadHasDevice) - Массовые загрузки
- Command (один-ко-многим) - Команды устройства
- ActualNorm (многие-ко-многим через ActualNormHasDevice) - Нормы

**Индексы:**
- `number_UNIQUE` на `number`

---

#### 4.2 CellHasDevice (Связь ячеек и устройств)
Связующая таблица many-to-many между ячейками и устройствами.

**Поля:**
- `cell_id` (Integer, PK, FK → Cell.id) - Ячейка
- `device_id` (Integer, PK, FK → Device.id) - Устройство

**Связи:**
- Cell (многие-к-одному) - Ячейка
- Device (многие-к-одному) - Устройство

---

#### 4.3 ToolsHasDevice (Связь инструментов и устройств)
Связующая таблица many-to-many между инструментами и устройствами.

**Поля:**
- `tools_id` (Integer, PK, FK → Tools.id) - Инструмент
- `device_id` (Integer, PK, FK → Device.id) - Устройство

**Связи:**
- Tools (многие-к-одному) - Инструмент
- Device (многие-к-одному) - Устройство

---

#### 4.4 Command (Команды)
Команды для синхронизации и управления устройствами.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор команды
- `user_id` (Integer, FK → User.id) - Пользователь, создавший команду
- `device_id` (Integer, FK → Device.id) - Устройство
- `type_id` (Integer, FK → Type.id) - Тип команды
- `status_id` (Integer, FK → Status.id) - Статус выполнения
- `name` (String(45)) - Название команды
- `create` (Date) - Дата создания

**Связи:**
- User (многие-к-одному) - Пользователь
- Device (многие-к-одному) - Устройство
- Type (многие-к-одному) - Тип команды
- Status (многие-к-одному) - Статус

**Индексы:**
- `fk_Command_Device1_idx` на `device_id`
- `fk_Command_Status1_idx` на `status_id`
- `fk_Command_Type1_idx` на `type_id`
- `fk_Command_User1_idx` на `user_id`

---

#### 4.5 Type (Типы операций)
Справочник типов операций и команд.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор типа
- `name` (String(50)) - Название типа
- `operation` (String(10)) - Описание операции (insert, update, delete)

**Связи:**
- Command (один-ко-многим) - Команды этого типа

---

### 5. Операции с инструментами

#### 5.1 Load (Загрузка)
Операции загрузки инструментов в ячейки склада.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор загрузки
- `description` (String(255)) - Описание операции
- `tools_id` (Integer, FK → ToolTypes.id) - Тип инструмента
- `mass_load_id` (Integer, FK → MassLoad.id) - Массовая загрузка
- `cell_id` (Integer, FK → Cell.id) - Ячейка
- `plan_id` (Integer, FK → Plan.id) - Чертеж
- `history_id` (Integer, FK → History.id) - Запись истории
- `status_id` (Integer, FK → Status.id) - Статус

**Связи:**
- ToolTypes (многие-к-одному) - Тип инструмента
- MassLoad (многие-к-одному) - Массовая загрузка
- Cell (многие-к-одному) - Ячейка
- Plan (многие-к-одному) - Чертеж
- History (многие-к-одному) - История
- Status (многие-к-одному) - Статус
- LoadOperations (один-ко-многим) - Детали операции загрузки

**Индексы:**
- `idx_load_tools_id` на `tools_id`
- `idx_load_mass_load_id` на `mass_load_id`
- `idx_load_cell_id` на `cell_id`
- `idx_load_plan_id` на `plan_id`
- `idx_load_history_id` на `history_id`

---

#### 5.2 MassLoad (Массовая загрузка)
Группировка операций загрузки в одну транзакцию.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор массовой загрузки
- `description` (String(255)) - Описание задачи
- `created_at` (DateTime) - Дата и время создания
- `status_id` (Integer, FK → Status.id) - Статус операции

**Связи:**
- Status (многие-к-одному) - Статус
- Load (один-ко-многим) - Операции загрузки
- Device (многие-ко-многим через MassLoadHasDevice) - Устройства

**Индексы:**
- `idx_created_at_MassLoad` на `created_at`

---

#### 5.3 LoadOperations (Операции загрузки)
Детализация операций загрузки с отслеживанием состояния.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор операции
- `date` (DateTime) - Дата и время выполнения
- `description` (String(255)) - Описание операции
- `load_id` (Integer, FK → Load.id) - Загрузка
- `load_tools_id` (Integer, FK → ToolTypes.id) - Инструмент
- `status_id` (Integer, FK → Status.id) - Статус
- `history_id` (Integer, FK → History.id) - История

**Связи:**
- Load (многие-к-одному) - Загрузка
- ToolTypes (многие-к-одному) - Инструмент
- Status (многие-к-одному) - Статус
- History (многие-к-одному) - История
- Device (многие-ко-многим через LoadOperationsHasDevice) - Устройства

**Индексы:**
- `idx_load_id_tools_id` на `load_id`, `load_tools_id`
- `idx_status_id` на `status_id`
- `idx_history_id` на `history_id`

---

#### 5.4 Drop (Выдача)
Операции выдачи инструментов пользователям.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор выдачи
- `description` (String(255)) - Описание операции
- `created_at` (DateTime) - Дата и время создания
- `cell_id` (Integer, FK → Cell.id) - Ячейка
- `mass_drop_id` (Integer, FK → MassDrop.id) - Массовая выдача
- `tools_id` (Integer, FK → ToolTypes.id) - Тип инструмента
- `plan_id` (Integer, FK → Plan.id) - Чертеж
- `history_id` (Integer, FK → History.id) - История
- `status_id` (Integer, FK → Status.id) - Статус

**Связи:**
- Cell (многие-к-одному) - Ячейка
- MassDrop (многие-к-одному) - Массовая выдача
- ToolTypes (многие-к-одному) - Тип инструмента
- Plan (многие-к-одному) - Чертеж
- History (многие-к-одному) - История
- Status (многие-к-одному) - Статус
- Device (многие-к-одному) - Устройство
- DropOperations (один-ко-многим) - Детали операции выдачи

**Индексы:**
- `idx_drop_tools_id` на `tools_id`
- `idx_drop_mass_drop_id` на `mass_drop_id`
- `idx_drop_cell_id` на `cell_id`
- `idx_drop_plan_id` на `plan_id`
- `idx_drop_history_id` на `history_id`

---

#### 5.5 MassDrop (Массовая выдача)
Группировка операций выдачи в одну транзакцию.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор массовой выдачи
- `description` (String(255)) - Описание задачи
- `created_at` (DateTime) - Дата и время создания

**Связи:**
- Drop (один-ко-многим) - Операции выдачи
- Device (многие-ко-многим через MassDropHasDevice) - Устройства

**Индексы:**
- `idx_created_at` на `created_at`

---

#### 5.6 DropOperations (Операции выдачи)
Детализация операций выдачи с отслеживанием состояния.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор операции
- `date` (DateTime) - Дата и время выполнения
- `description` (String(255)) - Описание операции
- `history_id` (Integer, FK → History.id) - История
- `status_id` (Integer, FK → Status.id) - Статус
- `tools_id` (Integer, FK → ToolTypes.id) - Инструмент
- `drop_id` (Integer, FK → Drop.id) - Выдача

**Связи:**
- Drop (многие-к-одному) - Выдача
- ToolTypes (многие-к-одному) - Инструмент
- Status (многие-к-одному) - Статус
- History (многие-к-одному) - История
- Device (многие-ко-многим через DropOperationsHasDevice) - Устройства

**Индексы:**
- `idx_drop_operations_drop_id_tools_id` на `drop_id`, `tools_id`
- `idx_drop_operations_status_id` на `status_id`
- `idx_drop_operations_history_id` на `history_id`

---

#### 5.7 Consumption (Расход)
Операции расхода/списания инструментов.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор расхода
- `cell_id` (Integer, FK → Cell.id) - Ячейка
- `tools_id` (Integer, FK → ToolTypes.id) - Инструмент
- `plan_id` (Integer, FK → Plan.id) - Чертеж
- `history_id` (Integer, FK → History.id) - История
- `status_id` (Integer, FK → Status.id) - Статус

**Связи:**
- Cell (многие-к-одному) - Ячейка
- ToolTypes (многие-к-одному) - Инструмент
- Plan (многие-к-одному) - Чертеж
- History (многие-к-одному) - История
- Status (многие-к-одному) - Статус
- OperationsConsumption (один-ко-многим) - Детали операции расхода

**Индексы:**
- `idx_consumption_tools_id` на `tools_id`
- `idx_consumption_cell_id` на `cell_id`
- `idx_consumption_plan_id` на `plan_id`
- `idx_consumption_history_id` на `history_id`

---

#### 5.8 OperationsConsumption (Операции расхода)
Детализация операций расхода с отслеживанием состояния.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор операции
- `date` (DateTime) - Дата и время операции
- `description` (String(255)) - Описание операции
- `consumption_id` (Integer, FK → Consumption.id) - Расход
- `history_id` (Integer, FK → History.id) - История
- `consumption_tools_id` (Integer, FK → ToolTypes.id) - Инструмент
- `status_id` (Integer, FK → Status.id) - Статус

**Связи:**
- Consumption (многие-к-одному) - Расход
- ToolTypes (многие-к-одному) - Инструмент
- Status (многие-к-одному) - Статус
- History (многие-к-одному) - История
- Device (многие-ко-многим через OperationsConsumptionHasDevice) - Устройства

**Индексы:**
- `idx_consumption_id_tools_id` на `consumption_id`, `consumption_tools_id`
- `idx_status_operations_consumption_id` на `status_id`

---

### 6. Чертежи и планирование

#### 6.1 Plan (Чертежи/Планы)
Чертежи изделий с иерархической структурой.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор чертежа
- `enterprise` (String(45)) - Название предприятия
- `barcode` (String(45)) - Штрих-код чертежа
- `name` (String(45)) - Название чертежа
- `description` (String(450)) - Описание чертежа
- `designation` (String(100)) - Назначение чертежа
- `index_list` (Integer) - Идентификатор списка
- `list_count` (Integer) - Количество в списке
- `parent_plan_id` (Integer, FK → Plan.id) - Родительский чертеж

**Связи:**
- Plan (самосвязь) - Иерархия чертежей
- History (один-ко-многим) - История операций
- Tools (один-ко-многим) - Инструменты чертежа
- Load, Drop, Consumption (один-ко-многим) - Операции по чертежу
- PlanToolTypes (один-ко-многим) - Типы инструментов в чертеже

**Индексы:**
- `idx_plan_barcode` на `barcode`
- `idx_plan_name` на `name`
- `fk_plan_parent_idx` на `parent_plan_id`

---

#### 6.2 PlanToolTypes (Состав чертежей)
Связь чертежей с необходимыми типами инструментов.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор связи
- `tool_types_id` (Integer, FK → ToolTypes.id) - Тип инструмента
- `tool_types_count` (Integer) - Количество инструментов данного типа
- `plan_id` (Integer, FK → Plan.id) - Чертеж

**Связи:**
- ToolTypes (многие-к-одному) - Тип инструмента
- Plan (многие-к-одному) - Чертеж

**Индексы:**
- `idx_plan_id` на `plan_id`

---

### 7. История и журналирование

#### 7.1 History (История)
Главный журнал всех операций в системе.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор записи истории
- `datetime` (DateTime) - Дата и время события
- `status` (Integer) - Статус действия
- `description` (String(450)) - Описание события
- `user_id` (Integer, FK → User.id) - Пользователь
- `user_role_id` (Integer, FK → Role.id) - Роль пользователя
- `tools_id` (Integer, FK → ToolTypes.id) - Инструмент
- `plan_id` (Integer, FK → Plan.id) - Чертеж

**Связи:**
- User (многие-к-одному) - Пользователь
- Role (многие-к-одному) - Роль
- ToolTypes (многие-к-одному) - Инструмент
- Plan (многие-к-одному) - Чертеж
- Load, Drop, Consumption (один-ко-многим) - Связанные операции
- LoadOperations, DropOperations, OperationsConsumption (один-ко-многим)
- Device (многие-ко-многим через HistoryHasDevice) - Устройства

**Назначение:** Центральная таблица аудита всех операций системы.

---

#### 7.2 Error (Ошибки)
Журнал системных ошибок и неполадок.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор ошибки
- `error_type` (String(100)) - Тип ошибки (Timeout, Device Error и др.)
- `message` (String(500)) - Подробное сообщение об ошибке
- `timestamp` (DateTime) - Время возникновения ошибки

**Связи:**
- Device (многие-ко-многим через ErrorHasDevice) - Устройства с ошибками

**Индексы:**
- `idx_error_type` на `error_type`
- `idx_timestamp` на `timestamp`

---

### 8. Связующие таблицы устройств (HasDevice)

Эти таблицы реализуют связи many-to-many между различными сущностями и устройствами для поддержки многоустройственной архитектуры.

#### 8.1 ActualNormHasDevice
Связь актуальных норм с устройствами.

**Поля:**
- `actual_norm_id` (Integer, PK, FK → ActualNorm.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.2 MassLoadHasDevice
Связь массовых загрузок с устройствами.

**Поля:**
- `mass_load_id` (Integer, PK, FK → MassLoad.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.3 MassDropHasDevice
Связь массовых выдач с устройствами.

**Поля:**
- `mass_drop_id` (Integer, PK, FK → MassDrop.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.4 LoadOperationsHasDevice
Связь операций загрузки с устройствами.

**Поля:**
- `load_operations_id` (Integer, PK, FK → LoadOperations.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.5 DropOperationsHasDevice
Связь операций выдачи с устройствами.

**Поля:**
- `drop_operations_id` (Integer, PK, FK → DropOperations.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.6 OperationsConsumptionHasDevice
Связь операций расхода с устройствами.

**Поля:**
- `operations_consumption_id` (Integer, PK, FK → OperationsConsumption.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.7 ErrorHasDevice
Связь ошибок с устройствами.

**Поля:**
- `error_id` (Integer, PK, FK → Error.id)
- `device_id` (Integer, PK, FK → Device.id)

---

#### 8.8 HistoryHasDevice
Связь истории с устройствами.

**Поля:**
- `history_id` (Integer, PK, FK → History.id)
- `device_id` (Integer, PK, FK → Device.id)

---

### 9. Конфигурация и вспомогательные таблицы

#### 9.1 Settings (Настройки)
Хранилище настроек сервера в формате ключ-значение.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор настройки
- `key` (String(100), UNIQUE) - Ключ настройки
- `value` (Text) - Значение настройки в строковом формате
- `value_type` (String(20)) - Тип значения: 'str', 'int', 'bool', 'json'
- `category` (String(50)) - Категория настройки для группировки в UI
- `description` (Text) - Описание настройки для администраторов
- `updated_at` (DateTime) - Время последнего обновления
- `updated_by` (Integer) - ID пользователя, обновившего настройку
- `is_sensitive` (Boolean) - Флаг чувствительной информации (маскируется в UI)
- `requires_restart` (Boolean) - Требуется ли перезапуск сервера для применения
- `validation_rules` (Text) - JSON правила валидации значения

**Индексы:**
- `key_UNIQUE` на `key`

**Назначение:** Динамическое управление конфигурацией без редактирования кода.

---

#### 9.2 DeviceDefaults (Шаблоны устройств)
Шаблоны конфигураций для новых устройств.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор шаблона
- `template_name` (String(100), UNIQUE) - Имя шаблона конфигурации
- `config_type` (String(50)) - Тип конфигурации (device_config, и др.)
- `config_json` (Text) - JSON строка с полной конфигурацией устройства
- `description` (Text) - Описание шаблона для администраторов
- `is_active` (Boolean) - Активен ли шаблон для использования
- `created_at` (DateTime) - Время создания шаблона

**Индексы:**
- `template_name_UNIQUE` на `template_name`

**Назначение:** Упрощение развертывания новых устройств с предустановленными настройками.

---

#### 9.3 Help (Справка)
Система встроенной справки и подсказок.

**Поля:**
- `id` (Integer, PK) - Уникальный идентификатор записи справки
- `text` (String(450)) - Текст справки
- `data` (DateTime) - Дата создания/обновления

**Назначение:** Хранение контекстной справки для пользователей системы.

---

## Диаграмма связей основных сущностей

```
┌─────────┐     ┌──────┐     ┌────────┐
│  User   │────►│ Role │────►│ Rights │
└────┬────┘     └──┬───┘     └───┬────┘
     │            │              │
     │            │         ┌────▼────┐
     │            │         │  Page   │
     │            │         └─────────┘
     │            │
     │            ▼
     │      ┌─────────┐
     │      │ History │◄────────┐
     │      └────┬────┘         │
     ▼           │              │
┌─────────────┐  │         ┌────────────┐
│Identification│ │         │ ToolTypes  │
└─────────────┘  │         └─────┬──────┘
                 │               │
                 │               ├───► Load ────► MassLoad
                 │               │
                 │               ├───► Drop ────► MassDrop
                 │               │
                 │               └───► Consumption
                 │
                 └──────► Plan ◄──── PlanToolTypes
                          │
                          └──► Tools ──► ToolsNorm ──► ActualNorm
                               │
                               └──► Cell ──► Status
                                    │
                                    └──► CellHasDevice ──► Device
                                                           │
                                                           └──► Command ──► Type
```

---

## CRUD Registry (Реестр операций)

Система использует централизованный реестр CRUD-операций (`crud_registry.py`), который автоматически сопоставляет имена таблиц с соответствующими Engine-классами.

### Поддерживаемые форматы имен:
- **CamelCase**: `MassLoad`, `ToolTypes`
- **snake_case**: `mass_load`, `tool_types`
- **Нормализованные**: автоматическое удаление небуквенных символов и приведение к нижнему регистру

### Зарегистрированные Engine-классы:
```python
Cell, Consumption, Drop, DropOperations, Error, Group, Help, 
History, Identification, Load, LoadOperations, MassDrop, MassLoad, 
OperationsConsumption, Plan, PlanToolTypes, Rights, Role, Status, 
Tools, ToolTypes, User
```

---

## Процесс инициализации базы данных

### Создание схемы (`Create_db.py`)

**Последовательность создания таблиц:**
```python
[Cell, CellHasDevice, Command, Consumption, Device, Drop, DropOperations, 
DropOperationsHasDevice, Error, ErrorHasDevice, Group, Help, History, 
Identification, Load, LoadOperations, LoadOperationsHasDevice, MassDrop, 
MassLoad, MassDropHasDevice, MassLoadHasDevice, OperationsConsumption, 
OperationsConsumptionHasDevice, Plan, ActualNorm, ActualNormHasDevice, 
Rights, Role, Status, ToolTypes, ToolLocation, Tools, ToolsHasDevice, 
ToolsNorm, Type, User, Page, Settings, DeviceDefaults]
```

**Процесс:**
1. Удаление существующей БД (если есть)
2. Создание пустого файла SQLite
3. Создание engine через SQLAlchemy
4. Выполнение `Base.metadata.create_all(engine)`
5. Заполнение начальными данными через `default.py`

---

## Ключевые особенности схемы

### 1. Иерархические структуры
- **Role** - иерархия ролей через `parent_role_id`
- **Plan** - вложенные чертежи через `parent_plan_id`
- **Group** - иерархия групп инструментов через `paren_group_id`

### 2. Многоустройственная архитектура
- Все операционные таблицы имеют связующие таблицы `*HasDevice`
- Поддержка распределенной синхронизации данных
- Изоляция данных по устройствам

### 3. Аудит и трассировка
- Таблица **History** - центральный журнал всех операций
- Связь всех операций с историей через `history_id`
- Отслеживание пользователей, ролей, времени и контекста

### 4. Гибкость статусов
- Единая таблица **Status** для всех типов статусов
- Поле `stype` определяет назначение статуса
- Возможность добавления новых статусов без изменения схемы

### 5. Типизация инструментов
- **ToolTypes** - шаблоны/типы инструментов
- **Tools** - конкретные экземпляры с инвентарными номерами
- Связь через `tool_type_id` для группировки и учета

---

## Индексы и производительность

### Основные индексированные поля:
- Все внешние ключи (автоматические индексы)
- Поля для поиска: `barcode`, `code`, `name`
- Поля для фильтрации: `status_id`, `datetime`, `created_at`
- Уникальные поля: `number`, `barcode`, `code`

### Составные индексы:
- `(load_id, load_tools_id)` в LoadOperations
- `(drop_id, tools_id)` в DropOperations
- `(consumption_id, consumption_tools_id)` в OperationsConsumption

---

## Интеграция с системой синхронизации

### Таблицы синхронизации:
- **Command** - команды для синхронизации
- **Type** - типы операций (insert, update, delete)
- Все `*HasDevice` таблицы - привязка данных к устройствам

### Поток данных:
1. Изменение данных на устройстве → создание Command
2. Синхронизация через `/sync/push`
3. Применение изменений на сервере
4. Распространение через `/sync/pull` на другие устройства

---

## Рекомендации по работе с БД

### 1. Создание записей
- Всегда создавайте запись в **History** для операций
- Используйте транзакции для связанных операций (Load + LoadOperations)
- Проверяйте существование связанных записей перед вставкой

### 2. Обновление записей
- Обновляйте `updated_at` в Settings
- Создавайте запись в History при изменении критичных данных
- Используйте оптимистичную блокировку для конкурентных изменений

### 3. Удаление записей
- Предпочитайте soft delete через изменение `status_id`
- Проверяйте наличие зависимых записей
- Создавайте запись в History при удалении

### 4. Запросы
- Используйте индексы для фильтрации
- Применяйте lazy loading для связей
- Ограничивайте выборку через LIMIT/OFFSET

---

## Версионирование и миграции

Для управления изменениями схемы используется модуль `DatabaseMigrator.py` из `Core/`.

### Процесс миграции:
1. Создание скрипта миграции
2. Тестирование на копии БД
3. Резервное копирование перед применением
4. Выполнение миграции
5. Проверка целостности данных

---

## Заключение

База данных AutoSklad представляет собой комплексную систему управления инструментальным складом с поддержкой:
- Многопользовательского доступа с ролевой моделью
- Распределенной архитектуры с синхронизацией
- Полного аудита операций
- Иерархических справочников
- Гибкой системы статусов и типизации

Архитектура позволяет масштабировать систему от одного устройства до распределенной сети вендинговых автоматов с централизованным управлением.



