from sqlalchemy.orm import Session
from typing import Optional, List, Type  # , Type
from DB.Engine.CRUD import BaseCRUD
from DB.Models.ToolTypes import ToolTypes


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

    def add_tool_type(self,
                      tool_type_id: int,
                      name: str,
                      description: Optional[str] = None,
                      count: Optional[int] = None,
                      img: Optional[str] = None,
                      groups_id: Optional[int] = None
                      ) -> bool:
        """
        Добавляет новый тип инструмента.

        :param tool_type_id: Идентификатор типа.
        :param name: Название типа инструмента.
        :param description: Описание типа инструмента.
        :param count: Количество инструментов данного типа.
        :param img: Изображение, связанное с типом.
        :param groups_id: Идентификатор группы (если есть).
        :return: True, если операция успешна.
        """
        new_tool_type = ToolTypes(
            id=tool_type_id,
            name=name,
            description=description,
            count=count,
            img=img,
            groups_id=groups_id,
        )
        self.session.add(new_tool_type)
        self.session.commit()
        return True

    def get_tool_type_by_id(self, tool_type_id: int) -> Optional[ToolTypes]:
        """
        Получает тип инструмента по его идентификатору.
        """
        return self.get(tool_type_id)

    def update_tool_type(self,
                         tool_type_id: int,
                         name: str,
                         description: str,
                         count: int,
                         img: str,
                         groups_id: int
                         ) -> bool:
        """
        Обновляет данные типа инструмента.
        """
        return self.update(
            index=tool_type_id,
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
