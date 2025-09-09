import serial
import time
import queue
import threading
from PyQt5.QtCore import QObject, pyqtSignal

class SerialManagerCRC(threading.Thread, QObject):
    signal_received = pyqtSignal(str)  # Сигнал для GUI при получении ответа

    def __init__(self, port="COM30", baudrate=9600, timeout=1):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None

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


    def send_data_crc(self, command_code: int, data: bytes = b''):
        """
        Формирует и отправляет сообщение через COM-порт согласно следующему протоколу:
          [STX][CMD][LEN][DATA][CRC][ETX]
        где:
          - STX = 0x02
          - CMD — код команды (один байт)
          - LEN — длина данных (один байт)
          - DATA — полезная нагрузка (если есть)
          - CRC — контрольная сумма (сумма байтов от CMD до конца DATA по модулю 256)
          - ETX = 0x03

        :param command_code: Код команды в виде целого числа (например, 0x01 для command_is_send).
        :param data: Дополнительные данные (по умолчанию пусто).
        """
        print(f"Обработка command_code: {command_code}")
        STX = b'\x02'
        ETX = b'\x03'
        # Преобразуем команду и длину данных в байты
        CMD = command_code.to_bytes(1, byteorder='big')
        LEN = len(data).to_bytes(1, byteorder='big')
        # Вычисляем CRC как сумму байтов от CMD до конца DATA по модулю 256
        crc_val = (sum(CMD) + sum(LEN) + sum(data)) & 0xFF
        CRC = crc_val.to_bytes(1, byteorder='big')
        message = STX + CMD + LEN + data + CRC + ETX
        print(f"Отправка message: {message}")
        self.serial_conn.write(message)


    def read_data(self):
        """
        Чтение данных из COM-порта в виде байтов.
        После получения данных вызывается обработка сообщения.
        """
        if self.serial_conn and self.serial_conn.is_open:
            try:
                # Читаем байтовую строку без декодирования
                response = self.serial_conn.readline().strip()
                if response:
                    print(f"Получено: {response}")
                    self.handle_controller_serial_response(response)
                    # Для GUI отправляем текстовое представление
                    self.signal_received.emit(response.hex())
            except Exception as e:
                print(f"Ошибка чтения: {e}")

    def handle_serial_controller(self, parsed_response):
        """Простой обработчик разобранного сообщения (можно расширить логику)."""
        print("Обработанное сообщение:", parsed_response)

    def handle_controller_serial_response(self, response: bytes):
        """
        Обрабатываем полученный ответ:
          - Проверяем, что сообщение начинается с STX (0x02) и заканчивается ETX (0x03)
          - Извлекаем поля: CMD, LEN, DATA, CRC
          - Вычисляем CRC и сравниваем с полученным значением
          - Преобразуем код команды в строковое представление (например, 0x01 -> 'command_is_send', 0x02 -> 'command_ok')
        После чего передаём разобранное сообщение в handle_serial_controller.
        """
        try:
            # Проверка формата сообщения
            if not (response.startswith(b'\x02') and response.endswith(b'\x03')):
                raise ValueError("Сообщение не соответствует формату: отсутствует STX или ETX")
            if len(response) < 6:
                raise ValueError("Сообщение слишком короткое для обработки")

            # Формат: [STX][CMD][LEN][DATA (LEN байт)][CRC][ETX]
            cmd = response[1]
            length = response[2]
            expected_length = length + 5  # 1 (STX) + 1 (CMD) + 1 (LEN) + length (DATA) + 1 (CRC) + 1 (ETX)
            if len(response) != expected_length:
                raise ValueError("Длина сообщения не соответствует указанной длине данных")
            data = response[3:3 + length]
            crc_received = response[3 + length]

            # Вычисляем CRC: сумма байтов от CMD до конца DATA по модулю 256
            crc_calculated = sum(response[1:3 + length]) & 0xFF
            if crc_calculated != crc_received:
                raise ValueError("Контрольная сумма (CRC) не совпадает")

            # Преобразуем код команды в строковое представление
            command_mapping = {0x01: "command_is_send", 0x02: "command_ok"}
            command_str = command_mapping.get(cmd, f"unknown_command_{cmd}")

            parsed_response = {"command": command_str, "data": data}
            self.handle_serial_controller(parsed_response)

            if parsed_response.get("command") == "command_ok":
                print("`command_ok` - процесс завершён")
            elif parsed_response.get("command") == "command_is_send":
                print("`command_is_send` - переключаем на экран ожидания")
        except Exception as e:
            print(f"Ошибка при обработке ответа: {e}")
            self.handle_serial_controller({"error": str(e)})

    def run(self):
        self.open_port()
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command.startswith("send:"):
                    data_to_send = command.split("send:")[1]
                    self.send_data(data_to_send)
            self.read_data()
            time.sleep(0.1)
        self.close_port()

    def stop(self):
        self.running = False
