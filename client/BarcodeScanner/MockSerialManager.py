import time
import queue
import threading
from PyQt5.QtCore import QObject, pyqtSignal


class MockSerialManager(threading.Thread, QObject):
    signal_received = pyqtSignal(str)

    def __init__(self, port=None, baudrate=9600, timeout=1):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.command_queue = queue.Queue()
        self.running = True

    def open_port(self):
        print("[MockSerial] Открытие виртуального порта")

    def close_port(self):
        print("[MockSerial] Закрытие виртуального порта")

    def send_data(self, data):
        """Добавляет команду в очередь для обработки в отдельном потоке"""
        print(f"[MockSerial] Добавление в очередь: ${data}")
        self.command_queue.put(f"send:{data}")

    def _process_command(self, data):
        """Обрабатывает команду в отдельном потоке (не блокирует GUI)"""
        print(f"[MockSerial] Отправка: ${data}\\r\\n")
        # имитируем ответ контроллера: $1 -> $2
        self.signal_received.emit('command_is_send')
        # задержка 20 сек для имитации работы Arduino (открытие ячейки)
        print("[MockSerial] Ожидание 2 сек (имитация работы Arduino)...")
        time.sleep(2)
        self.signal_received.emit('command_ok')
        print("[MockSerial] Команда выполнена успешно")

    def run(self):
        self.open_port()
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command.startswith("send:"):
                    data_to_send = command.split("send:")[1]
                    self._process_command(data_to_send)
            time.sleep(0.05)
        self.close_port()

    def stop(self):
        self.running = False
