import traceback

import serial

# Настройка COM-порта
ser = serial.Serial(
    port='COM3',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)

while True:
    try:
        # Чтение данных из порта
        data = ser.read(ser.in_waiting)

        # Проверка, есть ли данные
        if data:
            # Декодирование байтов в строку
            message = data.decode('utf-8')
            print(f"Received message: {message}")
    except serial.SerialException as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        break

# Закрытие порта
ser.close()