import asyncio
import sqlite3
from typing import Protocol, TypeVar, Generic, Type, Optional, List, Any, Dict

import asyncsqlite3
from cachetools import TTLCache


T = TypeVar('T')
ID = int


class IRepository(Protocol, Generic[T]):
    """
    Репозиторий определяет контракт CRUD-операций над моделью T.
    """

    async def get(self, id: ID) -> Optional[T]:
        ...  # pragma: no cover

    async def all(self) -> List[T]:
        ...  # pragma: no cover

    async def filter_by(self, **kwargs: Any) -> List[T]:
        ...  # pragma: no cover

    async def add(self, obj_in: T) -> T:
        ...  # pragma: no cover

    async def update(self, id: ID, **kwargs: Any) -> bool:
        ...  # pragma: no cover

    async def delete(self, id: ID) -> bool:
        ...  # pragma: no cover


class AsyncSqliteRepository(Generic[T], IRepository[T]):
    """
    Асинхронный CRUD-репозиторий для SQLite с динамической генерацией SQL на основе моделей SQLAlchemy.
    Использует asyncsqlite3 и кеширование результатов чтения через cachetools.TTLCache.

    :param model: SQLAlchemy-модель, имеющая атрибут __table__
    :param db_path: путь к файлу SQLite
    :param cache_maxsize: максимальное число элементов в кеше
    :param cache_ttl: время жизни кеша в секундах
    """

    def __init__(
        self,
        model: Type[T],
        db_path: str,
        *,
        cache_maxsize: int = 1000,
        cache_ttl: int = 300,
    ):
        self.model = model
        self.db_path = db_path
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)
        self._lock = asyncio.Lock()

    async def _connect(self) -> asyncsqlite3.Connection:
        conn = await asyncsqlite3.connect(self.db_path)
        # Возвращаем dict-подобные строки по имени колонки
        conn.row_factory = sqlite3.Row
        return conn

    def _make_key(self, *parts: Any) -> str:
        return f"{self.model.__name__}:" + ":".join(str(p) for p in parts)

    async def get(self, id: ID) -> Optional[T]:
        """
        Получить объект по первичному ключу.

        :param id: первичный ключ записи
        :return: экземпляр модели или None, если не найден
        """
        key = self._make_key('get', id)
        async with self._lock:
            if key in self._cache:
                return self._cache[key]

        table = self.model.__table__
        sql = f"SELECT * FROM {table.name} WHERE id = ?"
        async with await self._connect() as conn:
            cur = await conn.execute(sql, (id,))
            row = await cur.fetchone()
        obj = self.model(**dict(row)) if row else None

        async with self._lock:
            self._cache[key] = obj
        return obj

    async def all(self) -> List[T]:
        """
        Получить все записи модели.

        :return: список экземпляров модели
        """
        key = self._make_key('all')
        async with self._lock:
            if key in self._cache:
                return self._cache[key]

        table = self.model.__table__
        sql = f"SELECT * FROM {table.name}"
        async with await self._connect() as conn:
            cur = await conn.execute(sql)
            rows = await cur.fetchall()
        objs = [self.model(**dict(r)) for r in rows]

        async with self._lock:
            self._cache[key] = objs
        return objs

    async def filter_by(self, **kwargs: Any) -> List[T]:
        """
        Фильтр по именованным полям модели.

        :param kwargs: поля и значения для фильтрации
        :return: список экземпляров модели
        """
        items = tuple(sorted(kwargs.items()))
        key = self._make_key('filter_by', items)
        async with self._lock:
            if key in self._cache:
                return self._cache[key]

        table = self.model.__table__
        cols = [f"{k} = ?" for k in kwargs.keys()]
        sql = f"SELECT * FROM {table.name} WHERE {' AND '.join(cols)}"
        params = tuple(kwargs.values())
        async with await self._connect() as conn:
            cur = await conn.execute(sql, params)
            rows = await cur.fetchall()
        objs = [self.model(**dict(r)) for r in rows]

        async with self._lock:
            self._cache[key] = objs
        return objs

    async def add(self, obj_in: T) -> T:
        """
        Добавить новую запись в таблицу.

        :param obj_in: объект модели (поля для вставки берутся из __dict__)
        :return: тот же объект с назначенным id
        :raises RuntimeError: при ошибке вставки
        """
        table = self.model.__table__
        data: Dict[str, Any] = {c.name: getattr(obj_in, c.name) for c in table.columns if c.name != 'id'}
        cols = ', '.join(data.keys())
        q_marks = ', '.join('?' for _ in data)
        sql = f"INSERT INTO {table.name} ({cols}) VALUES ({q_marks})"
        params = tuple(data.values())

        async with await self._connect() as conn:
            try:
                await conn.execute(sql, params)
                await conn.commit()
                # Получаем сгенерированный id
                cur = await conn.execute("SELECT last_insert_rowid() AS id")
                row = await cur.fetchone()
                setattr(obj_in, 'id', row['id'])
            except Exception as e:
                await conn.rollback()
                raise RuntimeError(f"Ошибка вставки: {e}") from e

        async with self._lock:
            self._cache.clear()
        return obj_in

    async def update(self, id: ID, **kwargs: Any) -> bool:
        """
        Обновить поля записи по id.

        :return:
        :param id: первичный ключ записи
        :param kwargs: поля и новые значения
        :return: True, если обновлено >=1 строка
        :raises RuntimeError: при ошибке обновления
        """
        table = self.model.__table__
        cols = ', '.join(f"{k} = ?" for k in kwargs.keys())
        sql = f"UPDATE {table.name} SET {cols} WHERE id = ?"
        params = tuple(kwargs.values()) + (id,)

        async with await self._connect() as conn:
            try:
                cur = await conn.execute(sql, params)
                await conn.commit()
                updated = cur.rowcount
            except Exception as e:
                await conn.rollback()
                raise RuntimeError(f"Ошибка обновления: {e}") from e

        async with self._lock:
            self._cache.clear()
        return updated > 0

    async def delete(self, id: ID) -> bool:
        """
        Удалить запись по id.

        :param id: первичный ключ записи
        :return: True, если удалено >=1 строка
        :raises RuntimeError: при ошибке удаления
        """
        table = self.model.__table__
        sql = f"DELETE FROM {table.name} WHERE id = ?"

        async with await self._connect() as conn:
            try:
                cur = await conn.execute(sql, (id,))
                await conn.commit()
                deleted = cur.rowcount
            except Exception as e:
                await conn.rollback()
                raise RuntimeError(f"Ошибка удаления: {e}") from e

        async with self._lock:
            self._cache.clear()
        return deleted > 0
