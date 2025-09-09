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
                print(f"Отправлено: {data.hex()}")
            except Exception as e:
                print(f"Ошибка при отправке данных: {e}")

    def raw_send_data(self, data):
        """
        Отправка данных через COM-порт с учетом нового формата:
        сообщение начинается с '$' и заканчивается '\n'.
        """
        """
        Отправка данных в формате: $<данные>\n
        """
        if self.serial and self.serial.is_open:
            try:
                # Преобразуем данные в строку
                data_str = str(data)

                # Формируем сообщение в виде байтов: $<данные>\n
                message = b'$' + data_str.encode('utf-8') + b'\n'

                # Отправляем
                self.serial.write(message)
                print(f"[Отправлено] {message}")  # Для отладки

                # Принудительно очищаем буфер (опционально)
                self.serial.flush()

            except Exception as e:
                print(f"Ошибка отправки: {e}")


    def raw_read_data(self):
        """
        Чтение данных из COM-порта с учетом нового формата:
        ожидается, что сообщение начинается с '$' и заканчивается '\n'.
        Возвращается содержимое между этими символами.
        """
        if self.serial and self.serial.is_open:
            try:
                raw_data = self.serial.readline()
                if raw_data:
                    # hex_raw_data = hex(raw_data)
                    # print(hex_raw_data)
                    # Проверка: сообщение должно начинаться с '$' и заканчиваться '\n'
                    first_s = chr(raw_data[0])
                    end_r = chr(raw_data[-1])
                    first_check = chr(0x24)
                    end_check = '\n'
                    len_raw_data = len(raw_data)
                    if len_raw_data >= 2 and first_s == first_check and end_r == end_check:
                        data = raw_data[1:-1].strip()  # Извлекаем содержимое без '$' и '\n'
                        return data
                    else:
                        print("Получено сообщение с некорректным форматом:", raw_data)
                        return None
            except Exception as e:
                print(f"Ошибка при чтении данных: {e}")
        return None


    def read_data(self):
        """
        Чтение данных из COM-порта.

        :return: Прочитанные данные в виде строки.
        """
        if self.serial and self.serial.is_open:
            try:
                data = self.serial.readline().decode().strip()  # Чтение строки
                return data
            except Exception as e:
                print(f"Ошибка при чтении данных: {e}")
        return None


if __name__ == "__main__":
    # Укажите имя порта, например, 'COM3' для Windows
    port_name = "COM30"

    # Создаем объект SerialPort
    serial_port = SerialPort(port=port_name, baudrate=9600)

    try:
        serial_port.open()  # Открываем порт

        while True:
            # Пример чтения данных
            received = serial_port.raw_read_data()
            if received and received!='':
                print(f"Получено: { received}")
                # Подтверждение приёма команды
                serial_port.raw_send_data('1')
                time.sleep(10)
                # Подтверждение исполнения команды
                serial_port.raw_send_data('2')
                # Условие выхода
                if received == "exit":
                    print("Завершение работы.")
                    break

            time.sleep(1)  # Задержка перед следующей итерацией

    except KeyboardInterrupt:
        print("Программа завершена пользователем.")

    finally:
        serial_port.close()  # Закрываем порт
