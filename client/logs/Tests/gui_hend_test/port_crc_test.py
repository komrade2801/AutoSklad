import serial
import time
from datetime import datetime

class SerialPort:
    def __init__(self, port, baudrate=9600, timeout=1):
        """
        Инициализация COM-порта.

        :param port: Имя порта (например, 'COM3').
        :param baudrate: Скорость передачи данных (по умолчанию 9600).
        :param timeout: Тайм-аут для чтения в секундах (по умолчанию 1 секунда).
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None

    def open(self):
        """Открытие COM-порта."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            print(f"Порт {self.port} открыт.")
        except serial.SerialException as e:
            print(f"Ошибка при открытии порта {self.port}: {e}")

    def close(self):
        """Закрытие COM-порта."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print(f"Порт {self.port} закрыт.")

    def send_data(self, data):
        """
        Отправка данных через COM-порт.

        :param data: Строка или байты для отправки.
        """
        if self.serial and self.serial.is_open:
            try:
                if isinstance(data, str):
                    data = data.encode()  # Преобразование строки в байты
                self.serial.write(data)
                print(f"Отправлено: {data}")
            except Exception as e:
                print(f"Ошибка при отправке данных: {e}")

    def read_data(self):
        """
        Чтение данных из COM-порта.

        :return: Прочитанные данные в виде байтов.
        """
        if self.serial and self.serial.is_open:
            try:
                data = self.serial.readline().strip()  # Чтение байтов
                return data
            except Exception as e:
                print(f"Ошибка при чтении данных: {e}")
        return None

def handle_serial_controller(parsed_response):
    """Пример обработчика разобранного сообщения."""
    print("Обработанное сообщение:", parsed_response)

def handle_controller_serial_response(response: bytes):
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
        if len(response) < 5:
            raise ValueError("Сообщение слишком короткое для обработки")

        # Извлечение полей: [STX][CMD][LEN][DATA][CRC][ETX]
        cmd = response[1]
        length = response[2]
        expected_length = length + 5  # 1 (STX) + 1 (CMD) + 1 (LEN) + length (DATA) + 1 (CRC) + 1 (ETX) = length + 5
        if len(response) != expected_length:
            raise ValueError("Длина сообщения не соответствует указанной длине данных")
        data = response[3:3 + length]
        crc_received = response[3 + length]

        # Вычисляем CRC как сумму байтов от CMD до конца DATA по модулю 256
        crc_calculated = sum(response[1:3 + length]) & 0xFF
        if crc_calculated != crc_received:
            raise ValueError("Контрольная сумма (CRC) не совпадает")

        # Преобразуем код команды в строковое представление
        command_mapping = {0x01: "command_is_send", 0x02: "command_ok"}
        command_str = command_mapping.get(cmd, f"unknown_command_{cmd}")

        parsed_response = {"command": command_str, "data": data}
        handle_serial_controller(parsed_response)

        if parsed_response.get("command") == "command_ok":
            print("`command_ok` - процесс завершён")
        elif parsed_response.get("command") == "command_is_send":
            print("`command_is_send` - переключаем на экран ожидания")
    except Exception as e:
        print(f"Ошибка при обработке ответа: {e}")
        handle_serial_controller({"error": str(e)})

if __name__ == "__main__":
    port_name = "COM30"
    serial_port = SerialPort(port=port_name, baudrate=9600, timeout=1)

    try:
        serial_port.open()
        while True:
            # Читаем данные с COM-порта (ожидаем байтовое сообщение)
            received = serial_port.read_data()
            if received is not None and received != b'':
                print(f"Получено: {received}")
                # Здесь имитируем обработку ответа через функцию handle_controller_serial_response
                # Отправляем ответ command_is_send: формат [STX][CMD=0x01][LEN=0][CRC=0x01][ETX]
                msg_is_send = b'\x02\x01\x00\x01\x03'
                handle_controller_serial_response(msg_is_send)
                time.sleep(10)
                # Отправляем ответ command_ok: формат [STX][CMD=0x02][LEN=0][CRC=0x02][ETX]
                msg_ok = b'\x02\x02\x00\x02\x03'
                handle_controller_serial_response(msg_ok)
                # Если получено сообщение "exit", завершаем работу
                if received.strip() == b"exit":
                    print("Завершение работы.")
                    break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Программа завершена пользователем.")
    finally:
        serial_port.close()
