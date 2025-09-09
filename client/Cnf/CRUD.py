from datetime import datetime
from typing import Any, Dict, Optional, Union
from threading import RLock
from pathlib import Path
import json
import logging
from pydantic import ValidationError

from Cnf.Models import AppConfig


class CnfCRUD:
    """
    Синглтон для работы с файлом конфигурации config.json посредством моделей Pydantic.

    Реализует:
      - Загрузку и сохранение конфигурации с использованием блокировки (RLock) для потокобезопасности.
      - Методы доступа и модификации настроек для сети, последовательного порта, блокировок и логов.
      - Метод read_signature, возвращающий данные секции 'signature' (с номером серии и настройками ячеек).
    """
    _instance = None
    _lock = RLock()

    def __new__(cls, config_path: Union[str, Path] = "config.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(config_path)
        return cls._instance

    def _init(self, config_path: Union[str, Path]):
        self.config_path = Path(config_path)
        self._config: Optional[AppConfig] = None
        self.file_lock = RLock()

    def _load_config(self) -> None:
        """
        Загружает конфигурацию из файла config.json.
        Если файл отсутствует, создается новая конфигурация по умолчанию и сохраняется.
        При ошибках парсинга или валидации выбрасывается RuntimeError.
        """
        try:
            with self.file_lock:
                if self.config_path.exists():
                    raw_data = json.loads(self.config_path.read_text())
                    self._config = AppConfig.model_validate(raw_data)
                else:
                    self._config = AppConfig()
                    self._save_config()
        except (json.JSONDecodeError, ValidationError) as e:
            logging.critical(f"Config load error: {str(e)}")
            raise RuntimeError("Invalid configuration file") from e

    def _save_config(self) -> None:
        """
        Сохраняет текущую конфигурацию в файл config.json с форматированием.
        Используется метод model_dump_json() для сериализации модели.
        """
        with self.file_lock:
            self.config_path.write_text(
                self._config.model_dump_json(indent=2, exclude_none=True)
            )

    @property
    def config(self) -> AppConfig:
        """
        Возвращает текущую конфигурацию.
        Если конфигурация еще не загружена, происходит её загрузка из файла.
        """
        if self._config is None:
            self._load_config()
        return self._config

    # Методы работы с настройками сети
    def get_ip(self) -> str:
        """
        Возвращает IP-адрес из секции network.
        """
        return str(self.config.network.ip)

    def set_ip(self, ip: str) -> None:
        """
        Устанавливает новый IP-адрес в секции network и сохраняет конфигурацию.
        """
        self.config.network.ip = ip
        self._save_config()

    # Методы работы с последовательным портом
    def get_serial(self) -> Dict[str, Any]:
        """
        Возвращает настройки последовательного порта в виде словаря.
        """
        return self.config.serial.model_dump()

    def set_serial(self, port: str, baudrate: int) -> None:
        """
        Устанавливает порт и скорость (baudrate) для последовательного подключения и сохраняет конфигурацию.
        """
        self.config.serial.port = port
        self.config.serial.baudrate = baudrate
        self._save_config()

    # Методы работы с блокировками
    def get_load_lock(self) -> bool:
        """
        Возвращает состояние блокировки загрузки.
        """
        return self.config.locks.load_locked

    def set_load_lock(self, locked: bool) -> None:
        """
        Устанавливает состояние блокировки загрузки и сохраняет конфигурацию.
        """
        self.config.locks.load_locked = locked
        self._save_config()

    def get_drop_lock(self) -> bool:
        """
        Возвращает состояние блокировки выгрузки.
        """
        return self.config.locks.drop_locked

    def set_drop_lock(self, locked: bool) -> None:
        """
        Устанавливает состояние блокировки выгрузки и сохраняет конфигурацию.
        """
        self.config.locks.drop_locked = locked
        self._save_config()

    # Методы работы с логами
    def add_critical_error(self, error: str) -> None:
        """
        Добавляет новую критическую ошибку с временной меткой в секцию логов и сохраняет конфигурацию.
        """
        self.config.logs.critical_errors.append({
            "timestamp": datetime.now().isoformat(),
            "message": error
        })
        self._save_config()

    def read_signature(self):
        """
        Возвращает данные секции 'signature' из конфигурации.
        """
        return self.config.signature
