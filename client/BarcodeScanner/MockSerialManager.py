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
        print(f"[MockSerial] Отправка: ${data}\\r\\n")
        # имитируем ответ контроллера: $1 -> $2
        self.signal_received.emit('command_is_send')
        # небольшая задержка и успешное завершение
        time.sleep(0.2)
        self.signal_received.emit('command_ok')

    def run(self):
        self.open_port()
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command.startswith("send:"):
                    data_to_send = command.split("send:")[1]
                    self.send_data(data_to_send)
            time.sleep(0.05)
        self.close_port()

    def stop(self):
        self.running = False
