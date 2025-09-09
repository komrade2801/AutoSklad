# DB/Data/sqlite_db.py
import os
from sqlalchemy import event, NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from options import db_path


def _get_db_file_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, db_path)


_engine = None


def get_engine():
    """
    Возвращает одиночный движок, создаёт его при первом вызове.
    """
    global _engine
    if _engine is None:
        db_file = _get_db_file_path()
        _engine = create_engine(
            f"sqlite:///{db_file}",
            echo=False,
            poolclass=NullPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            },
        )

        # Включаем WAL‑режим и NORMAL synchronous при каждом новом соединении
        @event.listens_for(_engine, "connect")
        def _enable_wal(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()
    return _engine


def SessionLocal():
    # _engine=engine(_db_path=check_file())
    _engine = get_engine()
    import time
    time.sleep(0.1)  # 100 мс
    _SessionLocal = sessionmaker(
        bind=_engine,
        expire_on_commit=False
    )
    return _SessionLocal()
