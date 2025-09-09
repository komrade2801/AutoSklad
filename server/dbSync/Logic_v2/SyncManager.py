# import traceback
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

        if op_lower in ("insert", "add"):
            return self._handle_insert(crud, table, data, rec_id)
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
            raise

    def _handle_insert(self, crud, table, data, rec_id):
        """
        Обрабатывает операцию вставки (INSERT) для указанной таблицы.

        Специальная логика:
        1. Для таблиц Tools/Consumption: инкремент счётчика при существующей записи
        2. UPSERT-логика при существующем rec_id
        3. Чистая вставка с обработкой индекса

        Приоритеты для index:
        - Если clean_data содержит 'index' - используем его
        - Если нет - используем rec_id (если он int)
        - Если ни один вариант недоступен - ошибка

        После вставки получаем созданный объект через get() для сериализации
        """
        # 1) Спец‑случай с инкрементом
        if table in ("Tools", "Consumption") and "count" in data and rec_id is not None:
            existing = crud.get(rec_id)
            if existing:
                return self._increment_count(crud, rec_id, data["count"])

        # 2) Если запись уже есть — делать UPSERT‑логику
        if rec_id is not None and crud.get(rec_id):
            return self._upsert_update(crud, rec_id, data)

        # 3) Чистый INSERT
        clean_data = {k: v for k, v in data.items() if k != "id"}

        # Определяем ID для вставки и последующего получения объекта
        if "index" in clean_data:
            # Вариант 1: index явно указан в данных
            target_id = clean_data["index"]
            crud.add(**clean_data)
        elif isinstance(rec_id, int):
            # Вариант 2: используем rec_id как index
            target_id = rec_id
            crud.add(index=rec_id, **clean_data)
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

        # 3) Генерация события "после вставки"
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

    def _upsert_update(self, crud, rec_id, data):
        """Если запись есть — сравниваем и либо возвращаем, либо обновляем."""
        current = crud.get(rec_id).to_dict()
        incoming = {k: data[k] for k in data if k in current}
        if incoming == {k: current[k] for k in incoming}:
            return self._serialize(crud.get(rec_id))
        crud.update(index=rec_id, **incoming)
        return self._serialize(crud.get(rec_id))

    def _handle_update(self, crud, data, rec_id):
        # просто вызываем update(**data)
        crud.update(**data)
        return self._serialize(crud.get(rec_id))

    def _handle_delete(self, crud, rec_id):
        existing = crud.get(rec_id)
        if existing:
            crud.delete(rec_id)
            return self._serialize(existing)
        else:
            return {"id": rec_id}

    def get_current_data(self, table: str, rec_id: Any, work_session: Session = None) -> Optional[Dict[str, Any]]:
        """
        Возвращает текущее состояние записи для детекта конфликтов.
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

        # тут мы **вызываем** конструктор EngineX()
        crud = crud_cls()

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
            dbSync.init_db = True
            results.append(self.process_command(cmd))
            dbSync.init_db = False
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
