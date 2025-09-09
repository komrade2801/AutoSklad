import time
from cryptography.fernet import Fernet

from BarcodeScanner.SecureSerialManager import SecureSerialManager

# Генерируем или используем заранее сохранённый ключ (должен быть одинаковым на обоих устройствах)
encryption_key = Fernet.generate_key()

# Создаём объект для работы с COM-портом
serial_manager_a = SecureSerialManager(port="COM30", baudrate=9600, key=encryption_key)
serial_manager_b = SecureSerialManager(port="COM29", baudrate=9600, key=encryption_key)

# Запускаем в отдельном потоке
serial_manager_a.start()
serial_manager_b.start()

# Отправляем команду 0x01 с полезной нагрузкой "Hello, Device!"
serial_manager_a.command_queue.put("send:1:Hello, device!")
serial_manager_b.command_queue.put("send:2:Hello, word!")

# Ждём некоторое время, чтобы дать системе возможность обработать ответ
time.sleep(5)

# Останавливаем поток и закрываем порт
serial_manager_a.stop()
serial_manager_a.join()

serial_manager_b.stop()
serial_manager_b.join()