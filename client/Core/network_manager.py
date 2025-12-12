"""
Модуль для применения сетевых настроек к системному сетевому интерфейсу Linux.
Поддерживает применение настроек через dhcpcd на Raspberry Pi и других Linux системах.
"""
import subprocess
import logging
import re
from pathlib import Path
from typing import Optional, Tuple
from ipaddress import IPv4Address, IPv4Network

from Core.platforms import detect


class NetworkManager:
    """
    Класс для управления сетевыми настройками системы Linux.
    Применяет настройки IP, маски подсети, шлюза и DNS к системному интерфейсу.
    """
    
    def __init__(self):
        self.platform = detect()
        self.dhcpcd_conf_path = Path("/etc/dhcpcd.conf")
        self.logger = logging.getLogger(__name__)
        
    def _is_linux_platform(self) -> bool:
        """Проверяет, является ли платформа Linux или Raspberry Pi"""
        return self.platform in ('Linux', 'Raspberry Pi')
    
    def _mask_to_cidr(self, mask: str) -> int:
        """
        Конвертирует маску подсети в CIDR нотацию.
        
        :param mask: Маска подсети в формате "255.255.255.0"
        :return: CIDR префикс (например, 24 для 255.255.255.0)
        """
        try:
            # Конвертируем маску в IPv4Address
            mask_addr = IPv4Address(mask)
            # Подсчитываем количество единичных битов в 32-битном числе
            mask_int = int(mask_addr)
            # Используем bit_length() для правильного подсчета битов
            # или просто считаем единичные биты
            cidr = 0
            for i in range(32):
                if mask_int & (1 << (31 - i)):
                    cidr += 1
                else:
                    break
            return cidr
        except Exception as e:
            self.logger.error(f"Ошибка конвертации маски {mask} в CIDR: {e}")
            return 24  # Значение по умолчанию
    
    def _get_network_interface(self) -> Optional[str]:
        """
        Определяет активный сетевой интерфейс (eth0, wlan0 и т.д.)
        
        :return: Имя интерфейса или None
        """
        try:
            # Пытаемся найти интерфейс через ip команду
            result = subprocess.run(
                ['ip', 'route', 'get', '8.8.8.8'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Ищем имя интерфейса в выводе
                match = re.search(r'dev\s+(\w+)', result.stdout)
                if match:
                    return match.group(1)
        except Exception as e:
            self.logger.warning(f"Не удалось определить интерфейс через ip: {e}")
        
        # Пробуем стандартные интерфейсы
        for interface in ['eth0', 'wlan0', 'enp0s3', 'enp0s8']:
            try:
                result = subprocess.run(
                    ['ip', 'link', 'show', interface],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return interface
            except Exception:
                continue
        
        self.logger.warning("Не удалось определить сетевой интерфейс")
        return None
    
    def _update_dhcpcd_conf(
        self,
        interface: str,
        ip: str,
        subnet_mask: Optional[str],
        gateway: Optional[str],
        dns: Optional[str]
    ) -> bool:
        """
        Обновляет конфигурационный файл /etc/dhcpcd.conf для применения статических сетевых настроек.
        
        :param interface: Имя сетевого интерфейса (например, eth0)
        :param ip: IP адрес устройства
        :param subnet_mask: Маска подсети
        :param gateway: Адрес шлюза
        :param dns: Адрес DNS сервера
        :return: True если успешно, False в противном случае
        """
        try:
            # Проверяем права доступа
            if not self.dhcpcd_conf_path.exists():
                self.logger.error(f"Файл {self.dhcpcd_conf_path} не существует")
                return False
            
            # Читаем текущий конфигурационный файл
            current_content = self.dhcpcd_conf_path.read_text(encoding='utf-8')
            
            # Формируем новую секцию конфигурации для интерфейса
            cidr = self._mask_to_cidr(subnet_mask) if subnet_mask else 24
            ip_with_cidr = f"{ip}/{cidr}"
            
            # Удаляем старую конфигурацию для этого интерфейса
            lines = current_content.split('\n')
            new_lines = []
            skip_interface_section = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Находим начало секции интерфейса
                if stripped.startswith(f"interface {interface}"):
                    skip_interface_section = True
                    continue
                
                # Пропускаем строки внутри секции интерфейса
                if skip_interface_section:
                    # Если строка пустая или начинается с новой секции (не static и не пробел/таб), прекращаем пропуск
                    if not stripped:
                        skip_interface_section = False
                        new_lines.append(line)  # Сохраняем пустую строку
                    elif stripped.startswith('static'):
                        # Пропускаем строки static
                        continue
                    elif not line.startswith((' ', '\t')) and stripped:
                        # Новая секция (не отступ), прекращаем пропуск
                        skip_interface_section = False
                        new_lines.append(line)
                    else:
                        # Пропускаем строки с отступом (комментарии и т.д.)
                        continue
                else:
                    new_lines.append(line)
            
            # Добавляем новую конфигурацию для интерфейса
            new_lines.append(f"\n# Автоматически сгенерировано приложением")
            new_lines.append(f"interface {interface}")
            new_lines.append(f"static ip_address={ip_with_cidr}")
            
            if gateway:
                new_lines.append(f"static routers={gateway}")
            
            if dns:
                new_lines.append(f"static domain_name_servers={dns}")
            
            new_lines.append("")  # Пустая строка в конце
            
            # Записываем обновленный конфигурационный файл
            new_content = '\n'.join(new_lines)
            self.dhcpcd_conf_path.write_text(new_content, encoding='utf-8')
            
            self.logger.info(f"Конфигурация dhcpcd обновлена для интерфейса {interface}")
            return True
            
        except PermissionError:
            self.logger.error(f"Недостаточно прав для записи в {self.dhcpcd_conf_path}. "
                            f"Приложение должно запускаться с правами sudo.")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка обновления dhcpcd.conf: {e}")
            return False
    
    def _apply_network_settings_immediate(
        self,
        interface: str,
        ip: str,
        subnet_mask: Optional[str],
        gateway: Optional[str]
    ) -> bool:
        """
        Применяет сетевые настройки немедленно через команды ip/ifconfig.
        Это временное применение до перезагрузки системы.
        
        :param interface: Имя сетевого интерфейса
        :param ip: IP адрес
        :param subnet_mask: Маска подсети
        :param gateway: Адрес шлюза
        :return: True если успешно
        """
        try:
            cidr = self._mask_to_cidr(subnet_mask) if subnet_mask else 24
            ip_with_cidr = f"{ip}/{cidr}"
            
            # Удаляем текущий IP адрес (если есть)
            subprocess.run(
                ['ip', 'addr', 'flush', 'dev', interface],
                check=False,
                timeout=5
            )
            
            # Устанавливаем новый IP адрес
            subprocess.run(
                ['ip', 'addr', 'add', ip_with_cidr, 'dev', interface],
                check=True,
                timeout=5
            )
            
            # Включаем интерфейс
            subprocess.run(
                ['ip', 'link', 'set', interface, 'up'],
                check=True,
                timeout=5
            )
            
            # Устанавливаем маршрут по умолчанию через шлюз
            if gateway:
                # Удаляем старый маршрут по умолчанию
                subprocess.run(
                    ['ip', 'route', 'del', 'default'],
                    check=False,
                    timeout=5
                )
                # Добавляем новый маршрут
                subprocess.run(
                    ['ip', 'route', 'add', 'default', 'via', gateway],
                    check=True,
                    timeout=5
                )
            
            self.logger.info(f"Сетевые настройки применены к интерфейсу {interface}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка применения сетевых настроек: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при применении настроек: {e}")
            return False
    
    def apply_network_settings(
        self,
        ip: str,
        subnet_mask: Optional[str] = None,
        gateway: Optional[str] = None,
        dns: Optional[str] = None,
        apply_immediate: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Применяет сетевые настройки к системному интерфейсу.
        
        :param ip: IP адрес устройства
        :param subnet_mask: Маска подсети (опционально)
        :param gateway: Адрес шлюза (опционально)
        :param dns: Адрес DNS сервера (опционально)
        :param apply_immediate: Если True, применяет настройки немедленно (до перезагрузки)
        :return: Кортеж (успех, сообщение об ошибке)
        """
        if not self._is_linux_platform():
            self.logger.info(f"Применение сетевых настроек не поддерживается на {self.platform}")
            return (True, None)  # Не ошибка, просто не применимо
        
        # Определяем сетевой интерфейс
        interface = self._get_network_interface()
        if not interface:
            error_msg = "Не удалось определить сетевой интерфейс"
            self.logger.error(error_msg)
            return (False, error_msg)
        
        self.logger.info(f"Применение сетевых настроек к интерфейсу {interface}")
        
        # Обновляем конфигурационный файл dhcpcd.conf
        if not self._update_dhcpcd_conf(interface, ip, subnet_mask, gateway, dns):
            error_msg = "Не удалось обновить конфигурацию dhcpcd"
            return (False, error_msg)
        
        # Если требуется немедленное применение (опционально)
        if apply_immediate:
            if not self._apply_network_settings_immediate(interface, ip, subnet_mask, gateway):
                self.logger.warning("Не удалось применить настройки немедленно, "
                                  "но конфигурация сохранена для применения после перезагрузки")
        
        # Перезапускаем dhcpcd для применения настроек (если не применяли немедленно)
        if not apply_immediate:
            try:
                subprocess.run(
                    ['systemctl', 'restart', 'dhcpcd'],
                    check=True,
                    timeout=10
                )
                self.logger.info("Служба dhcpcd перезапущена")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Не удалось перезапустить dhcpcd: {e}. "
                                  f"Настройки будут применены после перезагрузки")
            except FileNotFoundError:
                self.logger.warning("systemctl не найден. Настройки будут применены после перезагрузки")
        
        return (True, None)

