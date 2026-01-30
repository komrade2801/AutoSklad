from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Core.app_logging import get_logger
from options import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

logger = get_logger(__name__)


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
