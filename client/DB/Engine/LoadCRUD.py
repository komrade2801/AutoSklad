from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional, List

from ..Data.base import Base
from ..Engine.BaseCRUD import BaseCRUD  # Предполагается, что BaseCRUD уже реализован
from ..Models.Load import Load  # Импорт модели Load


class EngineLoad(BaseCRUD):
    """
    Класс EngineLoad предоставляет интерфейс для работы с моделью Load.
    Наследуется от BaseCRUD, добавляя специфичные методы для модели Load.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineLoad.

        :param session: Объект сессии SQLAlchemy для работы с базой данных.
        """
        super().__init__(session, Load)

    def add_load(self, id: int, description: str, tools_id: int, mass_load_id: int, cell_id: int):
        """
        Добавляет новую запись о загрузке инструментов в базу данных.

        :param id: Уникальный идентификатор записи загрузки.
        :param description: Описание загрузки или дополнительные детали.
        :param tools_id: Идентификатор инструмента (внешний ключ на таблицу Tools).
        :param mass_load_id: Идентификатор массовой загрузки (внешний ключ на таблицу mass_load).
        :param cell_id: Идентификатор ячейки хранения (внешний ключ на таблицу Cell).
        :return: Объект добавленной записи или результат выполнения метода добавления.
        """
        return self.add(
            id=id,
            description=description,
            tools_id=tools_id,
            mass_load_id=mass_load_id,
            cell_id=cell_id,
        )

    def get_load_by_id(self, load_id: int) -> Optional[Load]:
        """
        Получает операцию Drop по её ID.

        :param load_id: Уникальный идентификатор операции.
        :return: Экземпляр DropOperations или None, если операция не найдена.
        """
        return self.get(load_id)

    def find_by_tools_id(self, tools_id: int) -> Load:
        """
        Возвращает список записей Load, связанных с указанным tools_id.

        :param tools_id: Идентификатор инструмента.
        :return: Список записей Load.
        """
        return self.session.query(self.model).filter_by(tools_id=tools_id).first()

    def find_by_mass_load_id(self, mass_load_id: int) -> List[Load]:
        """
        Возвращает список записей Load, связанных с указанным mass_load_id.

        :param mass_load_id: Идентификатор массовой загрузки.
        :return: Список записей Load.
        """
        return self.session.query(self.model).filter_by(mass_load_id=mass_load_id).all()

    def update_description(self, load_id: int, description: str) -> bool:
        """
        Обновляет описание для записи Load по указанному идентификатору.

        :param load_id: Идентификатор записи Load.
        :param description: Новое описание.
        :return: True, если обновление прошло успешно, иначе False.
        """
        return self.update(load_id, description=description)

    def delete_by_tools_id(self, tools_id: int) -> int:
        """
        Удаляет все записи Load, связанные с указанным tools_id.

        :param tools_id: Идентификатор инструмента.
        :return: Количество удаленных записей.
        """
        count = 0

        while True:
            records = self.find_by_tools_id(tools_id)
            if records:
                count += 1
                self.session.delete(records)
                self.session.commit()
            else:
                break
        return count
        # try:except Exception as e:
        #     self.session.rollback()
        #     print(f"Ошибка при удалении записей: {e}")
        #     return 0

    def count_by_cell_id(self, cell_id: int) -> int:
        """
        Возвращает количество записей Load, связанных с указанным cell_id.

        :param cell_id: Идентификатор ячейки.
        :return: Количество записей.
        """
        return self.session.query(self.model).filter_by(cell_id=cell_id).count()
