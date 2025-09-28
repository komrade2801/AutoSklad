from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Type
from DB.Engine.BaseCRUD import BaseCRUD
from DB.Models.Tools import Tools
from DB.Models.Plan import Plan
from DB.Models.Group import Group
from DB.Models.Cell import Cell
from DB.Models.History import History


class EngineTools(BaseCRUD):
    """
    Класс EngineTools предоставляет интерфейс для работы с таблицей Tools,
    включая методы работы с новыми полями и отношениями.
    """

    def __init__(self, session: Session):
        """
        Инициализация класса EngineTools.

        :param session: Объект сессии SQLAlchemy для выполнения операций с базой данных.
        """
        super().__init__(session, Tools)

    def add_tool(self,
            id: int,
            barcode: str,
            name: str,
            description: str = None,
            img: str = None,
            plan_id: Optional[int] = None,
            groups_id: Optional[int] = None
        ) -> bool:
        """
        Добавляет новый инструмент в таблицу Tools.

        :param barcode: Штрих-код инструмента.
        :param name: Название инструмента.
        :param description: Описание инструмента.
        :param img: Путь к изображению инструмента.
        :param plan_id: ID связанного плана.
        :param groups_id: ID связанной группы.
        :return: True, если инструмент успешно добавлен, иначе False.
        """
        return self.add(
            id=id,
            barcode=barcode,
            name=name,
            description=description,
            img=img,
            plan_id=plan_id,
            groups_id=groups_id
        )

    def get_tool_by_id(self, tool_id: int) -> Optional[Tools]:
        """
        Получает инструмент по уникальному идентификатору.

        :param tool_id: Уникальный идентификатор инструмента.
        :return: Объект Tools или None, если запись не найдена.
        """
        return self.get(tool_id)

    def update_tool(self, tool_id: int, **kwargs) -> bool:
        """
        Обновляет данные инструмента по уникальному идентификатору.

        :param tool_id: Уникальный идентификатор инструмента.
        :param kwargs: Поля и значения для обновления.
        :return: True, если данные успешно обновлены, иначе False.
        """
        return self.update(tool_id, **kwargs)

    def delete_tool(self, tool_id: int) -> bool:
        """
        Удаляет инструмент по уникальному идентификатору.

        :param tool_id: Уникальный идентификатор инструмента.
        :return: True, если запись успешно удалена, иначе False.
        """
        return self.delete(tool_id)

    def get_all_tools(self) -> List[Tools]:
        """
        Возвращает список всех инструментов.

        :return: Список объектов Tools.
        """
        return self.all()

    def get_tools_with_relations(self) -> list[Type[Tools]]:
        """
        Возвращает список всех инструментов с их связанными данными.

        :return: Список объектов Tools со связанными данными.
        """
        return self.session.query(Tools).options(
            joinedload(Tools.plans),
            joinedload(Tools.groups),
            joinedload(Tools.cells),
            joinedload(Tools.stories)
        ).all()

    def get_tools_by_group(self, group_id: int) -> list[Type[Tools]]:
        """
        Возвращает список инструментов, связанных с определенной группой.

        :param group_id: Уникальный идентификатор группы.
        :return: Список объектов Tools, связанных с группой.
        """
        return self.session.query(Tools).filter(Tools.groups_id == group_id).all()

    def get_tools_by_plan(self, plan_id: int) -> list[Type[Tools]]:
        """
        Возвращает список инструментов, связанных с определенным планом.

        :param plan_id: Уникальный идентификатор плана.
        :return: Список объектов Tools, связанных с планом.
        """
        return self.session.query(Tools).filter(Tools.plan_id == plan_id).all()

    def get_tools_by_barcode(self, barcode: str) -> list[Type[Tools]]:
        """
        Возвращает список инструментов, связанных с определенным планом.

        :param barcode: Штрихкод инструмента.
        :return: Список объектов Tools, связанных со штрихкодом.
        """
        return self.session.query(Tools).filter(Tools.barcode == barcode).all()

    def get_tool_history(self, tool_id: int) -> List[History]:
        """
        Возвращает историю, связанную с указанным инструментом.

        :param tool_id: Уникальный идентификатор инструмента.
        :return: Список объектов History, связанных с инструментом.
        """
        tool = self.get_tool_by_id(tool_id)
        return tool.stories if tool else []

