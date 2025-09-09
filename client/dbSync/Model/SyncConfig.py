# dbSync/Model/SyncConfig.py

from sqlalchemy import Column, String, Boolean

from dbSync.Model.base import sync_base


# 5. (Опционально) Модель SyncConfig — включение/отключение синхронизации для таблиц
class SyncConfig(sync_base):
    __tablename__ = "SyncConfig"

    table_name = Column(String, primary_key=True)  # имя таблицы
    enabled = Column(Boolean, nullable=False, default=True)  # синхронизация включена?
