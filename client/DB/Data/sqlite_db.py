import os
from sqlalchemy import event, NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from config import db_path


def check_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем текущую директорию
    __db_path = os.path.join(current_dir, db_path)  # Формируем относительный путь

    return __db_path


def engine(db_path=check_file()):
    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        poolclass=NullPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 30
        },
    )

    @event.listens_for(_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()

    return _engine


def SessionLocal(_engine=engine(db_path=check_file())):
    import time
    time.sleep(0.1)  # 100 мс
    _SessionLocal = sessionmaker(
        bind=_engine,
        expire_on_commit=False
    )
    return _SessionLocal()
