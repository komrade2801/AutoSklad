from sqlalchemy.orm import Session
from typing import Optional, List, Type  # , Type
from ..Engine.CRUD import BaseCRUD
from ..Models.ToolTypes import ToolTypes


class EngineToolTypes(BaseCRUD):
    """
    Класс EngineToolTypes обеспечивает операции с таблицей ToolTypes, которая содержит:
       - id,
       - name,
       - description,
       - count,
       - img,
       - groups_id.

    Для работы с инструментами данного типа (связь с таблицей Tool) используется свойство модели tools.
    """

    def __init__(self, session_db: Session = None):
        super().__init__(session=session_db, model=ToolTypes)

    def add_tool_type(self, *args, **kwargs) -> bool:
        """
        Добавляет новый тип инструмента.

        Поддерживает параметры: id, tool_type_id (id принимает приоритет), name, description, count, img, groups_id.
        """
        if args:
            raise ValueError("Use keyword arguments only")

        # Extract id, preferring 'id' over 'tool_type_id'
        tt_id = kwargs.get('id') or kwargs.get('tool_type_id')
        if tt_id is None:
            raise ValueError("id or tool_type_id must be provided")

        # Extract other fields
        name = kwargs.get('name')
        if name is None:
            raise ValueError("name must be provided")

        description = kwargs.get('description')
        count = kwargs.get('count')
        img = kwargs.get('img')
        groups_id = kwargs.get('groups_id')

        # Use self.add to trigger sync
        return self.add(
            index=tt_id,
            name=name,
            description=description,
            count=count,
            img=img,
            groups_id=groups_id,
        )

    def get_tool_type_by_id(self, tool_type_id: int) -> Optional[ToolTypes]:
        """
        Получает тип инструмента по его идентификатору.
        """
        return self.get(tool_type_id)

    def get_tool_types_by_ids(self, tool_type_ids: List[int]) -> List[ToolTypes]:
        """
        Возвращает инструменты по списку идентификаторов.
        """
        return self.session.query(ToolTypes).filter(ToolTypes.id.in_(tool_type_ids)).all()

    def update_tool_type(self, *args, **kwargs) -> bool:
        """
        Обновляет данные типа инструмента.

        Поддерживает параметры: id, tool_type_id (id принимает приоритет), name, description, count, img, groups_id.
        """
        if args:
            raise ValueError("Use keyword arguments only")

        # Extract id, preferring 'id' over 'tool_type_id'
        tt_id = kwargs.get('id') or kwargs.get('tool_type_id')
        if tt_id is None:
            raise ValueError("id or tool_type_id must be provided")

        # Ensure 'id' is in kwargs for sync compatibility
        kwargs['id'] = tt_id

        # Extract fields, allowing None for optional sync updates
        name = kwargs.get('name')
        description = kwargs.get('description')
        count = kwargs.get('count')
        img = kwargs.get('img')
        groups_id = kwargs.get('groups_id')

        return self.update(
            index=tt_id,
            name=name,
            description=description,
            count=count,
            img=img,
            groups_id=groups_id,
        )

    def delete_tool_type(self, tool_type_id: int) -> bool:
        """
        Удаляет тип инструмента по идентификатору.
        """
        return self.delete(index=tool_type_id)

    def get_all_tool_types(self) -> List[ToolTypes]:
        """
        Возвращает список всех типов инструментов.
        """
        return self.all()

    # def find_by_name(self, name: str) -> list[ToolTypes]:
    #     key = self._make_key("find_by_name", name)
    #     if key in self._cache:
    #         return self._cache[key]
    #
    #     with self.transaction() as db:
    #         result = db.query(self.model).filter(self.model.name == name).all()
    #
    #     self._cache[key] = result
    #     return result

    def find_by_name(self, name: str) -> list[ToolTypes]:
        key = self._make_key("find_by_name", name)
        if key in self._cache:
            return self._cache[key]

        with self.transaction() as db:
            result = db.query(self.model).filter(
                self.model.name.ilike(f"%{name}%")).all()

        self._cache[key] = result
        return result

    def find_by_full_name(self, full_name: str) -> Optional[ToolTypes]:
        """
        Find tool type by exact full name (name + " " + description).
        """
        full_name = full_name.strip()
        # Use loop to handle empty descriptions properly
        all_tt = self.all()
        for tt in all_tt:
            tt_full = f"{tt.name} {tt.description}".strip(
            ) if tt.description else tt.name
            if tt_full == full_name:
                return tt
        return None

    def find_by_name_and_group(self, name: str, group_id: int) -> Optional[ToolTypes]:
        return self.session.query(self.model).filter(
            self.model.name == name, self.model.groups_id == group_id).first()

    def get_tools_by_group(self, index) -> List[ToolTypes]:
        """
        Получает все инструменты, относящиеся к типам из указанной группы.

        :param index: Идентификатор группы.
        :return: Список инструментов (Tools), связанных с группой.
        """
        return self.session.query(ToolTypes).filter(ToolTypes.groups_id == index).all()

    def get_by_group(self, group_id: int) -> list[Type[ToolTypes]]:
        """
        Получает все записи ToolTypes, у которых groups_id == group_id.

        :param group_id: Идентификатор группы.
        :return: Список объектов ToolTypes из указанной группы.
        """
        return (
            self.session
            .query(ToolTypes)
            .filter(ToolTypes.groups_id == group_id)
            .all()
        )
