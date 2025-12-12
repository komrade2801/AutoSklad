from typing import Any, Dict, Optional, Union
import logging

from Cnf.CRUD import CnfCRUD
from Core.network_manager import NetworkManager


# Реализация функций
class CnfActions:
    def __init__(self):
        self.cnf = CnfCRUD()
        self.network_manager = NetworkManager()
        self.logger = logging.getLogger(__name__)

    def write_cnf_lock_load(self, locked: bool) -> None:
        self.cnf.set_load_lock(locked)

    def read_cnf(self, index) -> Dict[str, Any]:
        # Заменяем устаревший .dict() на .model_dump()
        return self.cnf.config.model_dump()

    def write_cnf_unlock_load(self) -> None:
        self.cnf.set_load_lock(False)

    def write_cnf_unlock_drop(self) -> None:
        self.cnf.set_drop_lock(False)

    def read_cnf_serial(self, index) -> Dict[str, Any]:
        return self.cnf.get_serial()

    def read_cnf_IP(self, index) -> str:
        return self.cnf.get_ip()

    def write_cnf_serial(self, port: str, baudrate: int) -> None:
        self.cnf.set_serial(port, baudrate)

    def write_cnf_IP(self, ip: str) -> None:
        self.cnf.set_ip(ip)
    
    def write_cnf_network(self, *args) -> None:
        """
        Сохраняет все настройки сети: IP устройства, IP сервера, маску, шлюз и DNS.
        Также применяет настройки к системному сетевому интерфейсу на Linux/Raspberry Pi.
        
        :param args: Кортеж (device_ip, server_ip, subnet_mask, gateway, dns)
        """
        if len(args) < 2:
            raise ValueError("write_cnf_network требует минимум 2 аргумента: device_ip и server_ip")
        
        device_ip = args[0]
        server_ip = args[1]
        subnet_mask = args[2] if len(args) > 2 and args[2] else None
        gateway = args[3] if len(args) > 3 and args[3] else None
        dns = args[4] if len(args) > 4 and args[4] else None
        
        # Сохраняем настройки в config.json
        self.cnf.set_ip(device_ip)
        self.cnf.set_server_ip(server_ip)
        if subnet_mask:
            self.cnf.set_subnet_mask(subnet_mask)
        if gateway:
            self.cnf.set_gateway(gateway)
        if dns:
            self.cnf.set_dns(dns)
        
        # Применяем настройки к системному интерфейсу (только на Linux/Raspberry Pi)
        # Не применяем немедленно, т.к. настройки будут применены после перезагрузки
        # через обновленный dhcpcd.conf
        success, error_msg = self.network_manager.apply_network_settings(
            ip=device_ip,
            subnet_mask=subnet_mask,
            gateway=gateway,
            dns=dns,
            apply_immediate=False  # Настройки применятся после перезагрузки
        )
        
        if not success:
            self.logger.warning(f"Не удалось применить сетевые настройки к системе: {error_msg}")
            # Не выбрасываем исключение, т.к. настройки сохранены в config.json
            # и могут быть применены вручную или после перезагрузки

    def read_cnf_lock_load(self, index) -> bool:
        return self.cnf.get_load_lock()

    def read_cnf_lock_drop(self, index) -> bool:
        return self.cnf.get_drop_lock()

    def write_cnf_lock_drop(self, locked: bool) -> None:
        self.cnf.set_drop_lock(locked)

    def write_log_critical_err(self, error: str) -> None:
        self.cnf.add_critical_error(error)

    def read_cnf_signature(self, index):
        return self.cnf.read_signature()

    def write_cnf_signature(self, serial_number: int, length: int, columns: int, rows: int) -> None:
        """
        Обновляет параметры секции 'signature' в конфигурации:
         - serial_number: новый серийный номер,
         - cells: новые параметры ячеек (длина, количество столбцов и строк).

        :param serial_number: Новый серийный номер.
        :param length: Новое значение длины ячеек.
        :param columns: Новое количество столбцов.
        :param rows: Новое количество строк.
        """
        self.cnf.config.signature.serial_number = serial_number
        self.cnf.config.signature.cells.length = length
        self.cnf.config.signature.cells.columns = columns
        self.cnf.config.signature.cells.rows = rows
        self.cnf._save_config()

    def read_cnf_barcode(self, index) -> Dict[str, Any]:
        """
        Возвращает параметры конфигурации для сканера штрих-кодов.

        :param index: Параметр для совместимости с интерфейсом (не используется).
        :return: Словарь с настройками сканера штрих-кодов.
        """
        return self.cnf.config.barcode.model_dump()

    def write_cnf_barcode(self, port: str, baudrate: int) -> None:
        """
        Обновляет параметры конфигурации для сканера штрих-кодов.

        :param port: Порт сканера.
        :param baudrate: Скорость передачи данных сканера.
        """
        self.cnf.config.barcode.port = port
        self.cnf.config.barcode.baudrate = baudrate
        self.cnf._save_config()

    def clear_cnf_critical_errors(self) -> None:
        """
        Очищает список критических ошибок в конфигурации.
        """
        self.cnf.config.logs.critical_errors.clear()
        self.cnf._save_config()

    def reload_cnf(self) -> None:
        """
        Принудительно перезагружает конфигурацию из файла.
        """
        self.cnf._load_config()