import traceback

from BarcodeScanner.serial_manager import SerialManager
from Cnf.Models import SignatureConfig
from DB.Models.Plan import Plan
from EventsSystem.action_selector import ActionSelector
from EventsSystem.state_router import StateRouter



class Executor:

    def __init__(self):
        self.selector = ActionSelector(self)
        self.router = StateRouter(self.selector.mappers)
        self.controller_serial_manager = None
        self.handle_barcode_manager = lambda response: print(f"Ответ получен: {response}")
        self.barcode_manager = lambda response: print(f"Ответ получен: {response}")
        self.handle_serial_controller = lambda response: print(f"Ответ получен: {response}")
        self.handle_serial_barcode_reader = lambda response: print(f"Ответ получен: {response}")

    def handle_widget_executor(self, start, current, map, value, handle_callback_executor):

        # Если value не задан или ложное, задаём значение по умолчанию
        if not value:
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
            print(e, traceback.extract_stack())
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
        """Подключаем уже запущенный SerialManager"""
        self.controller_serial_manager = serial_manager
        self.controller_serial_manager.signal_received.connect(self.handle_controller_serial_response)

    def handle_controller_serial_response(self, response):
        """Обрабатываем полученный ответ"""

        self.handle_serial_controller(response)

        if response == "Ok":
            print("`Ok` - переключаем на экран ожидания")
        elif response == "command_ok":
            print("`command_ok` - процесс завершён")

    def cmd_send(self, number, tool_name):
        """Отправка команды в очередь SerialManager"""
        if self.controller_serial_manager:
            print(f"Отправка: {number} | Инструмент: {tool_name}")
            self.controller_serial_manager.command_queue.put(f"send:{number}")
        else:
            print("SerialManager не запущен!")

    def attach_barcode_manager(self, barcode_manager):
        """Подключаем уже запущенный SerialManager"""
        self.barcode_manager = barcode_manager
        self.barcode_manager.signal_received.connect(self.handle_barcode_response)

    def handle_barcode_response(self, response):
        """Обрабатываем полученный ответ"""
        self.handle_barcode_manager(response)
        print(f"barcode: {response}")
