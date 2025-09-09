# DB/BaseCRUD.py
"""
base_crud.py

Универсальный CRUD-класс для SQLAlchemy-моделей с встраиваемым кешированием результатов чтения
в памяти (TTLCache). Подходит для небольших и средних приложений, не требует внешнего сервиса.

Основные возможности:
- Стандартные операции CRUD: add, get, all, update, delete, delete_all, drop, count.
- Гибкие методы фильтрации: filter_by, filter, with_options, join_and_filter.
- Динамические методы get_by_<field> для любой колонки модели.
- Внутренний кеш с TTL и ограничением размера (_cache), автоматически инвалидация при изменении данных.
"""

from sqlalchemy import ClauseElement
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import NoResultFound, SQLAlchemyError, IntegrityError
from typing import Type, TypeVar, List, Optional, Generator
from contextlib import contextmanager
from cachetools import TTLCache



T = TypeVar('T')


class CoreEngine:
    """
    Базовый класс для CRUD-операций над SQLAlchemy-моделью с встраиваемым кешированием.

    Атрибуты:
        session (Session): объект сессии SQLAlchemy.
        model (Type[T]): класс модели SQLAlchemy.
        _cache (TTLCache): кеш чтения с ограниченным размером и временем жизни.

    Параметры конструктора:
        session (Session): сессия для работы с БД.
        model (Type[T]): модель, над которой выполняются операции.
        cache_maxsize (int): максимальное число элементов в кеше (по умолчанию 1000).
        cache_ttl (int): время жизни элемента в кеше в секундах (по умолчанию 300).
    """

    def __init__(self,
                 session: Session,
                 model: Type[T],
                 *,
                 cache_maxsize: int = 1000,
                 cache_ttl: int = 300):
        """
        Инициализирует CRUD-класс и настраивает кеш.

        :param session: Объект SQLAlchemy Session.
        :param model: SQLAlchemy-модель для операций.
        :param cache_maxsize: Максимальное количество записей в кеше.
        :param cache_ttl: Время жизни кеша в секундах.
        """
        from DB.session import get_db_session
        self.session = session or get_db_session()  # получаем Session, не генератор
        self.model = model
        self._cache = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl)

    def _make_key(self, *parts) -> str:
        """
        Генерирует уникальный ключ для кеша на основе частей.

        :param parts: Любые объекты, преобразуемые в строку.
        :return: Строковый ключ формата ModelName:part1:part2:...
        """
        return f"{self.model.__name__}:" + ":".join(str(p) for p in parts)

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        Контекстный менеджер для транзакций SQLAlchemy.

        При выходе без исключений вызывает commit().
        При IntegrityError или любом SQLAlchemyError откатывает транзакцию и пробрасывает RuntimeError.

        :yield: объект сессии для выполнения запросов внутри блока.
        """
        try:
            yield self.session
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise RuntimeError(f"Integrity error: {e}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error: {e}") from e

    # ————— Методы чтения с кешем —————

    def get(self, index: int) -> Optional[T]:
        """
        Возвращает запись по первичному ключу (id) с кешированием.

        :param index: Значение поля id.
        :return: Объект модели или None, если не найден.
        """
        key = self._make_key("get", index)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            try:
                result = db.query(self.model).filter_by(id=index).one()
            except NoResultFound:
                result = None

        self._cache[key] = result
        return result

    def all(self) -> List[T]:
        """
        Возвращает список всех записей модели с кешированием.

        :return: Список объектов модели.
        """
        key = self._make_key("all")
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            result = db.query(self.model).all()

        self._cache[key] = result
        return result

    def filter_by(self, **kwargs):  #: -> List[T]
        """
        Выполняет фильтрацию по переданным полям модели (filter_by) с кешированием.

        :param kwargs: Имя_поля=значение для фильтрации.
        :return: Список объектов модели, удовлетворяющих условию.
        """
        items = tuple(sorted(kwargs.items()))
        key = self._make_key("filter_by", items)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            result = db.query(self.model).filter_by(**kwargs).all()  #

        self._cache[key] = result
        return result

    def filter(self, *criteria: ClauseElement) -> List[T]:
        """
        Выполняет произвольную фильтрацию (filter) с любыми SQLAlchemy-выражениями.

        :param criteria: Одно или несколько условий SQLAlchemy.
        :return: Список объектов модели, удовлетворяющих всем критериям.
        """
        key = self._make_key("filter", criteria)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            result = db.query(self.model).filter(*criteria).all()

        self._cache[key] = result
        return result

    def with_options(self, *opts) -> List[T]:
        """
        Выполняет запрос с опциями загрузки (joined load, selectinload и т.п.) с кешированием.

        :param opts: SQLAlchemy LoadOptions.
        :return: Список объектов модели с применёнными опциями.
        """
        key = self._make_key("with_options", opts)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            result = db.query(self.model).options(*opts).all()

        self._cache[key] = result
        return result

    def build_query(
        self,
        joins: list[type] = None,
        *filters: ClauseElement
    ) -> Query:
        """
        Построить SQLAlchemy Query с заданными JOIN и WHERE-условиями,
        но ещё не выполнить его.
        """
        q = self.session.query(self.model)
        if joins:
            for rel in joins:
                q = q.join(rel)
        if filters:
            q = q.filter(*filters)
        return q

    def join_and_filter(self,
                        joins: List[type],
                        *criteria: ClauseElement) -> List[T]:
        """
        Делает JOIN по списку моделей и фильтрацию по критериям с кешированием.

        :param joins: Список связанных моделей для JOIN.
        :param criteria: Условия фильтрации после JOIN.
        :return: Список объектов модели.
        """
        key = self._make_key("join_and_filter", joins, criteria)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            q = db.query(self.model)
            for rel in joins:
                q = q.join(rel)
            if criteria:
                q = q.filter(*criteria)
            result = q.all()

        self._cache[key] = result
        return result

    def __getattr__(self, name: str):
        """
        Автоматически обрабатывает методы вида get_by_<field> с кешированием.

        :param name: Имя метода.
        :return: Функцию, выполняющую filter_by(<field>=value).
        :raises AttributeError: Если имя метода не соответствует шаблону.
        """
        prefix = "get_by_"
        if name.startswith(prefix):
            field = name[len(prefix):]

            def fn(value):
                """
                Динамически сгенерированный метод для фильтрации по единственному полю.
                """
                key = self._make_key(f"get_by_{field}", value)
                if key in self._cache:
                    return self._cache[key]

                with self.transaction() as db:
                    column = getattr(self.model, field)
                    result = db.query(self.model).filter(column == value).all()

                self._cache[key] = result
                return result

            return fn

        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    # ————— Методы изменения (сброс кеша) —————

    def add(self, **kwargs) -> bool:
        """
        Создаёт новую запись и очищает кеш.

        :param kwargs: Поля и значения для создания объекта.
        :return: True при успешном добавлении.
        """
        with self.transaction() as db:
            instance = self.model(**kwargs)
            db.add(instance)
        self._cache.clear()
        return True

    def update(self, *, index: int=0, **kwargs) -> bool:
        """
        Обновляет существующую запись по id и очищает кеш.

        :param index: Значение поля id для поиска
        :param kwargs: поля и новые значения
        :return: True, если запись найдена и обновлена, иначе False
        """
        with self.transaction() as db:
            instance = db.query(self.model).filter_by(id=index).one_or_none()
            if not instance:
                return False
            for k, v in kwargs.items():
                setattr(instance, k, v)
        self._cache.clear()
        return True

    def delete(self, *, index: int=0) -> bool:
        """
        Удаляет запись по id и очищает кеш.

        :param index: Значение поля id
        :return: True, если запись найдена и удалена, иначе False
        """
        with self.transaction() as db:
            instance = db.query(self.model).filter_by(id=index).one_or_none()
            if not instance:
                return False
            db.delete(instance)
        self._cache.clear()
        return True

    def delete_all(self) -> bool:
        """
        Удаляет все записи из таблицы модели и очищает кеш.

        :return: True при успешном удалении
        """
        with self.transaction() as db:
            db.query(self.model).delete()
        self._cache.clear()
        return True

    def drop(self) -> bool:
        """
        Удаляет таблицу модели из БД и очищает кеш.

        :return: True при успешном удалении таблицы
        """
        with self.transaction() as db:
            self.model.__table__.drop(db.bind)
        self._cache.clear()
        return True

    def get_all_ids(self) -> List[int]:
        """
        Возвращает список всех id записей модели.

        :return: Список целых значений id
        """
        with self.transaction() as db:
            ids = db.query(self.model.id).all()
        return [i[0] for i in ids]

    def count(self) -> int:
        """
        Подсчитывает количество записей модели.

        :return: Целое число — количество записей
        """
        return len(self.all())
