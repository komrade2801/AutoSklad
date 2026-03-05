# import traceback
import threading
from datetime import datetime
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
        Собирает схему из всех таблиц, для которых есть CRUD в реестре.
        Возвращает структуру {table_name: {column_name: type_name}}.
        """
        from DB.Data.base import Base
        # from DB.Data.sqlite_db import engine
        schema: Dict[str, Dict[str, str]] = {}
        for tbl in Base.metadata.sorted_tables:
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
        return crud_cls(session=self._session)

    def _parse_dates(self, data: Dict[str, Any]):
        for key in ("date", "datetime"):
            val = data.get(key)
            if isinstance(val, str):
                try:
                    data[key] = datetime.fromisoformat(val)
                except ValueError:
                    pass

    def _parse_incoming_datetimes(self, table: str, data: dict):

        mapper = sqlalchemy_inspect(self.crud_registry[table]().model)
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
        print(f'[COUNT_FIX][SERVER] _handle_insert called for table {table}, rec_id={rec_id}, sync_context={sync_context}')
        print(f'[COUNT_FIX][SERVER] data keys: {list(data.keys())}, count value: {data.get("count")}')

        # 1) Спец‑случай с инкрементом - только for non-sync operations (normal tool usage)
        if table in ("Tools", "Consumption") and "count" in data and rec_id is not None and not sync_context:
            existing = crud.get(rec_id)
            if existing:
                print(f'[COUNT_FIX][SERVER] Incrementing count for existing tool {rec_id}: {existing.count} + {data["count"]} = {existing.count + data["count"]}')
                return self._increment_count(crud, rec_id, data["count"])

        # For sync operations, bypass count increment logic
        if table in ("Tools", "Consumption") and sync_context:
            print(f'[COUNT_FIX][SERVER] Sync context - setting exact count value instead of incrementing')

        # 2) Если запись уже есть — делать UPSERT‑логику
        if rec_id is not None and crud.get(rec_id):
            return self._upsert_update(crud, rec_id, data, sync_context=sync_context)

        # 3) Добавление записи (ADD)
        # Удаляем id и другие невалидные поля
        # Получаем список валидных колонок модели
        valid_columns = {col.name for col in crud.model.__table__.columns}
        clean_data = {k: v for k, v in data.items() if k != "id" and k in valid_columns}
        
        # Дополнительная очистка: удаляем все поля, которых нет в модели
        # (например, вложенные объекты типа Status, которые должны были быть обработаны в DataTransformer)
        invalid_fields = [k for k in clean_data.keys() if k not in valid_columns]
        if invalid_fields:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_insert] WARNING: Removing invalid fields from {table}: {invalid_fields}')
            clean_data = {k: v for k, v in clean_data.items() if k in valid_columns}
        
        # Специальная обработка для Consumption: если history_id отсутствует, пытаемся найти связанную запись History
        if table == "Consumption" and ("history_id" not in clean_data or clean_data.get("history_id") is None):
            # Ищем последнюю запись History с тем же tools_id
            # Это временное решение для синхронизации, когда history_id не передаётся с клиента
            try:
                from DB.Engine.HistoryCRUD import EngineHistory
                history_crud = EngineHistory(self._session)
                # Пытаемся найти последнюю запись History с соответствующими параметрами
                if "tools_id" in clean_data:
                    # Ищем последнюю запись History для этого инструмента
                    all_history = history_crud.all()
                    matching_history = [h for h in all_history if h.tools_id == clean_data.get("tools_id")]
                    if matching_history:
                        # Берём последнюю запись (самую свежую)
                        latest_history = max(matching_history, key=lambda h: h.datetime if h.datetime else datetime.min)
                        clean_data["history_id"] = latest_history.id
                        print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_insert] Found related History record {latest_history.id} for Consumption with tools_id={clean_data.get("tools_id")}')
                    else:
                        # Если не нашли, выбрасываем ошибку, так как history_id обязателен
                        raise ValueError(f"Consumption requires history_id, but no History record found for tools_id={clean_data.get('tools_id')}")
                else:
                    raise ValueError("Consumption requires history_id, but both history_id and tools_id are missing")
            except Exception as e:
                print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_insert] ERROR: Failed to find related History for Consumption: {e}')
                raise ValueError(f"Cannot create Consumption without history_id: {e}") from e

        # Определяем ID для вставки и последующего получения объекта
        if "index" in clean_data:
            # Вариант 1: index явно указан в данных
            target_id = clean_data["index"]
            try:
                crud.add(sync_context=sync_context, **clean_data)
            except (RuntimeError, Exception) as e:
                # Если возникла ошибка (например, IntegrityError из-за race condition),
                # проверяем, не появилась ли запись между проверкой и вставкой
                error_str = str(e).lower()
                if "integrity" in error_str or "unique" in error_str or "constraint" in error_str:
                    print(f'[INTEGRITY_FIX][SERVER] IntegrityError при вставке {target_id}, проверяем существование записи. Ошибка: {e}')
                    existing = crud.get(target_id)
                    if existing:
                        # Запись появилась между проверкой и вставкой (race condition)
                        # Делаем upsert вместо insert
                        print(f'[INTEGRITY_FIX][SERVER] Запись {target_id} найдена после IntegrityError, выполняем upsert')
                        return self._upsert_update(crud, target_id, data, sync_context=sync_context)
                # Если это не IntegrityError или запись не найдена, пробрасываем ошибку дальше
                raise
        elif isinstance(rec_id, int):
            # Вариант 2: используем rec_id как index
            target_id = rec_id
            try:
                crud.add(index=rec_id, sync_context=sync_context, **clean_data)
            except (RuntimeError, Exception) as e:
                # Если возникла ошибка (например, IntegrityError из-за race condition),
                # проверяем, не появилась ли запись между проверкой и вставкой
                error_str = str(e).lower()
                if "integrity" in error_str or "unique" in error_str or "constraint" in error_str:
                    print(f'[INTEGRITY_FIX][SERVER] IntegrityError при вставке {target_id}, проверяем существование записи. Ошибка: {e}')
                    existing = crud.get(target_id)
                    if existing:
                        # Запись появилась между проверкой и вставкой (race condition)
                        # Делаем upsert вместо insert
                        print(f'[INTEGRITY_FIX][SERVER] Запись {target_id} найдена после IntegrityError, выполняем upsert')
                        return self._upsert_update(crud, target_id, data, sync_context=sync_context)
                # Если это не IntegrityError или запись не найдена, пробрасываем ошибку дальше
                raise
        else:
            # Вариант 3: критическая ошибка - нет источника для index
            raise ValueError(
                f"Missing 'index' for table {table}. "
                f"rec_id={rec_id} ({type(rec_id)} is not int, "
                "and 'index' not in payload"
            )

        # Получаем созданный объект из БД
        instance = crud.get(target_id)

        # Возвращаем сериализованную запись
        result = self._serialize(instance)

        # 4) Генерация события "после вставки"
        try:
            from dbSync.Logic_v2.sync_events import fire_after_insert
            fire_after_insert(table, result)
        except Exception:
            pass

        return result

    def _increment_count(self, crud, rec_id, delta):
        existing = crud.get(rec_id)
        new_count = existing.count + delta
        crud.update(index=rec_id, count=new_count)
        return self._serialize(crud.get(rec_id))

    def _upsert_update(self, crud, rec_id, data, sync_context=False):
        """Если запись есть — сравниваем и либо возвращаем, либо обновляем."""
        existing_obj = crud.get(rec_id)
        if existing_obj is None:
            # Если не нашли запись, логируем и создаём новую
            print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_upsert_update] Record {rec_id} not found in {crud.model.__tablename__}, creating new (sync_context={sync_context})')
            # Удаляем id и index из data перед созданием
            clean_data = {k: v for k, v in data.items() if k not in ("id", "index")}
            # Получаем валидные колонки модели
            valid_columns = {col.name for col in crud.model.__table__.columns}
            clean_data = {k: v for k, v in clean_data.items() if k in valid_columns}
            crud.add(index=rec_id, sync_context=sync_context, **clean_data)
            new_obj = crud.get(rec_id)
            return self._serialize(new_obj) if new_obj else None

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
                print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_upsert_update] Record {rec_id} in {crud.model.__tablename__} identical to existing, skipping update')
                return self._serialize(existing_obj)

        print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_upsert_update] Record {rec_id} in {crud.model.__tablename__} updating (sync_context={sync_context})')
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
            print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_update] Record {rec_id} not found, performing upsert')
            return self._upsert_update(crud, rec_id, data, sync_context=True)
        
        # Удаляем служебные поля, которые не должны обновляться
        # id, index - идентификаторы
        # created_at, updated_at - временные метки создания/обновления
        excluded_fields = {"id", "index", "created_at", "updated_at"}
        update_data = {k: v for k, v in data.items() if k not in excluded_fields}
        
        # Если нет данных для обновления, просто возвращаем существующую запись
        if not update_data:
            print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_update] No data to update for record {rec_id}, returning existing record')
            return self._serialize(existing_record)
        
        # Вызываем update с явным указанием index
        try:
            success = crud.update(index=rec_id, sync_context=True, **update_data)
            if not success:
                # Если обновление не удалось, возможно из-за IntegrityError, пробуем upsert
                print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_update] Update returned False for record {rec_id}, trying upsert')
                return self._upsert_update(crud, rec_id, data, sync_context=True)
        except Exception as e:
            # Если произошла ошибка при обновлении, пробуем upsert
            print(f'[ПОТОК][{threading.current_thread().name}][SyncManager][_handle_update] Error during update for record {rec_id}: {e}, trying upsert')
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
            raise ValueError(f"Неизвестная таблица: {table}")

        # Принудительное обновление сессии перед чтением
        # Это гарантирует, что мы получим актуальные данные из БД, а не устаревшие из кэша сессии
        # Сначала получаем сессию, которую будет использовать CRUD
        from DB.session import get_db_session
        session_to_use = self._session if self._session else get_db_session()
        
        try:
            if session_to_use:
                session_to_use.commit()
                session_to_use.expire_all()
                print(f"[SyncManager][get_current_data] Session expired before getting {table} id={rec_id} - fresh data will be loaded from DB")
        except Exception as e:
            print(f"[SyncManager][get_current_data] Warning: Failed to expire session before getting {table} id={rec_id}: {e}")

        # тут мы **вызываем** конструктор EngineX()
        # Передаем сессию, чтобы использовать ту же сессию, которую мы только что обновили
        crud = crud_cls(session=session_to_use)

        if rec_id is None:
            return None

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

    def list(self, table: str) -> List[Any]:
        """
        Возвращает все записи таблицы.
        """
        crud_cls = self.crud_registry.get(table)
        if crud_cls is None:
            raise ValueError(f"Неизвестная таблица: {table}")
        crud = crud_cls(session=self._session)
        return crud.list()

    def filter(self, table: str, **conds: Any) -> List[Any]:
        """
        Возвращает записи, удовлетворяющие условиям.
        """
        crud_cls = self.crud_registry.get(table)
        if crud_cls is None:
            raise ValueError(f"Неизвестная таблица: {table}")
        crud = crud_cls(session=self._session)
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

# Список изменений
# Протокол CRUDInterface
# – Чётко описал, какие методы должны быть у CRUD-классов (add, update, delete, get, list, filter, bulk).
# Новые методы
# list(table) — получить все записи.
# filter(table, **conds) — отфильтровать по условию.
# bulk_process(commands) — пакетная обработка списка команд.
# Унификация ошибок
# – Везде бросаем ValueError при отсутствии таблицы или обязательных полей.
# Докстринги
# – Полные описания места в архитектуре, протокола вызовов и возвращаемых результатов для каждого метода.
# Типизация
# – Использование Protocol, Dict, List, Optional для строгой типизации.
# Приведение результата get_current_data к dict
# – Поддержка моделей с методом to_dict или атрибутом __dict__.
# Дополнительные рекомендации
# Транзакционность
# – В сложных сценариях объединять несколько операций в единую транзакцию.
# Асинхронность
# – Для масштабных батчей можно сделать async def bulk_process.
# Метрики
# – Внедрить счётчики CRUD-запросов, времени выполнения.
# Unit-тесты
# – Покрыть все новые ветки: insert, update без id, delete, list, filter, bulk.
# Оптимизация bulk
# – Если многие команды обращаются к одной таблице, группировать их внутри CRUD-классов.
