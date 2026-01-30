# dbSync/Logic_v2/utils.py
import logging
import pkgutil
import importlib
from sqlalchemy import MetaData

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from DB.Data.base import Base
from sqlalchemy.engine import create_engine


# --- Шаг 1: силой импортируем все модули из папки DB.Models ---
import DB.Models  # пакет, в котором лежат все ваши модели
from dbSync.Engines.SyncConfigEngine import SyncConfigCRUD

for finder, name, ispkg in pkgutil.iter_modules(DB.Models.__path__):
    importlib.import_module(f"DB.Models.{name}")

def _build_server_schema() -> dict[str, dict[str, str]]:
    """
    Проходит по всему Base.metadata и собирает
    для каждой таблицы словарь столбцов -> строковое название типа.
    """
    schema: dict[str, dict[str, str]] = {}
    for table in Base.metadata.sorted_tables:
        cols: dict[str, str] = {}
        for col in table.columns:
            # Приводим тип к строке. Можно тонко настраивать, если нужен JSON-тип.
            cols[col.name] = col.type.__class__.__name__.lower()
        schema[table.name] = cols
    return schema


def init_sync_config_table(session: Session) -> None:
    """
    Заполняет таблицу SyncConfig всеми валидными таблицами из SERVER_SCHEMA,
    исключая те, в названии которых содержится "_has_". Новые записи создаются
    только если они ещё не существуют.

    :param session: SQLAlchemy Session
    """
    sync_crud = SyncConfigCRUD(session)

    for table_name in SERVER_SCHEMA:
        if "_has_" in table_name:
            continue

        current_status = sync_crud.get_status(table_name)
        if current_status is None:
            # Записи нет — создаём с enabled=True
            success = sync_crud.enable_sync(table_name)
            logger.debug("[init_sync_config_table] Добавлена запись: table_name=%s enabled=True → success=%s", table_name, success)
        else:
            logger.debug("[init_sync_config_table] Пропущена: table_name=%s (уже есть запись)", table_name)

# Сам SERVER_SCHEMA
SERVER_SCHEMA = _build_server_schema()
