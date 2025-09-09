import serial
from cryptography.fernet import Fernet
import hmac
import hashlib
import logging


class EncryptedSerialHandler:
    """
    Класс для безопасной передачи данных через COM-порт.
    Реализует симметричное шифрование (AES-128) и проверку целостности через HMAC.
    :cite[2]:cite[10]
    """

    def __init__(self, port, baudrate=9600, timeout=1, encryption_key=None, hmac_key=None):
        """
        :param encryption_key: Ключ для шифрования (32 байта в url-safe base64)
        :param hmac_key: Ключ для HMAC (рекомендуется 32+ байта)
        """
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )

        # Генерация ключей при их отсутствии
        self.fernet = Fernet(encryption_key or Fernet.generate_key())
        self.hmac_key = hmac_key or Fernet.generate_key()

        logging.basicConfig(level=logging.INFO)

    def _pack_data(self, raw_data: bytes) -> bytes:
        """Упаковка данных с HMAC."""
        signature = hmac.new(
            self.hmac_key,
            raw_data,
            hashlib.sha256
        ).digest()
        return raw_data + signature

    def _unpack_data(self, packed_data: bytes) -> bytes:
        """Распаковка и проверка HMAC."""
        if len(packed_data) < 32:
            raise ValueError("Invalid message length")

        received_signature = packed_data[-32:]
        raw_data = packed_data[:-32]

        expected_signature = hmac.new(
            self.hmac_key,
            raw_data,
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(received_signature, expected_signature):
            raise SecurityError("HMAC verification failed")

        return raw_data

    def send_encrypted(self, command_code: int, data: bytes = b'') -> None:
        """
        Шифрует данные, добавляет HMAC и отправляет через COM-порт.
        Сохраняет структуру оригинального протокола [STX][CMD][LEN][DATA][CRC][ETX]
        :cite[1]:cite[9]
        """
        try:
            # Шифрование полезной нагрузки
            encrypted_data = self.fernet.encrypt(data)

            # Формирование пакета по оригинальному протоколу
            stx = b'\x02'
            etx = b'\x03'
            cmd = command_code.to_bytes(1, 'big')
            length = len(encrypted_data).to_bytes(1, 'big')

            # Вычисление CRC для зашифрованных данных
            crc = (sum(cmd) + sum(length) + sum(encrypted_data)) & 0xFF
            crc_byte = crc.to_bytes(1, 'big')

            # Сборка пакета
            payload = cmd + length + encrypted_data + crc_byte
            packed_payload = self._pack_data(payload)
            full_message = stx + packed_payload + etx

            self.serial.write(full_message)
            logging.info(f"Sent encrypted message: {full_message.hex()}")

        except Exception as e:
            logging.error(f"Encryption error: {e}")
            raise

    def receive_encrypted(self) -> dict:
        """
        Принимает и расшифровывает данные, проверяя целостность.
        Возвращает словарь с разобранным сообщением.
        """
        try:
            # Чтение данных с учетом структуры протокола
            raw = self.serial.read_until(b'\x03')
            if not raw.startswith(b'\x02') or not raw.endswith(b'\x03'):
                raise ValueError("Invalid frame format")

            # Извлечение и проверка полезной нагрузки
            packed_payload = raw[1:-1]
            unpacked = self._unpack_data(packed_payload)

            # Парсинг полей
            cmd = unpacked[0]
            length = unpacked[1]
            encrypted_data = unpacked[2:2 + length]
            crc_received = unpacked[2 + length]

            # Проверка CRC
            crc_calculated = (sum(unpacked[:2 + length])) & 0xFF
            if crc_calculated != crc_received:
                raise ValueError("CRC mismatch")

            # Дешифровка данных
            decrypted_data = self.fernet.decrypt(encrypted_data)

            return {
                'command': cmd,
                'data': decrypted_data,
                'crc_valid': True
            }

        except Exception as e:
            logging.error(f"Decryption error: {e}")
            return {'error': str(e)}


class SecurityError(Exception):
    """Кастомное исключение для ошибок безопасности"""
    pass