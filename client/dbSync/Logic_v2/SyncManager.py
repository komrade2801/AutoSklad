from typing import Any, Dict, List, Optional, Protocol, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


from sqlalchemy import inspect

import dbSync


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

    def update(self, id: Any, **data) -> bool: ...

    def delete(self, id: Any) -> bool: ...

    def get(self, id: Any) -> Optional[Any]: ...

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

    def __init__(self, session: Session) -> None:

        from DB.crud_registry import crud_registry
        self.crud_registry: Dict[str, CRUDInterface] = crud_registry
        self._session = session

    def get_local_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Собирает схему из всех таблиц, для которых есть CRUD в реестре.
        Возвращает структуру {table_name: {column_name: type_name}}.
        """
        from DB.Data.base import Base
        from DB.Data.sqlite_db import engine
        schema: Dict[str, Dict[str, str]] = {}
        for tbl in Base.metadata.sorted_tables:
            cols: Dict[str, str] = {
                col.name: col.type.__class__.__name__.lower()
                for col in tbl.columns
            }
            schema[tbl.name] = cols
        return schema

    def __extract_rec_id(self, data: dict) -> Any:
        """
        Пытается получить идентификатор из data первым из полей
        'id', 'index', 'number'. Если ни одного нет — вернёт None.
        """
        for key in ("id", "index", "number"):
            if key in data and data[key] is not None:
                return data[key]
        return None

    def process_command(self, command: Dict[str, Any]) -> Any:
        """
        Делегирует одну команду синхронизации:
          insert, update, delete.
        """
        table = command.get("table")
        op = command.get("operation")
        data = command.get("data", {})
        rec_id = self.__extract_rec_id(data)

        if not table or not op:
            raise ValueError("Команда должна содержать 'table' и 'operation'")

        crud_cls = self.crud_registry.get(table)
        if crud_cls is None:
            raise ValueError(f"Неизвестная таблица: {table}")
        crud = crud_cls(self._session)
        op = op.lower()

        if rec_id is None:
            rec_id = max(crud.get_all_ids(), default=0) + 1
            # raise ValueError(f"'id' обязателен для {op_lower}")

        if op == "insert" or op == "add":
            try:
                dbSync.init_db = True
                crud.add(**data)
                dbSync.init_db = False
                result = crud.get(rec_id)
                return result
            except:
                item = crud.get(rec_id)
                print(f'[SyncManager][process_command][IntegrityError] data: {data}')
                print(f'[SyncManager][process_command][IntegrityError] item: {item}')

                if item is None:
                    raise ValueError(f"[SyncManager] Получен None для таблицы {table}, данные: {data}")

                if item.to_dict() == data:
                    return item
                else:
                    index = max(crud.get_all_ids(), default=0) + 1
                    if isinstance(data, dict):
                        data['id'] = index
                    else:
                        data.id = index
                    print(f'[SyncManager][process_command][IntegrityError] index = {index} data: {data}')
                    crud.add(index, **data)
                    return data

        if op == "update":
            if rec_id is None:
                raise ValueError("'id' обязателен для update")
            crud.update(index=rec_id, **data)
            return crud.get(rec_id)
        if op == "delete":
            data = None
            if rec_id is None:
                raise ValueError("'id' обязателен для delete")
            try:
                data = crud.get(rec_id)
                if data:
                    crud.delete(rec_id)
                else:
                    data = {'id':rec_id}
                return data
            except:
                return {'id':rec_id}

        raise ValueError(f"Операция {op} не поддерживается")

    # def get_current_data(self, session, table: str, rec_id: Any) -> Optional[Dict[str, Any]]:
    def get_current_data(self, session: Session, table: str, rec_id: Any) -> Optional[Dict[str, Any]]:
        """
        Возвращает текущее состояние записи для детекта конфликтов.
        """

        if isinstance(session, sessionmaker):
            session = session()

        crud_cls = self.crud_registry.get(table)
        if crud_cls is None:
            return None
            # raise ValueError(f"Неизвестная таблица: {table!r}")

        # тут мы **вызываем** конструктор EngineX(session)
        crud = crud_cls(session)

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
            results.append(self.process_command(cmd))
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
