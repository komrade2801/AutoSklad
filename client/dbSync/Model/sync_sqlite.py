# dbSync/Model/sync_sqlite.py
"""
Использует единый модуль sync_db для пути к базе и движка.
"""
from sqlalchemy.orm import sessionmaker

from dbSync.sync_db import _get_sync_engine
from dbSync.Model.base import sync_base

# Получаем движок из общего модуля sync_db
sync_engine = _get_sync_engine()
# Фабрика сессий
SyncSession = sessionmaker(bind=sync_engine)

