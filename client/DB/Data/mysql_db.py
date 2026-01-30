import os

from Core.app_logging import get_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = get_logger(__name__)


# Конфигурация базы данных
DB_HOST = "192.168.0.10"  # Адрес сервера MySQL
DB_PORT = 3306  # Порт MySQL (по умолчанию 3306)
DB_NAME = "vending"  # Имя базы данных
DB_USER = "root"  # Имя пользователя базы данных
DB_PASSWORD = ""  # Пароль пользователя базы данных


def engine():
    """
    Создает движок SQLAlchemy для подключения к базе данных MySQL.
    """
    connection_string = (
        f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    _engine = create_engine(
        connection_string,
        echo=False,  # Уберите True, если не нужно выводить SQL-запросы
        pool_recycle=3600,  # Переподключение к базе каждые 3600 секунд
    )
    return _engine


def SessionLocal(_engine=engine()):
    """
    Создает и возвращает сессию SQLAlchemy.
    """
    _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal()


# Проверка подключения
if __name__ == "__main__":
    try:
        test_engine = engine()
        with test_engine.connect() as connection:
            logger.info("Успешное подключение к базе данных MySQL.")
    except Exception as e:
        logger.exception("Ошибка подключения к базе данных: %s", e)
