from typing import Type, TypeVar

from DB.BaseCRUD import CoreEngine
from sqlalchemy.orm import Session

from dbSync.decorators import sync_aware

T = TypeVar("T")


class BaseCRUD(CoreEngine):

    def __init__(self, model: Type[T], *, session: Session = None, cache_maxsize: int = 1000, cache_ttl: int = 300):
        """
        Инициализация класса BaseCRUD.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        # Передаем модель и сессию в BaseCRUD.
        super().__init__(session, model, cache_maxsize=cache_maxsize, cache_ttl=cache_ttl)

    @sync_aware
    def add(self, *, index: int, **kwargs):
        # Убираем sync_context перед передачей в CoreEngine
        kwargs.pop('sync_context', None)
        return super().add(id=index, **kwargs)

    @sync_aware
    def update(self, *, index: int, **kwargs) -> bool:
        # Убираем sync_context перед передачей в CoreEngine
        kwargs.pop('sync_context', None)
        try:
            with self.transaction() as db:
                instance = db.query(self.model).filter_by(id=index).one_or_none()
                if not instance:
                    return False
                for k, v in kwargs.items():
                    setattr(instance, k, v)
                # тут же сделается commit при выходе из with
        except RuntimeError as e:
            # если UNIQUE constraint — считаем, что апдейт не применился
            if "Integrity error" in str(e):
                return False
            raise
        else:
            self._cache.clear()
            return True

    @sync_aware
    def delete(self, *, index: int, **kwargs):
        # Убираем sync_context перед передачей в CoreEngine
        kwargs.pop('sync_context', None)
        return super().delete(index=index)
