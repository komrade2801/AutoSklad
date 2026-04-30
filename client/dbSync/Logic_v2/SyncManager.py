# import traceback
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional, Protocol  # , Union

# from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import DateTime
from sqlalchemy.inspection import inspect as sqlalchemy_inspect

from DB.crud_registry import normalize_to_snake


# from DB.crud_registry import crud_registry


# from sqlalchemy import inspect


class CRUDInterface(Protocol):
    """
    Интерфейс CRUD-класса для одной таблицы.
    Реальные реализации должны иметь методы:
      - add(**data) -> Any
      - update(id, **data) -> bool
      - delete(id) -> bool
      - get(id) -> Optional[Union[dict, Any]]
      - list() -> List[Any]
      - filter(**conds) -> List[Any]
      - bulk(commands: List[Dict[str, Any]]) -> List[Any]
    """

    def add(self, **data) -> Any: ...

    def update(self, *, id: Any, **data) -> bool: ...

    def delete(self, *, id: Any) -> bool: ...

    def get(self, *, id: Any) -> Optional[Any]: ...

    def list(self) -> List[Any]: ...

    def filter(self, **conds) -> List[Any]: ...

    def bulk(self, commands: List[Dict[str, Any]]) -> List[Any]: ...

    # def add(self, **data) -> Any: ...
    #
    # def update(self, *, id: Any, **data) -> bool: ...
    #
    # def delete(self, *, id: Any) -> bool: ...
    #
    # def get(self, *, id: Any) -> Optional[Any]: ...
    #
    # def list(self) -> List[Any]: ...
    #
    # def filter(self, **conds) -> List[Any]: ...
    #
    # def bulk(self, commands: List[Dict[str, Any]]) -> List[Any]: ...


class SyncManager:
    """
    Фасад для выполнения CRUD-операций по именам таблиц и
    командам синхронизации в формате:
        {"table": str, "operation": str, "data": dict, "id": Optional[Any]}

    Место в архитектуре:
      • SyncProcessor → SyncManager.process_command() → конкретный CRUD.
      • Отделяет логику синхронизации от деталей доступа к данным.

    Основные методы:
      - process_command(cmd)         — единая точка входа для одной команды.
      - list(table)                  — вернуть все записи таблицы.
      - filter(table, **conds)      — вернуть по условию.
      - bulk_process(commands)       — выполнить батч операций.
      - get_current_data(table, id) — получить текущее состояние записи.

    Зависимости:
      :param crud_registry: реестр таблица→CRUD-класс.
    """

    def __init__(self, session: Session = None) -> None:

        from DB.crud_registry import crud_registry
        self.crud_registry: Dict[str, CRUDInterface] = crud_registry
        self._session = session

    def get_local_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Собирает схему только из таблиц, для которых есть CRUD в реестре.
        Возвращает структуру {table_name: {column_name: type_name}}.
        """
        from DB.Data.base import Base
        schema: Dict[str, Dict[str, str]] = {}
        for tbl in Base.metadata.sorted_tables:
            if self.crud_registry.get(tbl.name) is None:
                continue
            cols: Dict[str, str] = {
                col.name: col.type.__class__.__name__.lower()
                for col in tbl.columns
            }
            schema[tbl.name] = cols
        return schema

    def _serialize_datetimes(self, obj):
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(v) for v in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def process_command(self, command: Dict[str, Any]) -> Any:
        table, op_lower, data, rec_id = self._parse_command(command)

        crud = self._get_crud(table)
        # Парсим даты
        # self._parse_dates(data)
        self._parse_incoming_datetimes(table, data)

        if op_lower == "add":
            return self._handle_insert(crud, table, data, rec_id, sync_context=False)
        elif op_lower == "update":
            return self._handle_update(crud, data, rec_id)
        elif op_lower == "delete":
            return self._handle_delete(crud, rec_id)
        else:
            raise ValueError(f"Операция {op_lower} не поддерживается")

    def process_sync_command(self, command: Dict[str, Any], sync_context: bool = True) -> Any:
        """
        Process command during sync operations with special handling for count fields.

        :param command: Sync command dictionary
        :param sync_context: True if called during sync, False for normal operations
        """
        table, op_lower, data, rec_id = self._parse_command(command)

        crud = self._get_crud(table)
        # Парсим даты
        # self._parse_dates(data)
        self._parse_incoming_datetimes(table, data)

        if op_lower == "add":
            return self._handle_insert(crud, table, data, rec_id, sync_context=sync_context)
        elif op_lower == "update":
            return self._handle_update(crud, data, rec_id)
        elif op_lower == "delete":
            return self._handle_delete(crud, rec_id)
        else:
            raise ValueError(f"Операция {op_lower} не поддерживается")

    def _parse_command(self, command):
        table = command.get("table")
        op = command.get("operation")
        data = command.get("data", {}) or {}
        if "kwargs" in data and isinstance(data["kwargs"], dict):
            data = data["kwargs"]
        rec_id = data.get("id") or data.get("index")

        if not table or not op:
            raise ValueError("Команда должна содержать 'table' и 'operation'")

        return table, op.lower(), data, rec_id

    def _get_crud(self, table):
        crud_cls = self.crud_registry.get(table)
        if crud_cls is None:
            raise ValueError(f"Неизвестная таблица: {table}")
        return crud_cls(self._session)

    def _parse_dates(self, data: Dict[str, Any]):
        for key in ("date", "datetime"):
            val = data.get(key)
            if isinstance(val, str):
                try:
                    data[key] = datetime.fromisoformat(val)
                except ValueError:
                    pass

    def _parse_incoming_datetimes(self, table: str, data: dict):

        mapper = sqlalchemy_inspect(self.crud_registry[table](self._session).model)
        for col in mapper.columns:
            if isinstance(col.type, DateTime) and col.name in data and isinstance(data[col.name], str):
                try:
                    data[col.name] = datetime.fromisoformat(data[col.name])
                except ValueError:
                    pass

    def _serialize(self, record) -> Any:
        if record:
            return self._serialize_datetimes(record.to_dict())
        else:
            raise ValueError("Cannot serialize None or empty record")

    def _handle_insert(self, crud, table, data, rec_id, sync_context=False):
        """
        Handle ADD operations.

        :param crud: CRUD instance for table
        :param table: Table name
        :param data: Data to insert
        :param rec_id: Record ID if provided
        :param sync_context: True if called during sync, False for normal operations
        """
        logger.debug("[COUNT_FIX] _handle_insert called for table %s, rec_id=%s, sync_context=%s", table, rec_id, sync_context)
        logger.debug("[COUNT_FIX] data keys: %s, count value: %s", list(data.keys()), data.get("count"))

        # 1) Спец‑случай с инкрементом - только for non-sync operations (normal tool usage)
        if table in ("Tools", "Consumption") and "count" in data and rec_id is not None and not sync_context:
            existing = crud.get(rec_id)
            if existing:
                logger.debug("[COUNT_FIX] Incrementing count for existing tool %s: %s + %s = %s", rec_id, existing.count, data["count"], existing.count + data["count"])
                return self._increment_count(crud, rec_id, data["count"])

        # For sync operations, bypass count increment logic
        if table in ("Tools", "Consumption") and sync_context:
            logger.debug("[COUNT_FIX] Sync context - setting exact count value instead of incrementing")

        # 2) Если запись уже есть — делать UPSERT‑логику
        if rec_id is not None and crud.get(rec_id):
            return self._upsert_update(crud, rec_id, data, sync_context=sync_context)

        # 3) Чистый INSERT
        # определяем rec_id: сначала из data["id"], потом data["index"], иначе автоинкремент
        rec_id = data.get("id") or data.get("index") or max(crud.get_all_ids(), default=0) + 1
        # отбрасываем оба служебных поля
        fields = {k: v for k, v in data.items() if k not in ("id", "index")}
        # передаём rec_id первым аргументом, остальное — именованно

        if "id" not in data.items() and rec_id:
            fields["id"] = rec_id

        logger.debug("[COUNT_FIX] Inserting new record with final rec_id=%s, fields=%s", rec_id, fields)
        try:
            crud.add(rec_id, sync_context=sync_context, **fields)
        except (RuntimeError, Exception) as e:
            # Если возникла ошибка (например, IntegrityError из-за race condition),
            # проверяем, не появилась ли запись между проверкой и вставкой
            error_str = str(e).lower()
            if "integrity" in error_str or "unique" in error_str or "constraint" in error_str:
                logger.warning("[INTEGRITY_FIX] IntegrityError при вставке %s, проверяем существование записи: %s", rec_id, e)
                existing = crud.get(rec_id)
                if existing:
                    # Запись появилась между проверкой и вставкой (race condition)
                    # Делаем upsert вместо insert
                    logger.debug("[INTEGRITY_FIX] Запись %s найдена после IntegrityError, выполняем upsert", rec_id)
                    return self._upsert_update(crud, rec_id, data, sync_context=sync_context)
            # Если это не IntegrityError или запись не найдена, пробрасываем ошибку дальше
            raise

        # Вместо instance.id — берём rec_id из payload или максимальный ID в таблице
        new_id = data.get("id") or max(crud.get_all_ids(), default=0)
        return self._serialize(crud.get(new_id))

    def _increment_count(self, crud, rec_id, delta):
        existing = crud.get(rec_id)
        new_count = existing.count + delta
        logger.debug("_increment_count rec_id=%s, crud=%s, delta=%s", rec_id, crud, delta)
        crud.update(index=rec_id, sync_context=False, count=new_count)
        return self._serialize(crud.get(rec_id))

    def _upsert_update(self, crud, rec_id, data, sync_context=False):
        """Если запись есть — сравниваем и либо возвращаем, либо обновляем."""
        logger.debug("_upsert_update rec_id=%s, crud=%s, sync_context=%s", rec_id, crud, sync_context)
        existing_obj = crud.get(rec_id)
        if existing_obj is None:
            # Если не нашли запись, логируем и создаём новую
            logger.debug("[DUPLICATION_CHECK] Record %s not found in %s, creating new (sync_context=%s)", rec_id, crud.model.__tablename__, sync_context)
            new_id = crud.add(rec_id, sync_context=sync_context, **{k: v for k, v in data.items() if k not in ("id", "index")})
            new_obj = crud.get(new_id or rec_id)
            return new_obj.to_dict() if new_obj else None

        current = existing_obj.to_dict()
        incoming = {k: data[k] for k in data if k in current}
        
        # Удаляем служебные поля, которые не должны обновляться
        # id, index - идентификаторы
        # created_at, updated_at - временные метки создания/обновления
        excluded_fields = {"id", "index", "created_at", "updated_at"}
        incoming = {k: v for k, v in incoming.items() if k not in excluded_fields}

        # For sync operations, always update without checking for changes
        # For normal operations, check for changes first
        if not sync_context:
            if incoming == {k: current[k] for k in incoming}:
                logger.debug("[DUPLICATION_CHECK] Record %s in %s identical to existing, skipping update", rec_id, crud.model.__tablename__)
                return self._serialize(existing_obj)

        logger.debug("[DUPLICATION_CHECK] Record %s in %s updating (sync_context=%s)", rec_id, crud.model.__tablename__, sync_context)
        crud.update(index=rec_id, sync_context=sync_context, **incoming)
        return self._serialize(crud.get(rec_id))

    def _handle_update(self, crud, data, rec_id):
        """
        Обрабатывает UPDATE операцию.
        
        :param crud: CRUD экземпляр для таблицы
        :param data: Данные для обновления (может содержать id/index)
        :param rec_id: ID записи для обновления
        """
        if rec_id is None:
            raise ValueError("Cannot update record: rec_id is None")
        
        # Проверяем существование записи перед обновлением
        existing_record = crud.get(rec_id)
        if existing_record is None:
            # Если запись не существует, выполняем upsert (insert или update)
            logger.debug("[SyncManager][_handle_update] Record %s not found, performing upsert", rec_id)
            return self._upsert_update(crud, rec_id, data, sync_context=True)
        
        # Удаляем служебные поля, которые не должны обновляться
        # id, index - идентификаторы
        # created_at, updated_at - временные метки создания/обновления
        excluded_fields = {"id", "index", "created_at", "updated_at"}
        update_data = {k: v for k, v in data.items() if k not in excluded_fields}
        
        # Если нет данных для обновления, просто возвращаем существующую запись
        if not update_data:
            logger.debug("[SyncManager][_handle_update] No data to update for record %s, returning existing record", rec_id)
            return self._serialize(existing_record)
        
        # Вызываем update с явным указанием index
        try:
            success = crud.update(index=rec_id, sync_context=True, **update_data)
            if not success:
                # Если обновление не удалось, возможно из-за IntegrityError, пробуем upsert
                logger.debug("[SyncManager][_handle_update] Update returned False for record %s, trying upsert", rec_id)
                return self._upsert_update(crud, rec_id, data, sync_context=True)
        except Exception as e:
            # Если произошла ошибка при обновлении, пробуем upsert
            logger.warning("[SyncManager][_handle_update] Error during update for record %s: %s, trying upsert", rec_id, e)
            return self._upsert_update(crud, rec_id, data, sync_context=True)
        
        updated_record = crud.get(rec_id)
        if updated_record is None:
            raise ValueError(f"Record with id {rec_id} not found after update")
        return self._serialize(updated_record)

    def _handle_delete(self, crud, rec_id):
        existing = crud.get(rec_id)
        if existing:
            crud.delete(index=rec_id, sync_context=True)
            return self._serialize(existing)
        else:
            return {"id": rec_id}

    def get_current_data(self, table: str, rec_id: Any, work_session: Session = None) -> Optional[Dict[str, Any]]:
        """
        Возвращает текущее состояние записи для детекта конфликтов.
        Принудительно обновляет сессию перед чтением, чтобы гарантированно видеть
        изменения, сделанные операцией выдачи инструмента.
        """

        if isinstance(work_session, sessionmaker):
            work_session = work_session

        # crud_cls = self.crud_registry.get(table)
        # if crud_cls is None:
        #     raise ValueError(f"Неизвестная таблица: {table!r}")

        normalized_table = normalize_to_snake(table)
        crud_cls = self.crud_registry.get(normalized_table)
        if crud_cls is None:
            raise ValueError(f"Неизвестная таблица: {table!r}")

        # Принудительное обновление сессии перед чтением
        # Это гарантирует, что мы получим актуальные данные из БД, а не устаревшие из кэша сессии
        try:
            self._session.commit()
            self._session.expire_all()
            logger.debug("[SyncManager][get_current_data] Session expired before getting %s id=%s - fresh data will be loaded from DB", table, rec_id)
        except Exception as e:
            logger.warning("[SyncManager][get_current_data] Failed to expire session before getting %s id=%s: %s", table, rec_id, e)

        # тут мы **вызываем** конструктор EngineX()
        crud = crud_cls(self._session)

        if rec_id is None:
            raise ValueError("record must be have id or index provided and cannot be None or empty.")

        record = crud.get(rec_id)
        if record is None:
            return None

        # Приводим к dict
        if hasattr(record, "to_dict"):
            return record.to_dict()
        elif hasattr(record, "__dict__"):
            return {k: v for k, v in record.__dict__.items() if not k.startswith("_")}
        elif isinstance(record, dict):
            return record
        else:
            return None

    def get_status_stype(self, status_id: Any) -> Optional[str]:
        """
        Возвращает тип статуса (stype) по id для разрешения конфликтов LWW.
        Используется, чтобы при remote_stype in ('mass_load_init', 'mass_load_ready',
        'mass_drop_init', 'mass_drop_ready') входящие данные принимались.
        """
        if status_id is None:
            return None
        try:
            crud_cls = self.crud_registry.get("Status")
            if crud_cls is None:
                return None
            crud = crud_cls(self._session)
            rec = crud.get(status_id)
            return getattr(rec, "stype", None) if rec else None
        except Exception:
            return None

    def list(self, table: str) -> List[Any]:
        """
        Возвращает все записи таблицы.
        """
        crud = self.crud_registry.get(table)
        if crud is None:
            raise ValueError(f"Неизвестная таблица: {table}")
        return crud.list()

    def filter(self, table: str, **conds: Any) -> List[Any]:
        """
        Возвращает записи, удовлетворяющие условиям.
        """
        crud = self.crud_registry.get(table)
        if crud is None:
            raise ValueError(f"Неизвестная таблица: {table}")
        return crud.filter(**conds)

    def bulk_process(self, commands: List[Dict[str, Any]]) -> List[Any]:
        """
        Выполняет сразу несколько команд CRUD в одном вызове.
        Удобно для оптимизации сетевого трафика.
        """
        results = []
        for cmd in commands:
            import dbSync
            dbSync.set_skip_sync_enqueue(True)
            try:
                results.append(self.process_command(cmd))
            finally:
                dbSync.set_skip_sync_enqueue(False)
        return results

# from datetime import datetime
# from typing import Any, Dict, List, Optional, Protocol, Union
#
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.orm import Session, sessionmaker
#
# from sqlalchemy import inspect
#
# import dbSync
#
#
# class CRUDInterface(Protocol):
#     """
#     Интерфейс CRUD-класса для одной таблицы.
#     Реальные реализации должны иметь методы:
#       - add(**data) -> Any
#       - update(id, **data) -> bool
#       - delete(id) -> bool
#       - get(id) -> Optional[Union[dict, Any]]
#       - list() -> List[Any]
#       - filter(**conds) -> List[Any]
#       - bulk(commands: List[Dict[str, Any]]) -> List[Any]
#     """
#
#     def add(self, **data) -> Any: ...
#
#     def update(self, id: Any, **data) -> bool: ...
#
#     def delete(self, id: Any) -> bool: ...
#
#     def get(self, id: Any) -> Optional[Any]: ...
#
#     def list(self) -> List[Any]: ...
#
#     def filter(self, **conds) -> List[Any]: ...
#
#     def bulk(self, commands: List[Dict[str, Any]]) -> List[Any]: ...
#
#
# class SyncManager:
#     """
#     Фасад для выполнения CRUD-операций по именам таблиц и
#     командам синхронизации в формате:
#         {"table": str, "operation": str, "data": dict, "id": Optional[Any]}
#
#     Место в архитектуре:
#       • SyncProcessor → SyncManager.process_command() → конкретный CRUD.
#       • Отделяет логику синхронизации от деталей доступа к данным.
#
#     Основные методы:
#       - process_command(cmd)         — единая точка входа для одной команды.
#       - list(table)                  — вернуть все записи таблицы.
#       - filter(table, **conds)      — вернуть по условию.
#       - bulk_process(commands)       — выполнить батч операций.
#       - get_current_data(table, id) — получить текущее состояние записи.
#
#     Зависимости:
#       :param crud_registry: реестр таблица→CRUD-класс.
#     """
#
#     def __init__(self, session: Session) -> None:
#
#         from DB.crud_registry import crud_registry
#         self.crud_registry: Dict[str, CRUDInterface] = crud_registry
#         self._session = session
#
#     def get_local_schema(self) -> Dict[str, Dict[str, str]]:
#         """
#         Собирает схему из всех таблиц, для которых есть CRUD в реестре.
#         Возвращает структуру {table_name: {column_name: type_name}}.
#         """
#         from DB.Data.base import Base
#         from DB.Data.sqlite_db import engine
#         schema: Dict[str, Dict[str, str]] = {}
#         for tbl in Base.metadata.sorted_tables:
#             cols: Dict[str, str] = {
#                 col.name: col.type.__class__.__name__.lower()
#                 for col in tbl.columns
#             }
#             schema[tbl.name] = cols
#         return schema
#
#     def __extract_rec_id(self, data: dict) -> Any:
#         """
#         Пытается получить идентификатор из data первым из полей
#         'id', 'index', 'number'. Если ни одного нет — вернёт None.
#         """
#         for key in ("id", "index", "number"):
#             if key in data and data[key] is not None:
#                 return data[key]
#         return None
#
#     def process_command(self, command: Dict[str, Any]) -> Any:
#         """
#         Делегирует одну команду синхронизации:
#           insert, update, delete.
#         """
#
#         table = command.get("table")
#         op = command.get("operation")
#         data = command.get("data", {}) or {}
#         rec_id = data.get("id")
#
#         if not table or not op:
#             raise ValueError("Команда должна содержать 'table' и 'operation'")
#
#         # ----- Новая логика: парсинг ISO-строк в datetime -----
#         for key in ("date", "datetime"):
#             val = data.get(key)
#             if isinstance(val, str):
#                 try:
#                     data[key] = datetime.fromisoformat(val)
#                 except ValueError:
#                     pass
#         # ----------------------------------------------------
#
#         crud_cls = self.crud_registry.get(table)
#         if crud_cls is None:
#             raise ValueError(f"Неизвестная таблица: {table}")
#         crud = crud_cls(self._session)
#         op_lower = op.lower()
#
#         if rec_id is None:
#             rec_id = max(crud.get_all_ids(), default=0)
#             # raise ValueError(f"'id' обязателен для {op_lower}")
#
#         # --- INSERT / ADD ---
#         if op_lower in ("insert", "add"):
#             # разбираем особые таблицы, где нужно инкрементировать поле
#             if table in ("Tools", "Consumption") and "count" in data:
#                 existing = crud.get(rec_id)
#                 if existing:
#                     # вместо вставки — update count
#                     new_count = existing.count + data.get("count", 0)
#                     crud.update(rec_id, count=new_count)
#                     result = crud.get(rec_id).to_dict()
#                     return self._serialize_datetimes(result)
#             try:
#                 import dbSync
#                 dbSync.init_db = True
#                 # crud.add(**data)
#                 # 1) Если в payload был ключ "id", вы можете его убрать,
#                 # чтобы не пытаться вставлять существующий PK:
#                 clean_data = {k: v for k, v in data.items() if k != "id"}
#                 # 2) Вызов add: именованные параметры ONLY
#                 # (если PK автогенерируется — не передаём id совсем)
#                 instance = crud.add(**clean_data)
#                 dbSync.init_db = False
#                 item = crud.get(rec_id)
#                 result = item.to_dict()
#             except Exception as e:
#                 # print(f'[SyncManager][process_command][AddError] data: {data} ошибка: {e}\n{traceback.format_exc()}')
#                 item = crud.get(rec_id)
#                 if item is not None and item.to_dict() == data:
#                     result = item.to_dict()
#                 else:
#                     new_id = max(crud.get_all_ids(), default=0) + 1
#                     data["id"] = new_id
#                     print(f'[SyncManager][process_command][IntegrityError] new_id = {new_id} data: {data}')
#                     crud.add(new_id, **{k: v for k, v in data.items() if k != "id"})
#                     result = crud.get(new_id).to_dict()
#             # сериализуем все datetime обратно в строки
#             return self._serialize_datetimes(result)
#
#         # --- UPDATE ---
#         if op_lower == "update":
#
#             # crud.update(rec_id, **data)
#             crud.update(**data)
#
#             item = crud.get(rec_id)
#
#             if not item:
#                 raise
#
#             result = item.to_dict()
#             return self._serialize_datetimes(result)
#
#         # --- DELETE ---
#         if op_lower == "delete":
#             existing = crud.get(rec_id)
#             if existing:
#                 crud.delete(rec_id)
#                 result = existing.to_dict()
#             else:
#                 result = {"id": rec_id}
#             return self._serialize_datetimes(result)
#
#         raise ValueError(f"Операция {op} не поддерживается")
#
#     def _serialize_datetimes(self, obj):
#         if isinstance(obj, dict):
#             return {k: self._serialize_datetimes(v) for k, v in obj.items()}
#         elif isinstance(obj, list):
#             return [self._serialize_datetimes(v) for v in obj]
#         elif isinstance(obj, datetime):
#             return obj.isoformat()
#         else:
#             return obj
#
#     def get_current_data(self, work_session: Session, table: str, rec_id: Any) -> Optional[Dict[str, Any]]:
#         """
#         Возвращает текущее состояние записи для детекта конфликтов.
#         """
#
#         if isinstance(work_session, sessionmaker):
#             work_session = work_session()
#
#         crud_cls = self.crud_registry.get(table)
#         if crud_cls is None:
#             return None
#             # raise ValueError(f"Неизвестная таблица: {table!r}")
#
#         # тут мы **вызываем** конструктор EngineX(session)
#         crud = crud_cls(work_session)
#
#         if rec_id is None:
#             return None
#
#         record = crud.get(rec_id)
#         if record is None:
#             return None
#
#         # Приводим к dict
#         if hasattr(record, "to_dict"):
#             return record.to_dict()
#         elif hasattr(record, "__dict__"):
#             return {k: v for k, v in record.__dict__.items() if not k.startswith("_")}
#         elif isinstance(record, dict):
#             return record
#         else:
#             return None
#
#     def list(self, table: str) -> List[Any]:
#         """
#         Возвращает все записи таблицы.
#         """
#         crud = self.crud_registry.get(table)
#         if crud is None:
#             raise ValueError(f"Неизвестная таблица: {table}")
#         return crud.list()
#
#     def filter(self, table: str, **conds: Any) -> List[Any]:
#         """
#         Возвращает записи, удовлетворяющие условиям.
#         """
#         crud = self.crud_registry.get(table)
#         if crud is None:
#             raise ValueError(f"Неизвестная таблица: {table}")
#         return crud.filter(**conds)
#
#     def bulk_process(self, commands: List[Dict[str, Any]]) -> List[Any]:
#         """
#         Выполняет сразу несколько команд CRUD в одном вызове.
#         Удобно для оптимизации сетевого трафика.
#         """
#         results = []
#         for cmd in commands:
#             results.append(self.process_command(cmd))
#         return results
#
#
#     # def process_command(self, command: Dict[str, Any]) -> Any:
#     #     """
#     #     Делегирует одну команду синхронизации:
#     #       insert, update, delete.
#     #     """
#     #     table = command.get("table")
#     #     op = command.get("operation")
#     #     data = command.get("data", {})
#     #     rec_id = self.__extract_rec_id(data)
#     #
#     #     if not table or not op:
#     #         raise ValueError("Команда должна содержать 'table' и 'operation'")
#     #
#     #     crud_cls = self.crud_registry.get(table)
#     #     if crud_cls is None:
#     #         raise ValueError(f"Неизвестная таблица: {table}")
#     #     crud = crud_cls(self._session)
#     #     op = op.lower()
#     #
#     #     if rec_id is None:
#     #         rec_id = max(crud.get_all_ids(), default=0) + 1
#     #         # raise ValueError(f"'id' обязателен для {op_lower}")
#     #
#     #     if op == "insert" or op == "add":
#     #         try:
#     #             dbSync.init_db = True
#     #             crud.add(**data)
#     #             dbSync.init_db = False
#     #             result = crud.get(rec_id)
#     #             return result
#     #         except:
#     #             item = crud.get(rec_id)
#     #             print(f'[SyncManager][process_command][IntegrityError] data: {data}')
#     #             print(f'[SyncManager][process_command][IntegrityError] item: {item}')
#     #
#     #             if item is None:
#     #                 raise ValueError(f"[SyncManager] Получен None для таблицы {table}, данные: {data}")
#     #
#     #             if item.to_dict() == data:
#     #                 return item
#     #             else:
#     #                 index = max(crud.get_all_ids(), default=0) + 1
#     #                 if isinstance(data, dict):
#     #                     data['id'] = index
#     #                 else:
#     #                     data.id = index
#     #                 print(f'[SyncManager][process_command][IntegrityError] index = {index} data: {data}')
#     #                 crud.add(index, **data)
#     #                 return data
#     #
#     #     if op == "update":
#     #         if rec_id is None:
#     #             raise ValueError("'id' обязателен для update")
#     #         crud.update(index=rec_id, **data)
#     #         return crud.get(rec_id)
#     #     if op == "delete":
#     #         data = None
#     #         if rec_id is None:
#     #             raise ValueError("'id' обязателен для delete")
#     #         try:
#     #             data = crud.get(rec_id)
#     #             if data:
#     #                 crud.delete(rec_id)
#     #             else:
#     #                 data = {'id':rec_id}
#     #             return data
#     #         except:
#     #             return {'id':rec_id}
#     #
#     #     raise ValueError(f"Операция {op} не поддерживается")
#
#     # def get_current_data(self, session, table: str, rec_id: Any) -> Optional[Dict[str, Any]]:
# # Список изменений
# # Протокол CRUDInterface
# # – Чётко описал, какие методы должны быть у CRUD-классов (add, update, delete, get, list, filter, bulk).
# # Новые методы
# # list(table) — получить все записи.
# # filter(table, **conds) — отфильтровать по условию.
# # bulk_process(commands) — пакетная обработка списка команд.
# # Унификация ошибок
# # – Везде бросаем ValueError при отсутствии таблицы или обязательных полей.
# # Докстринги
# # – Полные описания места в архитектуре, протокола вызовов и возвращаемых результатов для каждого метода.
# # Типизация
# # – Использование Protocol, Dict, List, Optional для строгой типизации.
# # Приведение результата get_current_data к dict
# # – Поддержка моделей с методом to_dict или атрибутом __dict__.
# # Дополнительные рекомендации
# # Транзакционность
# # – В сложных сценариях объединять несколько операций в единую транзакцию.
# # Асинхронность
# # – Для масштабных батчей можно сделать async def bulk_process.
# # Метрики
# # – Внедрить счётчики CRUD-запросов, времени выполнения.
# # Unit-тесты
# # – Покрыть все новые ветки: insert, update без id, delete, list, filter, bulk.
# # Оптимизация bulk
# # – Если многие команды обращаются к одной таблице, группировать их внутри CRUD-классов.
