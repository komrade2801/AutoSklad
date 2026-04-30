import logging
import traceback
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
        # `legacy` = номер ячейки ($n); `atmega_hal` = VendingSerialManager (очередь OK/DONE)
        self.controller_protocol: str = "legacy"
        # Глобальный контекст состояния железа для startup-проверки и экрана аппаратной ошибки.
        self.hardware_ready: bool = False
        self.hardware_last_error: str = ""
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

    def attach_serial_manager(self, serial_manager):
        """Подключаем уже запущенный SerialManager или VendingSerialManager / mock HAL."""
        self.controller_serial_manager = serial_manager
        # Для HAL не вешаем низкоуровневый fsm_trigger напрямую на GUI/FSM:
        # переходы управляются action-слоем (cmd_send/cmd_test_self + gate).
        if self.controller_protocol == "atmega_hal":
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
