import serial
import time


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
            exit(-1)

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
                    data = data.encode() # + ('\r\n').encode() # Преобразование строки в байты
                self.serial.write(data)
                print(f"Отправлено: {data}")
            except Exception as e:
                print(f"Ошибка при отправке данных: {e}")

    def read_data(self):
        """
        Чтение данных из COM-порта.

        :return: Прочитанные данные в виде строки.
        """
        if self.serial and self.serial.is_open:
            try:
                data = self.serial.readline().decode().strip()  # Чтение строки
                print(f"Получено: {data}")
                return data
            except Exception as e:
                print(f"Ошибка при чтении данных: {e}")
        return None


if __name__ == "__main__":
    # Укажите имя порта, например, 'COM3' для Windows
    port_name = "COM29"

    # Создаем объект SerialPort
    serial_port = SerialPort(port=port_name, baudrate=9600)

    try:
        serial_port.open()  # Открываем порт

        while True:
            # Пример отправки данных
            var = input("Введите barcode: ")
            serial_port.send_data(var)

            # Пример чтения данных
            received = serial_port.read_data()

            # Условие выхода
            if received == "exit":
                print("Завершение работы.")
                break

            time.sleep(1)  # Задержка перед следующей итерацией

    except KeyboardInterrupt:
        print("Программа завершена пользователем.")

    finally:
        serial_port.close()  # Закрываем порт
