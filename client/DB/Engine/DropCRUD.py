from sqlalchemy.orm import Session
from typing import List, Optional

from .BaseCRUD import BaseCRUD  # Импорт вашего BaseCRUD
from ..Models.Drop import Drop  # Импортируем модель Cell


class EngineDrop(BaseCRUD):
    """
    Класс EngineDrop предоставляет удобный интерфейс для работы с моделью Drop,
    используя функционал базового класса BaseCRUD.

    Основные функции:
    - Получение всех записей Drop.
    - Получение записи по ID.
    - Добавление новой записи.
    - Обновление существующей записи.
    - Удаление записи.
    - Поиск по полям: tools_id, mass_drop_id, cell_id.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineDrop.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
        super().__init__(session, Drop)

    def get_drop_by_id(self, drop_id: int) -> Optional[Drop]:
        """
        Получает ячейку по её уникальному идентификатору.

        :param drop_id: Уникальный идентификатор ячейки.
        :return: Объект Cell или None, если запись не найдена.
        """
        return self.get(drop_id)

    def get_by_tools_id(self, tools_id: int) -> List[Drop]:
        """
        Получает все записи Drop, связанные с указанным tools_id.

        :param tools_id: Идентификатор инструмента.
        :return: Список объектов Drop.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).all()

    def get_by_mass_drop_id(self, mass_drop_id: int) -> List[Drop]:
        """
        Получает все записи Drop, связанные с указанным mass_drop_id.

        :param mass_drop_id: Идентификатор массовой выдачи.
        :return: Список объектов Drop.
        """
        return self.session.query(self.model).filter_by(mass_drop_id=mass_drop_id).all()

    def get_by_cell_id(self, cell_id: int) -> List[Drop]:
        """
        Получает все записи Drop, связанные с указанным cell_id.

        :param cell_id: Идентификатор ячейки.
        :return: Список объектов Drop.
        """
        return self.session.query(self.model).filter_by(cell_id=cell_id).all()

    def add_drop(self, tools_id: int, mass_drop_id: int, cell_id: int, description: Optional[str] = None) -> bool:
        """
        Добавляет новую запись в таблицу Drop.

        :param tools_id: Идентификатор инструмента.
        :param mass_drop_id: Идентификатор массовой выдачи.
        :param cell_id: Идентификатор ячейки.
        :param description: Описание операции.
        :return: True если запись успешно добавлена, иначе False.
        """
        return self.add(tools_id=tools_id, mass_drop_id=mass_drop_id, cell_id=cell_id, description=description)

    def update_drop(self, drop_id: int, **kwargs) -> bool:
        """
        Обновляет существующую запись Drop.

        :param drop_id: Уникальный идентификатор записи.
        :param kwargs: Поля и значения для обновления.
        :return: True если запись успешно обновлена, иначе False.
        """
        return self.update(drop_id, **kwargs)

    def delete_drop(self, drop_id: int) -> bool:
        """
        Удаляет запись Drop по ID.

        :param drop_id: Уникальный идентификатор записи.
        :return: True если запись успешно удалена, иначе False.
        """
        return self.delete(drop_id)


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ..Data.base import Base  # Импорт вашего Base
    from ..Models.Drop import Drop  # Импорт модели Drop

    # from .EngineDrop import EngineDrop  # Импорт EngineDrop

    # Инициализация базы данных
    engine = create_engine('sqlite:///:memory:')  # Замените на вашу базу данных
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Создаем объект EngineDrop
    engine_drop = EngineDrop(session)

    # Пример добавления записи
    engine_drop.add_drop(tools_id=1, mass_drop_id=2, cell_id=3, description="Выдача инструмента")

    # Пример получения всех записей
    all_drops = engine_drop.all()
    print(all_drops)

    # Пример поиска по tools_id
    drops_by_tool = engine_drop.get_by_tools_id(1)
    print(drops_by_tool)

    # Пример обновления записи
    engine_drop.update_drop(1, description="Обновленное описание")

    # Пример удаления записи
    engine_drop.delete_drop(1)
