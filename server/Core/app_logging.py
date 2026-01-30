"""
Централизованная настройка логирования для серверного приложения AutoSklad.

Обеспечивает:
- Логирование в файлы с ротацией
- Разделение логов по категориям (app, sync, error)
- Вывод в консоль
- Настройку уровней логирования
"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_app_logging(
    log_dir: str = "logs",
    app_log_file: str = "app.log",
    sync_log_file: str = "sync.log",
    error_log_file: str = "error.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True
) -> None:
    """
    Настраивает централизованное логирование для всего приложения.

    :param log_dir: Директория для логов
    :param app_log_file: Имя файла для общих логов приложения
    :param sync_log_file: Имя файла для логов синхронизации
    :param error_log_file: Имя файла для ошибок
    :param level: Уровень логирования (logging.DEBUG, INFO, WARNING, ERROR)
    :param max_bytes: Максимальный размер файла лога перед ротацией
    :param backup_count: Количество резервных файлов при ротации
    :param console_output: Выводить ли логи в консоль
    """
    # Создаём директорию для логов
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Формат для логов
    detailed_format = '[%(asctime)s][%(threadName)s][%(name)s][%(levelname)s] %(message)s'
    simple_format = '[%(asctime)s][%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Очищаем существующие handlers корневого логгера
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    # 1. Handler для общих логов приложения (INFO и выше)
    app_log_path = log_path / app_log_file
    app_handler = logging.handlers.RotatingFileHandler(
        str(app_log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(detailed_format, date_format))
    app_handler.addFilter(lambda record: record.levelno >= logging.INFO)
    root_logger.addHandler(app_handler)

    # 2. Handler для логов синхронизации (отдельный файл)
    sync_log_path = log_path / sync_log_file
    sync_handler = logging.handlers.RotatingFileHandler(
        str(sync_log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    sync_handler.setLevel(logging.DEBUG)
    sync_handler.setFormatter(logging.Formatter(detailed_format, date_format))
    # Фильтр: только логи от компонентов синхронизации
    sync_handler.addFilter(lambda record: 'dbSync' in record.name or 'Sync' in record.name)
    root_logger.addHandler(sync_handler)

    # 3. Handler для ошибок (ERROR и CRITICAL)
    error_log_path = log_path / error_log_file
    error_handler = logging.handlers.RotatingFileHandler(
        str(error_log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(detailed_format, date_format))
    error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    root_logger.addHandler(error_handler)

    # 4. Handler для консоли (если включен)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(simple_format, date_format))
        root_logger.addHandler(console_handler)

    # Настраиваем уровни для конкретных модулей
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Логируем начало работы
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Логирование приложения инициализировано")
    logger.info(f"Директория логов: {log_path.absolute()}")
    logger.info(f"Уровень логирования: {logging.getLevelName(level)}")
    logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с указанным именем.

    :param name: Имя логгера (обычно __name__)
    :return: Экземпляр Logger
    """
    return logging.getLogger(name)
