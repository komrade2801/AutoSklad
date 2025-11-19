# dbSync/sync_db.py

import os
import threading
from datetime import datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from dbSync.Model.Command import Command
from dbSync.Model.CommandStatus import CommandStatus
from dbSync.Model.Record import Record
from dbSync.Model.SyncConfig import SyncConfig
from dbSync.Model.base import sync_base

# --- Конфигурация ---
SYNC_DB_FILENAME = "sync.db"


def _resolve_sync_db_path() -> str:
    """
    Возвращает абсолютный путь к файлу sync.db в папке dbSync/Model.
    """
    dbsync_dir = os.path.dirname(__file__)  # .../dbSync
    model_dir = os.path.join(dbsync_dir, "Model")  # .../dbSync/Model
    os.makedirs(model_dir, exist_ok=True)
    # .../dbSync/Model/sync.db
    out_name = os.path.join(model_dir, SYNC_DB_FILENAME)
    print(f"[ПОТОК][{threading.current_thread().name}][sync_db.py][_resolve_sync_db_path] расположение синхронизационной базы: {out_name} [{datetime.now()}]")
    return out_name


# --- Инициализация базы (удаление + создание таблиц) ---
def init_sync_db(force_recreate: bool = False) -> None:
    """
    Гарантированно создаёт чистый файл sync.db и структуру таблиц.
    :param force_recreate: если True, удаляет старый файл перед созданием.
    """
    db_file = _resolve_sync_db_path()
    if force_recreate and os.path.exists(db_file):
        os.remove(db_file)

    # Просто «touch» файла для SQLAlchemy URI
    if not os.path.exists(db_file):
        open(db_file, "w").close()

    models = [CommandStatus, Command, Record, SyncConfig]
    engine = _get_sync_engine()
    sync_base.metadata.create_all(engine)


# --- Движок и сессии ---
_sync_engine = None
_SessionLocal = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        db_file = _resolve_sync_db_path()
        url = f"sqlite:///{db_file}"
        e = create_engine(
            url,
            poolclass=NullPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        # Включаем WAL
        with e.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
        _sync_engine = e
    return _sync_engine


def get_sync_session():
    """
    Factory для SQLAlchemy Session, привязанной к sync.db.
    При первом вызове создаёт сессию через sessionmaker и запоминает.
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = _get_sync_engine()
        _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return _SessionLocal()


# --- точка входа для кода Runner.py и для скриптов миграции ---
if __name__ == "__main__":
    # Если запускаем напрямую — пересоздаём базу «с нуля»
    init_sync_db(force_recreate=True)
    print("Sync DB initialized at", _resolve_sync_db_path())
