# Список операций системы AutoSklad

Документ содержит полный перечень операций, доступных на сервере (веб-интерфейс и API) и на клиенте (вендинговый аппарат).

---

## Оглавление

1. [Операции на сервере](#операции-на-сервере)
   - [Управление пользователями и правами](#управление-пользователями-и-правами)
   - [Управление инструментами](#управление-инструментами)
   - [Управление группами](#управление-группами)
   - [Управление планами (чертежами)](#управление-планами-чертежами)
   - [Управление ячейками](#управление-ячейками)
   - [Массовые операции](#массовые-операции)
   - [История операций](#история-операций)
   - [Управление устройствами](#управление-устройствами)
   - [Настройки системы](#настройки-системы)
   - [Справочники](#справочники)
2. [Операции на клиенте](#операции-на-клиенте)
   - [Авторизация и идентификация](#авторизация-и-идентификация)
   - [Выдача инструментов](#выдача-инструментов)
   - [Массовые операции](#массовые-операции-клиент)
   - [Управление складом](#управление-складом)
   - [Просмотр истории](#просмотр-истории)
   - [Администрирование](#администрирование)
   - [Справочная информация](#справочная-информация)

---

## Операции на сервере

### Управление пользователями и правами

#### Пользователи (`/backend/all_users`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/authorization` | Авторизация пользователя (проверка логина/пароля) |
| GET | `/all_users` | Получить список всех пользователей |
| GET | `/all_users/{user_id}` | Получить информацию о конкретном пользователе |
| POST | `/create_user` | Создать нового пользователя |
| PUT | `/update_user/{user_id}` | Обновить данные пользователя |
| PATCH | `/patch_user/{user_id}` | Частичное обновление пользователя |
| DELETE | `/delete_user/{user_id}` | Удалить пользователя |
| POST | `/generate_credentials` | Сгенерировать учетные данные для пользователя |

#### Роли (`/backend/all_users`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/create_role` | Создать новую роль |
| GET | `/get_role/{role_id}` | Получить информацию о роли |
| GET | `/list_roles` | Получить список всех ролей |
| PUT | `/update_role/{role_id}` | Обновить роль |
| DELETE | `/delete_role/{role_id}` | Удалить роль |

#### Права доступа (`/backend/all_users`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/create_right` | Создать новое право доступа |
| GET | `/get_right/{right_id}` | Получить информацию о праве |
| GET | `/list_rights` | Получить список всех прав |
| PUT | `/update_right/{right_id}` | Обновить право доступа |
| DELETE | `/delete_right/{right_id}` | Удалить право доступа |

---

### Управление инструментами

#### Инструменты (`/backend/tools`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/tools/{device_number}` | Получить список инструментов для устройства |
| POST | `/tools/{device_number}` | Добавить инструмент в устройство |
| PUT | `/tools/{device_number}/{tool_id}` | Обновить инструмент |
| DELETE | `/tools/{device_number}/{tool_id}` | Удалить инструмент из устройства |

#### Все инструменты (`/backend/all_tools`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/create_tools` | Создать инструменты и тип инструмента |
| GET | `/tools_by_group/{group_id}` | Получить инструменты по группе |
| GET | `/tools_by_plan/{plan_id}` | Получить инструменты по плану |
| GET | `/tools_by_device/{device_number}` | Получить инструменты по устройству |
| GET | `/tools_controls` | Получить контролы для управления инструментами |
| DELETE | `/delete_tool/{tool_id}` | Удалить инструмент |

#### Библиотека инструментов (`/backend/tool-library`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/tool-library/{device_number}` | Добавить инструмент в библиотеку устройства |
| GET | `/tool-library/{device_number}` | Получить библиотеку инструментов устройства |
| PUT | `/tool-library/{device_number}/{tool_id}` | Обновить инструмент в библиотеке |
| DELETE | `/tool-library/{device_number}/{tool_id}` | Удалить инструмент из библиотеки |

#### Инструменты в вендинге (`/backend/tools-in-vending`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/tools-in-vending/{device_number}` | Получить инструменты в вендинговом аппарате |
| POST | `/tools-in-vending/{device_number}` | Добавить инструменты в вендинг |
| PUT | `/tools-in-vending/{device_number}/{plan_id}` | Обновить инструменты в вендинге |
| DELETE | `/tools-in-vending/{device_number}/{plan_id}` | Удалить инструменты из вендинга |

---

### Управление группами

#### Группы (`/backend/all_groups`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Получить инвентарь (группы с инструментами) |
| POST | `/create_groups` | Создать группу инструментов |
| GET | `/groups_by_device/{device_number}` | Получить группы по устройству |
| GET | `/groups_by_plan/{plan_id}` | Получить группы по плану |
| GET | `/groups_only` | Получить только список групп (без инструментов) |
| GET | `/groups_controls` | Получить контролы для управления группами |
| DELETE | `/delete_group/{group_id}` | Удалить группу |

---

### Управление планами (чертежами)

#### Планы (`/backend/all_plans`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/get_all_plans/{device_number}` | Получить все планы для устройства |
| GET | `/plans_by_device/{device_number}` | Получить планы по устройству |
| POST | `/create_plan/{device_number}` | Создать новый план (чертеж) |
| PUT | `/update_plan/{device_number}/{plan_id}` | Обновить план |
| DELETE | `/delete_plan/{device_number}/{plan_id}` | Удалить план |

---

### Управление ячейками

#### Ячейки (`/backend/cells`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/cells/{device_number}` | Получить карту ячеек устройства |
| POST | `/cells/{device_number}` | Создать новую ячейку |
| PUT | `/cells/{device_number}/{cell_id}` | Обновить ячейку |
| DELETE | `/cells/{device_number}/{cell_id}` | Удалить ячейку |

---

### Массовые операции

#### Массовая загрузка (`/backend/mass_load`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/mass_load_tools_by_free/{device_number}` | Получить инструменты для массовой загрузки (свободные) |
| GET | `/mass_load_tools_by_plan/{device_number}/{plan_id}` | Получить инструменты для массовой загрузки по плану |
| POST | `/mass_load_tools/{device_number}` | Выполнить массовую загрузку инструментов |

#### Массовая выгрузка (`/backend/mass_drop`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/mass_drop_tools/{device_number}` | Выполнить массовую выгрузку инструментов |

---

### История операций

#### Общая история (`/backend/history`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/history/{device_number}` | Получить историю операций устройства |
| POST | `/history/{device_number}` | Добавить запись в историю |
| PUT | `/history/{device_number}/{history_id}` | Обновить запись истории |
| DELETE | `/history/{device_number}/{history_id}` | Удалить запись истории |

#### История загрузок (`/backend/history-loads`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/random_load` | Получить случайную загрузку (для тестирования) |
| GET | `/history-loads/{device_number}` | Получить историю загрузок устройства |
| GET | `/history_loads` | Получить всю историю загрузок |
| POST | `/history-loads/{device_number}` | Добавить запись о загрузке |
| PUT | `/history-loads/{device_number}/{load_id}` | Обновить запись о загрузке |
| DELETE | `/history-loads/{device_number}/{load_id}` | Удалить запись о загрузке |

#### История выгрузок (`/backend/history_drops`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/random_drop` | Получить случайную выгрузку (для тестирования) |
| GET | `/history_drops` | Получить всю историю выгрузок |

#### История операций (`/backend/history-operation`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/history-operation/{device_number}` | Получить историю операций устройства |
| POST | `/history-operation/{device_number}` | Добавить операцию в историю |
| PUT | `/history-operation/{device_number}/{op_id}` | Обновить операцию |
| DELETE | `/history-operation/{device_number}/{op_id}` | Удалить операцию |

#### История ошибок (`/backend/history/error`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/history/error/{device_number}` | Получить историю ошибок устройства |
| POST | `/history/error/{device_number}` | Добавить ошибку в историю |
| PUT | `/history/error/{device_number}/{error_id}` | Обновить запись об ошибке |
| DELETE | `/history/error/{device_number}/{error_id}` | Удалить запись об ошибке |

#### История списаний (`/backend/history-write_off`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/history-write_off/{device_number}` | Получить историю списаний устройства |
| POST | `/history-write_off/{device_number}` | Добавить запись о списании |
| PUT | `/history-write_off/{device_number}/{drop_id}` | Обновить запись о списании |
| DELETE | `/history-write_off/{device_number}/{drop_id}` | Удалить запись о списании |

#### История случайных загрузок (`/backend/history-random-load`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/history-random-load/{device_number}` | Получить историю случайных загрузок |
| POST | `/history-random-load/{device_number}` | Добавить случайную загрузку |
| PUT | `/history-random-load/{device_number}/{history_id}` | Обновить случайную загрузку |
| DELETE | `/history-random-load/{device_number}/{history_id}` | Удалить случайную загрузку |

---

### Управление устройствами

#### Устройства (`/backend/all_device`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/all_devices` | Получить список всех устройств |
| GET | `/device/{device_id}` | Получить информацию об устройстве |
| POST | `/create_device` | Создать новое устройство |
| PUT | `/update_device/{device_id}` | Обновить устройство |
| PATCH | `/patch_device/{device_id}` | Частичное обновление устройства |
| DELETE | `/delete_device/{device_id}` | Удалить устройство |

---

### Настройки системы

#### Настройки (`/backend/settings`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/settings` | Получить все настройки системы (сгруппированные по категориям) |
| PUT | `/settings/{setting_key}` | Обновить настройку |
| POST | `/settings/restart` | Перезапустить приложение (применить настройки) |
| GET | `/device-templates` | Получить шаблоны конфигурации устройств |
| GET | `/current-device-config/{device_number}` | Получить текущую конфигурацию устройства |

---

### Справочники

#### Статусы (`/backend/status`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/status` | Получить все статусы системы |
| GET | `/status/{status_id}` | Получить статус по ID |

#### Нормы (`/backend/get_all`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/get_all` | Получить все нормы |
| GET | `/get/{user_id}` | Получить нормы пользователя |
| POST | `/post/{user_id}` | Создать нормы для пользователя |
| PUT | `/put/{user_id}` | Обновить нормы пользователя |
| DELETE | `/delete/{user_id}/{tool_name}` | Удалить норму инструмента |
| DELETE | `/delete/{user_id}` | Удалить все нормы пользователя |

#### QR-сканер (`/backend/qr/`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/qr/` | Обработать данные QR-кода |

---

## Операции на клиенте

### Авторизация и идентификация

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_user_from_barcode` | READ | Чтение пользователя по штрих-коду |
| `read_db_authorization` | READ | Авторизация пользователя (логин/пароль) |
| `read_db_username` | READ | Получение имени пользователя по логину |
| `write_db_err_barcode_user` | WRITE | Запись ошибки: пользователь не найден по штрих-коду |
| `write_db_err_login` | WRITE | Запись ошибки авторизации |

**Экраны:** `screen_3_authorization`, `screen_4_authorization_err`, `screen_5_identification_err`, `screen_6_user`

---

### Выдача инструментов

#### Выбор инструмента

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_groups` | READ | Получить список групп инструментов |
| `read_db_tool_names` | READ | Получить названия инструментов по группе |
| `read_db_tools_by_group_id` | READ | Получить инструменты по группе |
| `read_db_rights_tool` | READ | Проверка прав на выдачу инструмента |
| `read_db_get_cell` | READ | Получить ячейку для выдачи инструмента |
| `read_db_get_cells` | READ | Получить список ячеек для плана |
| `read_db_get_more_cells` | READ | Получить следующую ячейку из списка |

**Экраны:** `screen_7_select_group`, `screen_8_select_tool`, `screen_10_confirmation`

#### Выдача по плану

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_plan_id` | READ | Получить план по штрих-коду |
| `read_db_get_tools` | READ | Получить инструменты по плану |
| `read_db_get_plan_tools` | READ | Получить инструменты плана |
| `read_db_plan_complete` | READ | Проверка завершения плана |
| `write_db_plan_complete` | WRITE | Отметить план как завершенный |
| `read_db_tools_by_plans_id` | READ | Получить инструменты по ID планов |

**Экраны:** `screen_9_select_tool_by_plan`, `screen_33_select_plan`, `screen_35_plan_complete_confirmation`

#### Выдача инструмента

| Операция | Метод | Описание |
|----------|-------|----------|
| `write_db_tool_consumption` | WRITE | Записать выдачу инструмента (расход) |
| `write_db_err_rights` | WRITE | Записать ошибку прав доступа |
| `write_db_err_devices` | WRITE | Записать ошибку устройства |
| `write_db_err_timeout` | WRITE | Записать ошибку таймаута |

**Экраны:** `screen_11_tool_issued`, `screen_12_no_tool`, `screen_13_no_right`

---

### Массовые операции (клиент)

#### Массовая загрузка

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_mass_load_tools` | READ | Получить инструменты для массовой загрузки |
| `read_db_mass_load_tools_by_plan` | READ | Получить инструменты для массовой загрузки по плану |
| `write_db_mass_load_tools_by_plan` | WRITE | Создать массовую загрузку по плану |
| `write_db_mass_load_tools_by_free` | WRITE | Создать массовую загрузку свободных инструментов |
| `write_db_load_tool_groups` | WRITE | Подтвердить массовую загрузку (освободить ячейки) |
| `read_cnf_lock_load` | READ | Проверка блокировки массовой загрузки |
| `write_cnf_lock_load` | WRITE | Установить блокировку массовой загрузки |

**Экраны:** `screen_15_mass_load`, `screen_16_mass_load_ok`

#### Массовая выгрузка

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_mass_drop_tools` | READ | Получить инструменты для массовой выгрузки |
| `read_db_mass_drop_tools_by_plan` | READ | Получить инструменты для массовой выгрузки по плану |
| `read_db_mass_drop_tools_by_free` | READ | Получить свободные инструменты для массовой выгрузки |
| `write_db_mass_drop_tools_by_plan` | WRITE | Создать массовую выгрузку по плану |
| `write_db_mass_drop_tools_by_free` | WRITE | Создать массовую выгрузку свободных инструментов |
| `write_db_drop_tool_groups` | WRITE | Подтвердить массовую выгрузку (освободить ячейки) |
| `read_cnf_lock_drop` | READ | Проверка блокировки массовой выгрузки |
| `write_cnf_lock_drop` | WRITE | Установить блокировку массовой выгрузки |

**Экраны:** `screen_17_mass_drop`, `screen_18_mass_drop_ok`

---

### Управление складом

#### Управление группами

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_group_collection` | READ | Получить коллекцию групп для управления |
| `read_db_tools_collection` | READ | Получить коллекцию инструментов группы |

**Экраны:** `screen_19_management_group`, `screen_20_management_tool`

---

### Просмотр истории

#### История операций

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_history` | READ | Получить историю операций |
| `read_db_summary` | READ | Получить сводку (использует read_db_history) |
| `read_db_user_operations` | READ | Получить операции пользователя |
| `read_db_plan_operations` | READ | Получить операции по плану |
| `read_db_err_history` | READ | Получить историю ошибок |

**Экраны:** `screen_21_summary`, `screen_22_users`, `screen_23_plans`, `screen_24_history_by_plan`, `screen_25_history_by_user`, `screen_27_history_err`

---

### Администрирование

#### Управление пользователями

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_users` | READ | Получить список пользователей |
| `write_db_users` | WRITE | Обновить пользователей (синхронизация с сервером) |
| `read_db_rights_by_user_id` | READ | Получить права пользователя |
| `write_db_rights_by_user_id` | WRITE | Обновить права пользователя |

**Экраны:** `screen_22_users`

#### Управление планами

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_plans` | READ | Получить список планов |
| `read_db_plan` | READ | Получить план по индексу |
| `write_db_plans` | WRITE | Обновить планы (синхронизация с сервером) |

**Экраны:** `screen_23_plans`, `screen_33_select_plan`

#### Настройки системы

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_cnf_serial` | READ | Чтение настроек последовательного порта |
| `write_cnf_serial` | WRITE | Запись настроек последовательного порта |
| `read_cnf_IP` | READ | Чтение настроек сети (IP) |
| `write_cnf_IP` | WRITE | Запись настроек сети (IP) |
| `write_cnf_network` | WRITE | Запись сетевых настроек |
| `cmd_test_is_free` | CMD | Тест свободной ячейки (последовательный порт) |
| `cmd_ping` | CMD | Проверка сетевого соединения |
| `cmd_reboot` | CMD | Перезагрузка системы |
| `cmd_stop` | CMD | Остановка системы |

**Экраны:** `screen_26_admin`, `screen_28_net_options`, `screen_29_serial_options`, `screen_30_shutdown`, `screen_31_reboot`

---

### Справочная информация

#### Помощь

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_help` | READ | Получить справочную информацию |
| `write_db_help` | WRITE | Обновить справочную информацию |

**Экраны:** `screen_2_help`

#### Ошибки

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_db_err` | READ | Получить информацию об ошибке |
| `write_db_err_request` | WRITE | Записать ошибку запроса |
| `write_db_err_get_tools_by_plan_id` | WRITE | Записать ошибку получения инструментов по плану |
| `write_db_err_barcode_plan` | WRITE | Записать ошибку: план не найден по штрих-коду |
| `write_log_critical_err` | WRITE | Записать критическую ошибку в лог |

**Экраны:** `screen_27_history_err`, `screen_5_identification_err`

---

## Служебные операции клиента

### Синхронизация

| Операция | Метод | Описание |
|----------|-------|----------|
| `http_post_request_send_data` | HTTP | Отправка данных на сервер |
| `http_get_request_take_command` | HTTP | Получение команд с сервера |
| `http_parse_answer` | HTTP | Парсинг ответа от сервера |
| `http_wait_post_answer` | HTTP | Ожидание ответа на POST запрос |
| `http_wait_get_answer` | HTTP | Ожидание ответа на GET запрос |

### Команды системы

| Операция | Метод | Описание |
|----------|-------|----------|
| `cmd_start` | CMD | Запуск системы |
| `cmd_stop` | CMD | Остановка системы |
| `cmd_test_self` | CMD | Самодиагностика системы |
| `cmd_run_timer_event` | CMD | Запуск таймерного события |
| `cmd_run_timeout_post_back` | CMD | Таймаут POST запроса с возвратом |
| `cmd_run_timeout_get_back` | CMD | Таймаут GET запроса с возвратом |
| `cmd_run_timeout_wait_back` | CMD | Таймаут ожидания с возвратом |
| `cmd_empty` | CMD | Пустая команда (нет данных) |
| `cmd_keyboard_toggle` | CMD | Переключение клавиатуры |

### Конфигурация

| Операция | Метод | Описание |
|----------|-------|----------|
| `read_cnf` | READ | Чтение конфигурации |
| `read_cnf_signature` | READ | Чтение подписи конфигурации |
| `write_cnf_unlock_load` | WRITE | Разблокировать массовую загрузку |
| `write_cnf_unlock_drop` | WRITE | Разблокировать массовую выгрузку |

---

## Экраны клиента

### Основные экраны

- **screen_1_welcome** - Главный экран (приветствие)
- **screen_2_help** - Справка
- **screen_3_authorization** - Авторизация
- **screen_4_authorization_err** - Ошибка авторизации
- **screen_5_identification_err** - Ошибка идентификации
- **screen_6_user** - Выбор пользователя
- **screen_7_select_group** - Выбор группы инструментов
- **screen_8_select_tool** - Выбор инструмента
- **screen_9_select_tool_by_plan** - Выбор инструмента по плану
- **screen_10_confirmation** - Подтверждение выдачи
- **screen_11_tool_issued** - Инструмент выдан
- **screen_12_no_tool** - Инструмент не найден
- **screen_13_no_right** - Нет прав доступа

### Экран кладовщика

- **screen_14_stockman** - Главное меню кладовщика

### Массовые операции

- **screen_15_mass_load** - Массовая загрузка
- **screen_16_mass_load_ok** - Массовая загрузка завершена
- **screen_17_mass_drop** - Массовая выгрузка
- **screen_18_mass_drop_ok** - Массовая выгрузка завершена

### Управление складом

- **screen_19_management_group** - Управление группами
- **screen_20_management_tool** - Управление инструментами

### История и отчеты

- **screen_21_summary** - Сводка
- **screen_22_users** - Пользователи
- **screen_23_plans** - Планы
- **screen_24_history_by_plan** - История по плану
- **screen_25_history_by_user** - История по пользователю
- **screen_27_history_err** - История ошибок

### Администрирование

- **screen_26_admin** - Администрирование
- **screen_28_net_options** - Настройки сети
- **screen_29_serial_options** - Настройки последовательного порта
- **screen_30_shutdown** - Выключение системы
- **screen_31_reboot** - Перезагрузка системы

### Служебные экраны

- **screen_32_wait** - Ожидание
- **screen_33_select_plan** - Выбор плана
- **screen_35_plan_complete_confirmation** - Подтверждение завершения плана

---

## Примечания

1. **Префиксы операций:**
   - `read_db_*` - операции чтения из базы данных
   - `write_db_*` - операции записи в базу данных
   - `read_cnf_*` - чтение конфигурации
   - `write_cnf_*` - запись конфигурации
   - `cmd_*` - системные команды
   - `http_*` - HTTP операции

2. **Синхронизация:** Большинство операций записи на клиенте автоматически синхронизируются с сервером через систему синхронизации (`dbSync`).

3. **Массовые операции:** Массовая загрузка и выгрузка требуют подтверждения пользователем перед применением изменений к ячейкам.

4. **Права доступа:** Многие операции проверяют права пользователя перед выполнением.

5. **Обработка ошибок:** Система логирует все ошибки в таблицу `Error` и историю ошибок.

---

*Документ создан на основе анализа кодовой базы AutoSklad. Последнее обновление: 2026-01-27*
