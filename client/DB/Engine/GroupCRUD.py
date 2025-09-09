from sqlalchemy.orm import Session
from typing import Optional, List

from .CellCRUD import EngineCell
from .ToolsCRUD import EngineTools
from ..Engine.BaseCRUD import BaseCRUD  # Импортируем BaseCRUD
from ..Models.Group import Group  # Импортируем модель Error


class EngineGroup(BaseCRUD):
    """
    Класс EngineGroup предоставляет удобный интерфейс для работы с таблицей Group в базе данных
    Он инкапсулирует логику CRUD операций и предоставляет дополнительные методы, специфичные для Group
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineGroup

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных
        """
        super().__init__(session, Group)
        self.e_tools = EngineTools(session=session)
        self.e_cell = EngineCell(session=self.session)


    def add_group(self,
                  index: Optional[int],
                  name: Optional[str] = None,
                  description: Optional[str] = None,
                  status: Optional[int] = None
                  ) -> bool:
        """
         Добавляет новую группу в таблицу Group.
        :param index: Уникальный идентификатор.
        :param name: Название группы.
        :param description: Описание группы.
        :param status: Статус группы (например, активна/не активна).
        :return: True если группа успешно добавлена, иначе False.
        """
        return self.add(
            id=index,
            name=name,
            description=description,
            status=status
        )

    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """
        Получает группу из таблицы Group по уникальному идентификатору.

        :param group_id: Уникальный идентификатор группы.
        :return: Объект Group или None, если группа не найдена.
        """
        return self.get(group_id)

    def update_group(self, group_id: int, name: Optional[str] = None, description: Optional[str] = None,
                     status: Optional[int] = None) -> bool:
        """
        Обновляет данные группы по уникальному идентификатору.

        :param group_id: Уникальный идентификатор группы.
        :param name: Новое название группы.
        :param description: Новое описание группы.
        :param status: Новый статус группы.
        :return: True если группа успешно обновлена, иначе False.
        """
        updates = {}
        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if status is not None:
            updates['Status'] = status
        return self.update(group_id, **updates)

    def delete_group(self, group_id: int) -> bool:
        """
        Удаляет группу по уникальному идентификатору.

        :param group_id: Уникальный идентификатор группы.
        :return: True если группа успешно удалена, иначе False.
        """
        return self.delete(group_id)

    def get_all_groups(self) -> List[Group]:
        """
        Получает все группы из таблицы Group.

        :return: Список всех групп в таблице Group.
        """
        return self.all()

    def get_groups_by_status(self, status: int) -> List[Group]:
        """
        Получает все группы с определённым статусом.

        :param status: Статус группы (например, активна/не активна).
        :return: Список объектов Group с заданным статусом.
        """
        return self.session.query(self.model).filter_by(status=status).all()

    def get_cells_by_group(self, group_id: int) -> Optional[List]:
        """
        Получает все связанные объекты Cell для заданной группы.

        :param group_id: Уникальный идентификатор группы.
        :return: Список объектов Cell или None, если группа не найдена.
        """
        group = self.get_group_by_id(group_id)
        if group:
            cells = self.e_cell.get_cells_by_group(group_id)
            return cells
        return None

    def get_tools_by_group(self, group_id: int) -> Optional[List]:
        """
        Получает все связанные объекты Tools для заданной группы.

        :param group_id: Уникальный идентификатор группы.
        :return: Список объектов Tools или None, если группа не найдена.
        """
        group = self.get_group_by_id(group_id)
        if group:
            tools = self.e_tools.get_tools_by_group(group.id)
            return tools
        return None
