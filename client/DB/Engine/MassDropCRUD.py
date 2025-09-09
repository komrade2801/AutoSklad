from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from .BaseCRUD import BaseCRUD
from ..Models.MassDrop import MassDrop  # Импорт модели MassDrop
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class EngineMassDrop(BaseCRUD):
    """
    Класс EngineMassDrop, наследующий возможности BaseCRUD для работы с таблицей MassDrop.
    """

    def __init__(self, session: Session):
        """
        Инициализация EngineMassDrop.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
        super().__init__(session, MassDrop)

    def add_task(self, description: Optional[str] = None) -> bool:
        """
        Добавляет новую задачу массового удаления.

        :param description: Описание задачи.
        :return: True если задача успешно добавлена, иначе False.
        """
        return self.add(description=description)

    def get_task(self, task_id: int) -> Optional['MassDrop']:
        """
        Возвращает задачу по её уникальному идентификатору.

        :param task_id: Идентификатор задачи.
        :return: Объект задачи или None, если задача не найдена.
        """
        return self.get(task_id)

    def get_all_tasks(self) -> List['MassDrop']:
        """
        Возвращает список всех задач массового удаления.

        :return: Список объектов MassDrop.
        """
        return self.all()

    def update_task(self, task_id: int, description: Optional[str] = None) -> bool:
        """
        Обновляет описание задачи.

        :param task_id: Идентификатор задачи.
        :param description: Новое описание задачи.
        :return: True если обновление прошло успешно, иначе False.
        """
        return self.update(task_id, description=description)

    def delete_task(self, task_id: int) -> bool:
        """
        Удаляет задачу по её уникальному идентификатору.

        :param task_id: Идентификатор задачи.
        :return: True если удаление прошло успешно, иначе False.
        """
        return self.delete(task_id)

    def count_tasks(self) -> int:
        """
        Возвращает количество задач в таблице.

        :return: Число задач.
        """
        return self.count()

    def drop_table(self) -> bool:
        """
        Удаляет таблицу MassDrop из базы данных.

        :return: True если таблица успешно удалена, иначе False.
        """
        return self.drop()


if __name__ == "__main__":
    # Пример использования EngineMassDrop
    engine = create_engine('sqlite:///:memory:')  # Используйте вашу базу данных
    from DB.Data.base import Base
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # Инициализация
    session = SessionLocal()
    mass_drop_engine = EngineMassDrop(session)

    # Добавление задачи
    mass_drop_engine.add_task(description="Удаление устаревших данных")

    # Получение всех задач
    tasks = mass_drop_engine.get_all_tasks()
    print(tasks)

    # Обновление задачи
    mass_drop_engine.update_task(task_id=1, description="Обновленное описание")

    # Удаление задачи
    mass_drop_engine.delete_task(task_id=1)

    # Количество задач
    print(mass_drop_engine.count_tasks())
