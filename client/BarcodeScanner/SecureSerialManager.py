import serial
import time
import queue
import threading
from PyQt5.QtCore import QObject, pyqtSignal
from cryptography.fernet import Fernet
from datetime import datetime


class SecureSerialManager(threading.Thread, QObject):
    """
    Класс для работы с COM-портом с шифрованием и интегрированным протоколом:
      [STX][CMD][LEN][DATA][CRC][ETX]

    DATA (полезная нагрузка) шифруется с помощью Fernet.
    CRC рассчитывается как сумма байтов от CMD до конца зашифрованных данных по модулю 256.
    """
    signal_received = pyqtSignal(str)  # Сигнал для GUI с текстовым представлением полученного сообщения

    STX = b'\x02'
    ETX = b'\x03'

    def __init__(self, port="COM30", baudrate=9600, timeout=1, key: bytes = None):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None

        # Очередь для команд отправки
        self.command_queue = queue.Queue()
        self.running = True

        # Если ключ не задан, генерируем новый. Убедитесь, что оба устройства используют один и тот же ключ.
        self.key = key if key is not None else Fernet.generate_key()
        self.cipher = Fernet(self.key)
        print(f"Используем ключ шифрования: {self.key.decode()}")  # для отладки

    def open_port(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Порт {self.port} открыт.")
        except Exception as e:
            print(f"Ошибка открытия порта {self.port}: {e}")
            self.serial_conn = None

    def close_port(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print(f"Порт {self.port} закрыт.")

    def build_message(self, command_code: int, payload: bytes = b'') -> bytes:
        """
        Формирует сообщение согласно протоколу:
          [STX][CMD][LEN][DATA][CRC][ETX]
        DATA шифруется. CRC — контрольная сумма (сумма байтов от CMD до конца DATA по модулю 256).
        """
        # Шифруем полезную нагрузку, если она есть
        encrypted_payload = self.cipher.encrypt(payload) if payload else b''
        CMD = command_code.to_bytes(1, byteorder='big')
        LEN = len(encrypted_payload).to_bytes(1, byteorder='big')
        # Вычисляем CRC: сумма байтов от CMD, LEN и зашифрованных данных по модулю 256
        crc_val = (sum(CMD) + sum(LEN) + sum(encrypted_payload)) & 0xFF
        CRC = crc_val.to_bytes(1, byteorder='big')
        message = self.STX + CMD + LEN + encrypted_payload + CRC + self.ETX
        return message

    def parse_message(self, message: bytes) -> dict:
        """
        Разбирает сообщение по протоколу, проверяет CRC и расшифровывает DATA.
        Возвращает словарь с ключами 'command' и 'data'.
        """
        if not (message.startswith(self.STX) and message.endswith(self.ETX)):
            raise ValueError("Неверный формат: отсутствует STX или ETX")
        if len(message) < 6:
            raise ValueError("Сообщение слишком короткое для обработки")
        CMD = message[1]
        LEN = message[2]
        expected_length = LEN + 5  # 1+1+1+LEN+1+1
        if len(message) != expected_length:
            raise ValueError("Длина сообщения не соответствует данным")
        encrypted_payload = message[3:3 + LEN]
        CRC_received = message[3 + LEN]
        crc_calculated = sum(message[1:3 + LEN]) & 0xFF
        if crc_calculated != CRC_received:
            raise ValueError("Контрольная сумма не совпадает")
        # Расшифровываем DATA, если она не пуста
        payload = self.cipher.decrypt(encrypted_payload) if encrypted_payload else b''
        command_mapping = {0x01: "command_is_send", 0x02: "command_ok"}
        command_str = command_mapping.get(CMD, f"unknown_command_{CMD}")
        return {"command": command_str, "data": payload}

    def send_message(self, command_code: int, payload: bytes = b''):
        """
        Формирует сообщение с заданной командой и полезной нагрузкой и отправляет его через COM-порт.
        """
        if self.serial_conn and self.serial_conn.is_open:
            message = self.build_message(command_code, payload)
            print(f"Отправка: {message}")
            self.serial_conn.write(message)
        else:
            print("Порт не открыт. Невозможно отправить сообщение.")

    def read_data(self):
        """
        Чтение данных из COM-порта.
        После получения данных, вызывается обработка (парсинг и расшифровка).
        """
        if self.serial_conn and self.serial_conn.is_open:
            try:
                message = self.serial_conn.readline().strip()
                if message:
                    print(f"Получено: {message}")
                    try:
                        parsed = self.parse_message(message)
                        self.handle_serial_controller(parsed)
                        self.signal_received.emit(str(parsed))
                    except Exception as e:
                        print(f"Ошибка при разборе сообщения: {e}")
                        self.handle_serial_controller({"error": str(e)})
            except Exception as e:
                print(f"Ошибка чтения: {e}")

    def handle_serial_controller(self, parsed_response: dict):
        """
        Обрабатывает разобранное сообщение. Здесь можно расширять логику обработки.
        """
        print("Обработанное сообщение:", parsed_response)

    def run(self):
        self.open_port()
        while self.running:
            if not self.command_queue.empty():
                command = self.command_queue.get()
                # Ожидаем команды в формате "send:<command_code>:<payload>"
                if command.startswith("send:"):
                    try:
                        _, code_str, payload_str = command.split(":", 2)
                        command_code = int(code_str)
                        payload = payload_str.encode()  # преобразуем строку в байты
                        self.send_message(command_code, payload)
                    except Exception as e:
                        print(f"Ошибка отправки команды: {e}")
            self.read_data()
            time.sleep(0.1)
        self.close_port()

    def stop(self):
        self.running = False
