# План миграции: RPi + ATmega (HAL)

Перенос логики выдачи и координат с монолитного `.ino` на клиент PyQt5; ATmega — только исполнение по UART.

**Статус в чекбоксах:** `[x]` сделано, `[ ]` не сделано.

**Ссылки:** [hardware_barcode_relay_dispensing.md](hardware_barcode_relay_dispensing.md), [client_components_description.md](client_components_description.md).

---

## Легенда

| Поле | Значение |
|------|----------|
| **Статус этапа** | Краткая отметка по этапу в целом |
| Подзадачи | Отдельные чекбоксы |

---

## Наследие (кратко)

Сейчас контроллер: `SerialManager` + `$<номер>\r\n` и ответы `command_is_send` / `command_ok` (см. `serial_manager.py`, `action_cmd.py`, `state_map.py`). Сканер — второй порт. Известные долги: запись в COM из GUI, заглушки `write_db_err_*`, реле на `screen_14_stockman` параллельно будущему `$LOCK`.

---

## Справочник: целевой протокол (эталон)

**К RPi:** `$MOTn,x`, `$ZERO`, `$STOP`, `$MOTn_SPEED`, `$MOTn_BOOST`, `$LOCK,ms`, `$LOCK0`/`$LOCK1`, `$LED,x`, `$ALED,r,g,b`, `$SENS1`…`$SENS6`, при необходимости `$DISP,ms` (отдельно от `$LOCK`).

**От платы:** `OK`, `DONE`, `ERROR`, `SENSx_0/1`, в контракте оставить **`LOCK ON` / `LOCK OFF`**. Строки завершаются `\n`.

**В коде клиента для нового драйвера:** полезная нагрузка без `$` в API, окончание строки при отправке — `\n` (см. `vending_serial_manager.py`).

---

## Этап 1. Прошивка ATmega

**Статус этапа:** `[ ]` в работе / приёмка не зафиксирована в документе

|  | Задача |
|--|--------|
| [ ] | Стабильный `$ZERO`, синхронизация портала Z (при двух моторах), приёмка на стенде |
| [ ] | `$STOP` прерывает длительные движения; предсказуемый ответ |
| [ ] | `$DISP,ms` отдельно от `$LOCK` (люк выдачи) |
| [ ] | `$LOCK,ms` неблокирующий для приёма новых команд (`delay` убрать из основного цикла) |
| [ ] | Полный набор `$SENS1`…`$SENS6` или зафиксированное подмножество в спецификации |
| [ ] | Ответ на любую команду: без «молчаливых» веток (позже — по согласованию с клиентом) |
| [ ] | Краткий протокольный changelog / матрица тестов для Python |

---

## Этап 2. Клиент: драйвер, мок, интеграция

**Статус этапа:** `[x]` готово (`legacy` по умолчанию; `hardware.protocol: atmega_hal` — HAL + мост FSM)

|  | Задача |
|--|--------|
| [x] | Модуль `client/BarcodeScanner/vending_serial_manager.py` (построчное чтение, очередь TX, один полёт команды, `command_finished(cmd, outcome)`, таймауты, сигналы Qt) |
| [x] | Модуль `client/BarcodeScanner/dispense_command_gate.py` (вариант A: строго последовательные шаги, корреляция с `command_finished`, `threading.Lock`, без emit под lock) |
| [x] | `MockVendingSerialManager` (`client/BarcodeScanner/MockVendingSerialManager.py`): `OK`/`DONE`/`ERROR`, `LOCK ON`/`OFF`, `SENS`, `MOCKFAIL` |
| [x] | Флаг `hardware.protocol` в `config.json`: `legacy` \| `atmega_hal` (выбор в `main.py`; env `AUTOSKLAD_USE_MOCKS` по-прежнему включает моки) |
| [x] | Подключение в `main.py`: контроллер → `VendingSerialManager` / мок HAL, `start()`, `executor.controller_protocol`, опционально `hal_test_scenario_path` + `DispenseCommandGate` |
| [x] | `Executor` / `MainWindow`: для `atmega_hal` в `button_clicked` только мост `fsm_trigger` (`command_is_send` / `command_ok` / `err_devices`); полный сценарий выдачи — этап 3 (`action_dispense` + gate) |
| [x] | Унификация отправки: `Executor.send_controller_command` → `enqueue_command` (HAL) или `command_queue` (legacy); `action_cmd.cmd_send` через него |

---

## Этап 3. БД, кинематика, FSM

**Статус этапа:** `[x]` реализовано для `atmega_hal` (legacy оставлен без изменений)

|  | Задача |
|--|--------|
| [x] | Кинематика вынесена в `config.json` (`hardware.hal_motion_profile`, per-cell профиль в `cells`), legacy `Cell.number` сохранён без изменений |
| [x] | Старт приложения: `$ZERO` до допуска логина (startup-контракт для `atmega_hal`: проверка связи, `ZERO`, парковка `MOT1..MOT5 -> 0`, `LOCK1`; при сбое — `err_devices`) |
| [x] | HAL-сценарий выдачи в `cmd_send`: свет → MOT X/Z → MOT5 вниз/вверх → парковка → `$LOCK,ms`; исполнение через `DispenseCommandGate` |
| [x] | FSM-секвенсор для HAL: мгновенный переход в wait (`command_is_send`), успех по отложенному `command_ok`, ошибки/таймауты через `err_devices` |
| [x] | Списание в БД синхронизировано с `$LOCK,ms`: `command_ok` генерируется по **QTimer(lock_ms)** после завершения HAL-цепочки |
| [x] | `ERROR`/таймаут: стоп сценария, без списания, запись в `Error`, реализованы `write_db_err_devices` / `write_db_err_timeout` с переходом в аппаратную ошибку |
| [x] | Экран «Сбой механики» (`screen_36_hardware_err`): только кнопка возврата, без retry/инженерного меню; подключён в FSM по `err_devices`/таймаутам |

---

## Этап 4. UI и инженерное меню

**Статус этапа:** `[ ]` не начато

|  | Задача |
|--|--------|
| [ ] | Расширить `screen_26_admin` или `screen_hardware_test`: SPEED/BOOST, jog, опрос `$SENS`, сохранение X/Z в ячейку |
| [ ] | Согласовать GPIO реле кладовщика с `$LOCK` (убрать дублирование или разнести контуры) |

---

## Этап 5. Документация и приёмка

**Статус этапа:** `[ ]` не начато

|  | Задача |
|--|--------|
| [ ] | Обновить `docs/hardware_barcode_relay_dispensing.md` под фактический протокол |
| [ ] | **DoD:** полный цикл на моке; на стенде выдача из БД по мм; `$ZERO` при старте; инженерный экран; ошибки в `Error` и синк |

---

## Риски (кратко)

| Риск | Мера |
|------|------|
| Несколько `DONE` / рассинхрон | Последовательный gate + корреляция `command_finished` |
| Обрыв строк / буфер | Только `readline`, не `read_all` для текста |
| Долгий `$LOCK` на прошивке | Неблокирующий lock + таймауты на клиенте |

---

## Карта файлов

| Назначение | Путь |
|------------|------|
| Драйвер v0 | `client/BarcodeScanner/vending_serial_manager.py` |
| Очередь шагов выдачи | `client/BarcodeScanner/dispense_command_gate.py` |
| Старый COM | `client/BarcodeScanner/serial_manager.py` |
| Мок | `client/BarcodeScanner/MockSerialManager.py` |
| Вход в приложение | `client/main.py`, `EventsSystem/Executor.py`, `GUI/MainWindow.py` |
| FSM | `client/StateMachine/state_map.py` |
| БД ячеек | `client/DB/Models/Cell.py`, `DB/Engine/CellCRUD.py` |
| Прошивка (новая) | `client/MegaHardware/Vending_NEW.ino` |

---

*Номера моторов, мм↔шаги и тайминги фиксируются в спецификации станка и в ревизии прошивки.*
