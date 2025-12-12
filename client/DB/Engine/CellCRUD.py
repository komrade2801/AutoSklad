from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Type
from DB.Engine.BaseCRUD import BaseCRUD  # Импортируем BaseCRUD
from DB.Models.Cell import Cell  # Импортируем модель Cell
from DB.Models.Tools import Tools  # Импортируем модель Tools
from DB.Models.Group import Group  # Импортируем модель Group
from DB.Data.db import SessionLocal
from DB.Data.db import engine


class EngineCell(BaseCRUD):
    """
    Класс EngineCell предоставляет интерфейс для работы с таблицей Cell.
    Инкапсулирует CRUD-операции и предоставляет методы для работы с ячейками, их группами и инструментами.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineCell.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, Cell)

    def add_cell(self,
                 index: int,
                 number: int,
                 status_id: int,
                 tools_id: Optional[int] = None,
                 groups_id: Optional[int] = None,
                 description: Optional[str] = None
                 ) -> bool:
        """
        Добавляет новую ячейку в таблицу Cell.

        :param index:
        :param number: Номер ячейки.
        :param groups_id: Идентификатор группы.
        :param tools_id: Идентификатор инструмента.
        :param description: Описание ячейки или дополнительные детали.
        :return: True, если запись успешно добавлена, иначе False.
        """
        return self.add(
            id=index,
            number=number,
            groups_id=groups_id,
            tools_id=tools_id,
            description=description,
            status_id=status_id
        )

    def get_cell_by_id(self, cell_id: int) -> Optional[Cell]:
        """
        Получает ячейку по её уникальному идентификатору.

        :param cell_id: Уникальный идентификатор ячейки.
        :return: Объект Cell или None, если запись не найдена.
        """
        return self.get(cell_id)

    # noinspection PyTypeChecker
    def get_cells_with_groups_and_tools(self) -> list[Cell]:
        """
        Возвращает список всех ячеек с загруженными группами и инструментами.

        :return: Список объектов Cell с загруженными группами и инструментами.
        """
        return (
            self.session.query(Cell)
            .options(joinedload(Cell.groups), joinedload(Cell.tools))
            .all()
        )

    # def update_cell(self, cell_id: int, **kwargs) -> bool:
    #     """
    #     Обновляет параметры ячейки по её уникальному идентификатору.
    #
    #     :param cell_id: Уникальный идентификатор ячейки.
    #     :param kwargs: Поля и значения для обновления.
    #     :return: True, если запись успешно обновлена, иначе False.
    #     """
    #     return self.update(index=cell_id, **kwargs)
    # def update_cell(self,cell_id : int,
    #                 number,
    #                 description,
    #                 groups_id,
    #                 tools_id,
    #                 status_id,
    # ) -> bool:
    #     """
    #     Обновляет параметры ячейки по её уникальному идентификатору.
    #     :param status_id:
    #     :param tools_id:
    #     :param groups_id:
    #     :param description:
    #     :param number:
    #     :param cell_id: Уникальный идентификатор ячейки.
    #     :return: True, если запись успешно обновлена, иначе False.
    #     """
    #
    #     return self.update(
    #         index=cell_id,
    #         number=number,
    #         description=description,
    #         groups_id=groups_id,
    #         tools_id=tools_id,
    #         status_id=status_id,
    #     )
    def update_cell(self, cell_id: int,
                    number=None,
                    description=None,
                    groups_id=None,
                    tools_id=None,
                    status_id=None,
                    ) -> bool:
        """
            Обновляет параметры ячейки по её уникальному идентификатору.
            :param status_id:
            :param tools_id:
            :param groups_id:
            :param description:
            :param number:
            :param index: Уникальный идентификатор ячейки.
            :return: True, если запись успешно обновлена, иначе False.
        """
        print(f"update_cell {cell_id}, {number}, {description}, {groups_id}, {tools_id}, {status_id}")

        # 1) Загружаем из БД текущее состояние
        instance = self.session.query(self.model).get(cell_id)
        if not instance:
            return False

        # 2) Собираем только те поля, которые действительно изменились
        updates = {}
        if number is not None and instance.number != number:
            updates['number'] = number
        if description is not None and instance.description != description:
            updates['description'] = description
        # if groups_id is not None and instance.groups_id != groups_id:
        updates['groups_id'] = groups_id
        # if tools_id is not None and instance.tools_id != tools_id:
        updates['tools_id'] = tools_id
        # if status_id is not None and instance.status_id != status_id:
        updates['status_id'] = status_id

        # 3) Если нечего менять — вернём True, потому что ошибок нет
        if not updates:
            return True

        print(f"updates {cell_id}, {updates}")
        # 4) Иначе передаём только изменившиеся поля
        return self.update(index=cell_id, **updates)

    def delete_cell(self, cell_id: int) -> bool:
        """
        Удаляет ячейку по её уникальному идентификатору.

        :param cell_id: Уникальный идентификатор ячейки.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(cell_id)

    def get_cells_by_group(self, group_id: int) -> List[Cell]:
        """
        Возвращает список всех ячеек, принадлежащих указанной группе.

        :param group_id: Уникальный идентификатор группы.
        :return: Список объектов Cell.
        """
        return self.session.query(self.model).filter_by(groups_id = group_id).all()

    def get_cells_by_tool(self, tool_id: int) -> List[Cell]:  #
        """
        Возвращает список всех ячеек, связанных с указанным инструментом.

        :param tool_id: Уникальный идентификатор инструмента.
        :return: Список объектов Cell.
        """
        # return self.session.query(Cell).filter(Cell.tools_id == tool_id).all()
        return self.session.query(self.model).filter_by(tools_id=tool_id).all()

    def get_all_cells(self) -> List[Cell]:
        """
        Возвращает список всех ячеек в таблице Cell.

        :return: Список всех объектов Cell.
        """
        return self.all()

    def get_cells_by_description(self, description: str) -> list[Type[Cell]]:
        """
        Возвращает список ячеек, соответствующих указанному описанию.

        :param description: Описание ячейки.
        :return: Список объектов Cell.
        """
        return self.session.query(Cell).filter(Cell.description == description).all()

    def update_cell_status(self, cell_id: int, status_id: int) -> bool:
        """
        Обновляет статус ячейки по её уникальному идентификатору.

        :param cell_id: Уникальный идентификатор ячейки.
        :param status_id: Новый идентификатор статуса.
        :return: True, если статус успешно обновлён, иначе False.
        """
        return self.update(cell_id, status_id=status_id)
