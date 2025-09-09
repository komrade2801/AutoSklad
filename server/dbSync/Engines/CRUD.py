# dbSync/Engines/CRUD.py
from typing import Type, TypeVar, List

from sqlalchemy import ClauseElement

from DB.BaseCRUD import CoreEngine
from sqlalchemy.orm import Session



T = TypeVar("T")


class BaseCRUD(CoreEngine):

    def __init__(self, model: Type[T]=None,  session: Session=None, cache_maxsize: int = 1000, cache_ttl: int = 300):
        """
        Инициализация класса BaseCRUD.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        # from dbSync.Runner import create_db_session
        # Передаем модель и сессию в BaseCRUD.
        # session = session or create_db_session()
        from dbSync.sync_db import get_sync_session
        session = session or get_sync_session()
        super().__init__(session, model, cache_maxsize=cache_maxsize, cache_ttl=cache_ttl)


    def join_filter_order(
        self,
        joins: List[type] = None,
        filters: List[ClauseElement] = None,
        order_by=None
    ) -> List[T]:
        """
        JOIN + фильтры + сортировка в одном методе с кешированием результатов.

        :param joins: модели или подзапросы для JOIN
        :param filters: список SQLAlchemy-условий
        :param order_by: выражение для .order_by()
        :return: список готовых ORM-объектов
        """
        # формируем ключ кеша по параметрам
        key = self._make_key("join_filter_order", joins or [], tuple(filters or []), order_by)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            q = db.query(self.model)
            if joins:
                for rel in joins:
                    q = q.join(rel)
            if filters:
                q = q.filter(*filters)
            if order_by is not None:
                q = q.order_by(order_by)
            result = q.all()

        self._cache[key] = result
        return result