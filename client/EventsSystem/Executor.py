import logging
import traceback
from collections import deque
from typing import Optional

from BarcodeScanner.serial_manager import SerialManager

logger = logging.getLogger(__name__)
from Cnf.Models import SignatureConfig
from DB.Models.Plan import Plan
from EventsSystem.action_selector import ActionSelector
from EventsSystem.state_router import StateRouter



class Executor:

    def __init__(self):
        self.selector = ActionSelector(self)
        self.router = StateRouter(self.selector.mappers)
        self.controller_serial_manager = None
        # `legacy` = номер ячейки ($n); `atmega_hal` = VendingSerialManager (WAIT/DONE, MOT,p1..p5)
        self.controller_protocol: str = "legacy"
        # Глобальный контекст состояния железа для startup-проверки и экрана аппаратной ошибки.
        self.hardware_ready: bool = False
        self.hardware_last_error: str = ""
        # Контекст ожидания screen_32_wait для инженера: None | 'park' | 'dispense'
        self.engineer_wait_context: Optional[str] = None
        # Текущий вектор шагов M1..M5 (последние отправленные/подтверждённые)
        self.hal_motor_positions: list = [0, 0, 0, 0, 0]
        self.hal_projected_x: int = 0
        self.hal_projected_z: int = 0
        # hal_x/hal_z для «Сохранить координаты» (M3→hal_x, M1→hal_z на screen_38)
        self.hal_save_hal_x: Optional[int] = None
        self.hal_save_hal_z: Optional[int] = None
        # Подпись на screen_32_wait («Парковка…», «Тестовая выдача…»)
        self.wait_screen_message: str = ""
        # Номер ячейки для инженерных экранов (ввод / выбор из таблицы)
        self.engineer_cell_number: Optional[int] = None
        # Последний триггер JOG (hal_jog_x_plus и т.д.)
        self.last_hal_jog_trigger: str = ""
        # Шаг JOG с screen_38 (1 / 5 / 10 / 50 / 100), по умолчанию 50
        self.hal_jog_step: int = 50
        # Целевой вектор MOT для кнопки «Отправка» на screen_38
        self.hal_mot_goto_positions: Optional[list] = None
        # Последние строки UART (HAL) для диагностики при command_finished / FSM.
        self._hal_rx_recent: deque[str] = deque(maxlen=48)
        self.handle_barcode_manager = lambda response: logger.debug("Ответ получен: %s", response)
        self.barcode_manager = lambda response: logger.debug("Ответ получен: %s", response)
        self.handle_serial_controller = lambda response: logger.debug("Ответ получен: %s", response)
        self.handle_serial_barcode_reader = lambda response: logger.debug("Ответ получен: %s", response)

    def handle_widget_executor(self, start, current, map, value, handle_callback_executor):

        # Результат read_cnf_lock_drop (True/False) при переходе в read_db_mass_drop_tools:
        # брать последнюю MassDrop, не искать по id (проверять до «not value»)
        if isinstance(value, bool):
            value = {"index": None}
        # Если value не задан или ложное, задаём значение по умолчанию
        elif not value:
            value = {"index": 0}
        # Если value не является словарём, оборачиваем его в словарь
        elif isinstance(value, Plan):
            value = {"plan_id": value.id}
        elif isinstance(value, SignatureConfig):
            value = {"serial_number": value.serial_number}
        # elif value:
        #     value = {"serial_number": value['trigger']}
        mapper = self.selector.get_mapper(current)
        result = {'trigger':'err_authorization'}
        try:
            if isinstance(value, dict):
                result = mapper.execute(current, **value)
            elif isinstance(value, (tuple, list)) and value:
                # Если value - кортеж или список, распаковываем как позиционные аргументы
                result = mapper.execute(current, *value)
            elif value is None:
                # Если value None, используем значение по умолчанию
                result = mapper.execute(current, {"index": 0})
            else:
                return result, map.state()
        except Exception as e:
            logger.exception("Executor exception: %s", e)
        back_state = map.state()
        key = None
        if isinstance(result, dict):
            key = result.keys()
            if 'trigger' in key:
                trigger = result['trigger']
                map.lump.trigger(trigger)
                return result, map.state()
            else:
                trigger = self.router.find_transition_trigger(start, current, result, handle_callback_executor)
                if trigger is None:
                    raise ValueError("Trigger не задан, проверьте логику формирования события")
                map.lump.trigger(trigger)
                return result, map.state()
        else:
            trigger = self.router.find_transition_trigger(start, current, result, handle_callback_executor)
            if trigger is None:
                trigger = "err_authorization"
                # raise ValueError("Trigger не задан, проверьте логику формирования события")
            map.lump.trigger(trigger)
            return result, map.state()

    def format_hal_rx_snapshot(self) -> str:
        """Сжатый журнал последних принятых строк UART (HAL), для логов при ошибках/успехе."""
        if not self._hal_rx_recent:
            return "(empty)"
        return " | ".join(self._hal_rx_recent)

    def _on_hal_raw_line(self, line: str) -> None:
        text = (line or "").strip()
        if text:
            self._hal_rx_recent.append(text)

    def _on_hal_command_finished_log(self, cmd: str, outcome: str) -> None:
        snap = self.format_hal_rx_snapshot()
        if outcome in ("timeout_ack", "timeout_done"):
            logger.warning(
                "HAL UART command_finished cmd=%r outcome=%s recent_rx=%s",
                cmd,
                outcome,
                snap,
            )
        elif outcome == "error":
            logger.error(
                "HAL UART command_finished cmd=%r outcome=%s recent_rx=%s",
                cmd,
                outcome,
                snap,
            )
        elif outcome in ("done", "ok_short"):
            logger.info(
                "HAL UART command_finished cmd=%r outcome=%s recent_rx=%s",
                cmd,
                outcome,
                snap,
            )
        else:
            logger.info(
                "HAL UART command_finished cmd=%r outcome=%s recent_rx=%s",
                cmd,
                outcome,
                snap,
            )

    def attach_serial_manager(self, serial_manager):
        """Подключаем уже запущенный SerialManager или VendingSerialManager / mock HAL."""
        self.controller_serial_manager = serial_manager
        # Для HAL не вешаем низкоуровневый fsm_trigger напрямую на GUI/FSM:
        # переходы управляются action-слоем (cmd_send/cmd_test_self + gate).
        if self.controller_protocol == "atmega_hal":
            if hasattr(serial_manager, "raw_line"):
                serial_manager.raw_line.connect(self._on_hal_raw_line)
            if hasattr(serial_manager, "command_finished"):
                serial_manager.command_finished.connect(self._on_hal_command_finished_log)
            cmd_mapper = self.selector.mappers.get("cmd")
            if cmd_mapper is not None and hasattr(cmd_mapper, "wire_hal_pulse_handlers"):
                cmd_mapper.wire_hal_pulse_handlers(serial_manager)
            return
        if hasattr(serial_manager, "fsm_trigger"):
            serial_manager.fsm_trigger.connect(self.handle_controller_serial_response)
        else:
            self.controller_serial_manager.signal_received.connect(
                self.handle_controller_serial_response
            )

    def handle_controller_serial_response(self, response):
        """Обрабатываем полученный ответ"""

        self.handle_serial_controller(response)

        if response == "Ok":
            logger.debug("`Ok` - переключаем на экран ожидания")
        elif response == "command_ok":
            logger.debug("`command_ok` - процесс завершён")

    def send_controller_command(
        self, payload: str, *, is_long: Optional[bool] = None
    ) -> bool:
        """
        Единая точка отправки на контроллер: очередь TX HAL (enqueue) или legacy command_queue;
        не вызывать send_data с экранов напрямую.
        """
        if not self.controller_serial_manager:
            logger.warning("SerialManager не запущен!")
            return False
        mgr = self.controller_serial_manager
        if hasattr(mgr, "enqueue_command"):
            if is_long is not None:
                mgr.enqueue_command(str(payload), is_long=is_long)
            else:
                mgr.enqueue_command(str(payload))
        elif hasattr(mgr, "command_queue"):
            mgr.command_queue.put(f"send:{payload}")
        else:
            logger.warning("Контроллер не поддерживает enqueue_command/command_queue")
            return False
        return True

    def cmd_send(self, number, tool_name):
        """Отправка команды в очередь SerialManager / HAL."""
        if not number:
            logger.warning("cmd_send number: %s is None, tool_name: %s", number, tool_name)
            return
        logger.debug("Отправка: %s | Инструмент: %s", number, tool_name)
        self.send_controller_command(str(number))

    def attach_barcode_manager(self, barcode_manager):
        """Подключаем уже запущенный SerialManager"""
        self.barcode_manager = barcode_manager
        self.barcode_manager.signal_received.connect(self.handle_barcode_response)

    def handle_barcode_response(self, response):
        """Обрабатываем полученный ответ"""
        self.handle_barcode_manager(response)
        logger.debug("barcode: %s", response)
