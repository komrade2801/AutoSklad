from datetime import datetime
from typing import Type, TypeVar
from sqlalchemy import inspect

from DB.BaseCRUD import CoreEngine
from sqlalchemy.orm import Session

from dbSync.decorators import sync_aware

T = TypeVar('T')


class BaseCRUD(CoreEngine):

    def __init__(self, session: Session, model: Type[T], *, cache_maxsize: int = 1000, cache_ttl: int = 300):
        """
        Инициализация класса BaseCRUD.
        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        # Передаем модель и сессию в BaseCRUD.
        super().__init__(session, model, cache_maxsize=cache_maxsize, cache_ttl=cache_ttl)

    @sync_aware
    def add(self, *args, **kwargs):
        clean = self._coerce_types(kwargs)
        return super().add(**clean) # *args,

    @sync_aware
    def update(self, *args, **kwargs):
        clean = self._coerce_types(kwargs)
        return super().update(*args,**clean)

    @sync_aware
    def delete(self, *args, **kwargs):
        clean = self._coerce_types(kwargs)
        return super().delete(*args, **clean)

    def _coerce_types(self, data: dict) -> dict:
        mapper = inspect(self.model)
        for col in mapper.mapper.column_attrs:
            name = col.key
            if name not in data or data[name] is None:
                continue

            sqltype = mapper.columns[name].type
            pytype = getattr(sqltype, 'python_type', None)
            if pytype is None:
                continue

            val = data[name]

            # если уже нужный тип — пропускаем
            if isinstance(val, pytype):
                continue

            try:
                if pytype is datetime:
                    # строка ISO-формата
                    if isinstance(val, str):
                        data[name] = datetime.fromisoformat(val)
                    # UNIX timestamp
                    elif isinstance(val, (int, float)):
                        data[name] = datetime.fromtimestamp(val)
                    else:
                        raise TypeError(f"Невозможно преобразовать {type(val)} в datetime")
                else:
                    data[name] = pytype(val)
            except Exception as e:
                raise ValueError(f"Поле {name!r}: не удалось привести {val!r} к {pytype.__name__}: {e}")

        return data
# import traceback
#
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import NoResultFound, IntegrityError
# from typing import Type, TypeVar, List, Optional
# from contextlib import contextmanager
#
# T = TypeVar('T')
#
#
# class BaseCRUD:
#     """
#     Класс BaseCRUD предоставляет универсальный интерфейс для выполнения стандартных операций CRUD
#     (Create, Read, Update, Delete) над различными таблицами базы данных, определенными с помощью SQLAlchemy.
#
#     Основные методы класса:
#     - count(): Получение количества записей в таблице.
#     - add(**kwargs): Добавление новой записи в таблицу.
#     - all(): Получение списка всех записей в таблице.
#     - get(index): Получение записи по уникальному идентификатору.
#     - update(index, **kwargs): Обновление существующей записи по уникальному идентификатору.
#     - delete(index): Удаление записи по уникальному идентификатору.
#     - drop(): Удаление таблицы из базы данных.
#     """
#
#     def __init__(self, session: Session, model: Type[T]):
#         """
#         Инициализация класса BaseCRUD.
#
#         :param session: Объект сессии SQLAlchemy для работы с базой данных.
#         :param model: Модель SQLAlchemy, с которой будет работать класс.
#         """
#         self.session = session
#         self.model = model
#
#     @contextmanager
#     def transaction(self):
#         """Контекстный менеджер для работы с транзакциями."""
#
#         yield self.session
#         self.session.commit()
#         # try:except Exception:
#         #     self.session.rollback()
#         #     raise
#         # finally:
#         #     self.session.close()
#
#     def count(self) -> int:
#         """Возвращает количество записей в таблице."""
#         return self.session.query(self.model).count()
#
#     def add(self, **kwargs) -> bool:
#         """
#         Добавляет новую запись в таблицу.
#
#         :param kwargs: Поля и значения для создания новой записи.
#         :return: True если запись успешно добавлена, иначе False.
#         """
#         instance = self.model(**kwargs)
#
#         self.session.add(instance)
#         with self.transaction():
#             pass  # commit happens in the context manager
#         return True
#         # try:except IntegrityError as e:
#         #     print(f"Ошибка при добавлении записи: {e}")
#         #     return False
#
#     def all(self) -> List[T]:
#         """Возвращает список всех записей в таблице."""
#         return self.session.query(self.model).all()
#
#     def get(self, index: int) -> Optional[T]:
#         """
#         Получает запись по уникальному идентификатору.
#
#         :param index: Уникальный идентификатор записи.
#         :return: Запись или None если не найдена.
#         """
#         try:
#             return self.session.query(self.model).filter_by(id=index).one()
#         except NoResultFound:
#             print(traceback.format_exc())
#             return None
#
#     def update(self, index: int, **kwargs) -> bool:
#         """
#         Обновляет существующую запись по уникальному идентификатору.
#
#         :param index: Уникальный идентификатор записи для обновления.
#         :param kwargs: Поля и значения для обновления записи.
#         :return: True если запись успешно обновлена, иначе False.
#         """
#         instance = self.get(index)
#         if instance is not None:
#             for key, value in kwargs.items():
#                 setattr(instance, key, value)
#             with self.transaction():
#                 pass  # commit happens in the context manager
#             return True
#         return False
#
#     def delete(self, index: int) -> bool:
#         """
#         Удаляет запись по уникальному идентификатору.
#
#         :param index: Уникальный идентификатор записи для удаления.
#         :return: True если запись успешно удалена, иначе False.
#         """
#         instance = self.get(index)
#         if instance is not None:
#             self.session.delete(instance)
#             with self.transaction():
#                 pass  # commit happens in the context manager
#             return True
#         return False
#
#     def drop(self) -> bool:
#         """
#         Удаляет таблицу из базы данных.
#
#         :return: True если таблица успешно удалена, иначе False.
#         """
#
#         self.model.__table__.drop(self.session.bind)
#         return True
#         # try:except Exception as e:
#         #     print(f"Ошибка при удалении таблицы: {e}")
#         #     return False
#
#     def get_all_ids(self) -> List[int]:
#         """
#         Возвращает список всех значений поля 'id' из таблицы.
#
#         :return: Список значений поля 'id'.
#         """
#
#         ids = self.session.query(self.model.id).all()  # Запрашиваем все значения id
#         return [id_tuple[0] for id_tuple in ids]  # Извлекаем из списка кортежей только значения id
#         # try:except AttributeError:
#         #     print(f"Модель {self.model.__name__} не имеет поля 'id'.")
#         #     return []
#         # except Exception as e:
#         #     print(f"Ошибка при получении списка идентификаторов: {e}")
#         #     return []
#
#     def delete_all(self) -> bool:
#         """
#         Удаляет все записи из таблицы.
#
#         :return: True, если все записи успешно удалены, иначе False.
#         """
#
#         with self.transaction():
#             self.session.query(self.model).delete()
#         return True
#         # try:except Exception as e:
#         #     print(f"Ошибка при удалении всех записей: {e}")
#         #     return False
