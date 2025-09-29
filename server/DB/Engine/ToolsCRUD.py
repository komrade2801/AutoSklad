import random

from sqlalchemy.orm import Session  # , joinedload
from typing import Optional, List  # , Type
from DB.Engine.CRUD import BaseCRUD
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.DropOperationsCRUD import EngineDropOperations
from DB.Engine.DropOperationsHasDeviceCRUD import EngineDropOperationsHasDevice
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.LoadOperationsHasDeviceCRUD import EngineLoadOperationsHasDevice
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Models.Tools import Tools
from DB.Models.History import History


class EngineTools(BaseCRUD):
    """
    Класс EngineTools предоставляет интерфейс для работы с таблицей Tool,
    которая теперь содержит:
       - id,
       - inventory_number,
       - plan_id,
       - tool_type_id.

    Остальные связи (с Plan, Cell, History) доступны через свойства модели.
    """

    def __init__(self, session_db: Session = None):
        self.e_load_operations = EngineLoadOperations()
        self.e_load = EngineLoad()
        self.e_load_operations_has_device = EngineLoadOperationsHasDevice()
        self.e_tool_types = EngineToolTypes()
        self.e_tool_has_device = EngineToolsHasDevice()
        self.e_drop = EngineDrop()
        self.e_drop_operations = EngineDropOperations()
        self.e_drop_operations_has_device = EngineDropOperationsHasDevice()
        super().__init__(session=session_db, model=Tools)

    def add_tool(self,
                 tool_id: int,
                 inventory_number: str,
                 barcode: Optional[str] = None,
                 plan_id: Optional[int] = None,
                 tool_type_id: Optional[int] = None,
                 name: Optional[str] = "",
                 description: Optional[str] = "",
                 count: Optional[int] = None,
                 img: Optional[str] = "",
                 groups_id: Optional[int] = None
                 ) -> bool:
        """
        Добавляет новый инструмент.

        :param tool_id: Идентификатор инструмента.
        :param inventory_number: Инвентарный номер инструмента.
        :param plan_id: Идентификатор связанного плана (если есть).
        :param tool_type_id: Идентификатор типа инструмента.
        :return: True, если инструмент успешно добавлен.
        :param name: Название типа инструмента.
        :param description:  Описание типа инструмента.
        :param count:  Количество инструментов данного типа.
        :param img:  Изображение, связанное с типом.
        :param groups_id:  Идентификатор группы (если есть).
        """
        if barcode is None:
            barcode = inventory_number
        return self.add(
            index=tool_id,
            inventory_number=inventory_number,
            barcode=barcode,
            plan_id=plan_id,
            tool_type_id=tool_type_id,
            name=name,
            description=description,
            count=count,
            img=img,
            groups_id=groups_id
        )

    def get_tool_by_id(self, tool_id: int) -> Optional[Tools]:
        """
        Получает инструмент по уникальному идентификатору.
        """
        return self.get(tool_id)

    def update_tool(self,
                    tool_id: int,
                    inventory_number: str = None,
                    barcode: str = None,
                    plan_id: int = None,
                    tool_type_id: int = None,
                    **kwargs
                    ) -> bool:
        """
        Обновляет данные инструмента.
        """
        update_data = {}
        if inventory_number is not None:
            update_data['inventory_number'] = inventory_number
        if barcode is not None:
            update_data['barcode'] = barcode
        if plan_id is not None:
            update_data['plan_id'] = plan_id
        if tool_type_id is not None:
            update_data['tool_type_id'] = tool_type_id
        update_data.update(kwargs)
        return self.update(index=tool_id, **update_data)

    def delete_tool(self, tool_id: int) -> bool:
        """
        Удаляет инструмент по идентификатору.
        """
        return self.delete(index=tool_id)

    def get_all_tools(self) -> List[Tools]:
        """
        Возвращает список всех инструментов.
        """
        return self.all()

    def get_tools_by_tool_type(self, tool_type_id: int) -> List[Tools]:
        """
        Возвращает инструменты, связанные с определённым типом.
        """
        return self.session.query(Tools).filter(Tools.tool_type_id == tool_type_id).all()

    def get_tools_by_plan(self, plan_id: int) -> List[Tools]:
        """
        Возвращает инструменты, связанные с определённым планом.
        """
        return self.session.query(Tools).filter(Tools.plan_id == plan_id).all()

    def get_tool_history(self, tool_id: int) -> List[History]:
        """
        Возвращает историю изменений для указанного инструмента.
        """
        tool = self.get_tool_by_id(tool_id)
        return tool.stories if tool else []

    # -> List[Tools]:
    def get_inventory(self):
        """
        Возвращает список всех инструментов для инвентаризации.
        """
        return self.session.query(Tools).all()

    def get_tools_by_ids(self, tool_ids: List[int]) -> List[Tools]:
        """
        Возвращает инструменты по списку идентификаторов.
        """
        return self.session.query(Tools).filter(Tools.id.in_(tool_ids)).all()

    def delete_by_plans_id(self, plan_id: int) -> bool:
        """
        Удаляет все инструменты, связанные с данным планом.
        """
        self.session.query(Tools).filter(Tools.plan_id == plan_id).delete()
        self.session.commit()
        return True

    def update_by_plans_id(self, plan_id: int, **kwargs) -> bool:
        """
        Обновляет инструменты, связанные с данным планом.
        """
        self.session.query(Tools).filter(Tools.plan_id == plan_id).update(kwargs)
        self.session.commit()
        return True

    def update_tool_from_data(self, tool_id: int, data: dict) -> bool:
        """
        Обновление инструмента с использованием переданных данных.
        """
        return self.update_tool(tool_id, **data)

    # Если ранее использовались методы для связывания с ячейками или устройствами,
    # их реализация теперь зависит от наличия соответствующих таблиц и связей.
    # Например, можно реализовать через добавление записи в промежуточную таблицу.
    #
    # def link_tool_to_cell(self, tool_id: int, cell_id: int) -> bool:
    #     # Реализация установки связи инструмента с ячейкой
    #     pass
    #
    # def unlink_tool_from_cell(self, tool_id: int) -> bool:
    #     # Реализация удаления связи инструмента с ячейкой
    #     pass

    # self.e_load_operations
    # self.e_load
    # self.e_load_operations_has_device
    # self.e_load_operations
    # self.e_load
    # self.e_load_operations_has_device
    #
    # self.e_tool_has_device
    # self.e_drop
    # self.e_drop_operations
    # self.e_drop_operations_has_device

    def create_tool(self,
                    index: int = None,
                    name: str = None,
                    description: str = None,
                    img: str = None,
                    plan_id: int = None,
                    groups_id: int = None,
                    inventory_number=None
                    ):
        """
        Создает новый инструмент.
        """
        tool = {
            "id": None,
            "barcode": None,
            "name": None,
            "description": None,
            "img": None,
            "plan_id": None,
            "groups_id": None,
        }
        tool_type = self.e_tool_types.find_by_name(name)[0]
        # если нет типа, добавляем его
        type_id = max(self.e_tool_types.get_all_ids(), default=0) + 1
        if not tool_type and tool_type.description != description:
            type_id = max(self.e_tool_types.get_all_ids(), default=0) + 1
            self.e_tool_types.add_tool_type(
                tool_type_id=type_id,
                name=name,
                description=description,
                count=1,
                img=img,
                groups_id=groups_id,
            )
            tool_type = self.e_tool_types.get_tool_type_by_id(type_id)
        else:
            if not index:
                index = max(self.get_all_ids(), default=0) + 1
            if not inventory_number:
                inventory_number = self.e_tool_types.get_tool_type_by_id(tool_type_id=type_id)
            if not inventory_number:
                inventory_number = str(random.randint(111111111111, 999999999999))
            self.add_tool(
                tool_id=index,
                inventory_number=inventory_number,
                barcode=inventory_number,  # Set barcode equal to inventory_number
                plan_id=plan_id,
                tool_type_id=tool_type.id,
                name=name,
                description=description,
                count=1,
                img=img,
                groups_id=groups_id,
            )

        tool["id"] = index
        tool["barcode"] = inventory_number
        tool["inventory_number"] = inventory_number
        tool["name"] = tool_type.name
        tool["description"] = tool_type.description
        tool["img"] = tool_type.img
        tool["plan_id"] = plan_id
        tool["groups_id"] = tool_type.groups_id
        return tool

    def get_tools_for_load(self, device_id: int) -> Optional[List[Tools]]:
        """
        Список инструментов, которые можно загрузить на device_id —
        те, что не связаны с этим устройством сейчас.
        """
        # Все операции загрузки для устройства
        ops = self.e_load_operations_has_device.get_by_device(device_id)
        loaded_tool_ids = {op.tool_id for op in ops}
        # Те инструменты, которых ещё нет на устройстве
        return self.session.query(Tools).filter(~Tools.id.in_(loaded_tool_ids)).all()

    def get_tools_for_drop(self, device_id: int) -> Optional[List[Tools]]:
        """
        Список инструментов, которые можно выгрузить с device_id —
        те, что связаны с этим устройством сейчас.
        """
        ops = self.e_drop_operations_has_device.get_by_device(device_id)
        drop_tool_ids = {op.tool_id for op in ops}
        return self.session.query(Tools).filter(Tools.id.in_(drop_tool_ids)).all()

    def get_link(self, tool_id: int, device_id: int) -> Optional[Tools]:
        """
        Получает конкретную связь: если инструмент tool_id сейчас загружен
        на device_id (или есть запись о drop/load), возвращаем запись связи.
        """
        # Проверяем сначала загрузку
        link = self.e_load_operations_has_device.get_by_tool_and_device(tool_id, device_id)
        if link:
            return link
        # Иначе проверяем drop
        return self.e_drop_operations_has_device.get_by_tool_and_device(tool_id, device_id)

    def link_tool_to_cell(self, tool_id: int, cell_id: int) -> bool:
        """
        Привязывает инструмент к ячейке через ToolsHasDevice.
        """
        return self.e_tool_has_device.add_link(tool_id=tool_id, device_id=cell_id)

    def unlink_tool_from_cell(self, tool_id: int) -> bool:
        """
        Удаляет все связи инструмента с ячейками.
        """
        return self.e_tool_has_device.delete_by_tool(tool_id)

    def get_tools_by_group(self, group_id: int) -> List[Tools]:
        """
        Возвращает инструменты по принадлежности к группе типа.
        """
        # Получаем все типы инструментов из группы
        types = self.e_tool_types.get_by_group(group_id)
        type_ids = [t.id for t in types]
        return self.session.query(Tools).filter(Tools.tool_type_id.in_(type_ids)).all()
