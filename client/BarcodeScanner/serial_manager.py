import traceback

import serial
import time
import queue
import threading
from PyQt5.QtCore import QObject, pyqtSignal

class SerialManager(threading.Thread, QObject):
    signal_received = pyqtSignal(str)  # Сигнал для GUI при получении ответа

    def __init__(self, port="COM30", baudrate=9600, timeout=1):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None

        # Очереди
        self.command_queue = queue.Queue()
        self.running = True

    def open_port(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Порт {self.port} открыт.")
        except Exception as e:
            print(f"Ошибка порта {self.port}: {e}")
            self.serial_conn = None

    def close_port(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print(f"Порт {self.port} закрыт.")

    # def send_data(self, data):
    #     if self.serial_conn and self.serial_conn.is_open:
    #         # Формируем строку, которая будет выглядеть как "\$65"
    #         payload_str = "\\$" + str(data) + '\\r' + '\\n'
    #         payload_bytes = payload_str.encode()
    #         # Формируем строку для вывода в нужном формате
    #         output_str = 'Отправка: b"\\${}"'.format(data)
    #         print(output_str)
    #         self.serial_conn.write(payload_bytes)

    def send_data(self, data):
        if self.serial_conn and self.serial_conn.is_open:
            # Формируем строку, которая будет выглядеть как "$65\r\n"
            payload_str = "$" + str(data) + "\r\n"
            payload_bytes = payload_str.encode()
            output_str = 'Отправка: ' + repr(payload_bytes)
            print(output_str)
            self.serial_conn.write(payload_bytes)

    def raw_read_data(self):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                raw_response = self.serial_conn.read_all()
                if raw_response:
                    print(f"Получено: {raw_response}")

                    # Проверка для БАЙТОВ:
                    if len(raw_response) >= 3 and raw_response.startswith(b'$') and raw_response.endswith(b'\n'):
                        response = raw_response[1:-1].strip().decode()

                        if response.isdigit():
                            if response == '1':
                                self.signal_received.emit('command_is_send')
                            elif response == '2':
                                self.signal_received.emit('command_ok')
                    else:
                        print("Некорректный формат:", raw_response)

            except Exception as e:
                print(f"Ошибка чтения: {e}")

    def read_data(self):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                response = self.serial_conn.readline().decode().strip()
                if response:
                    # print(f"Получено: {response}")

                    if int(response) == 1:
                        response = 'command_is_send'
                    elif int(response) == 2:
                        response = 'command_ok'

                    self.signal_received.emit(response)  # Отправляем сигнал в GUI
            except Exception as e:
                print(traceback.format_exc())
                print(f"[{__file__}][{__name__}]Ошибка чтения: {e}")

    def run(self):
        self.open_port()
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command.startswith("send:"):
                    data_to_send = command.split("send:")[1]
                    self.send_data(data_to_send)

            self.raw_read_data()
            time.sleep(0.1)

        self.close_port()

    def stop(self):
        self.running = False
