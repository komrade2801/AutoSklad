import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

# InventoryResponse,
from API.backend.request_models import ToolsCreate, ToolsAddResponse, AllGroupsResponse, GroupsAddResponse, \
    GroupsCreate, AllGroupsOnlyResponse
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.DropOperationsCRUD import EngineDropOperations
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations

from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.GroupCRUD import EngineGroup
# from DB.Engine.CellCRUD import EngineCell
#
# from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
# from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
# from DB.Engine.DeviceCRUD import EngineDevice

# from DB.Engine.ConsumptionCRUD import EngineConsumption
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
# from DB.Engine.OperationsConsumptionHasDeviceCRUD import EngineOperationsConsumptionHasDevice
from DB.Models.DropOperations import DropOperations
from DB.Models.LoadOperations import LoadOperations
from DB.Models.OperationsConsumption import OperationsConsumption

all_groups_router = APIRouter(tags=["All Groups"])


# , response_model=InventoryResponse
@all_groups_router.get("/")
def get_inventory(db: Session = Depends(get_db)):
    """
    Получает информацию для экрана "упрinventoryавление запасами".
    Метод:
      1. Получает список инструментов с информацией о наличии (stock, machine, in_use) через EngineTools.
      2. Для каждого инструмента определяет группу (через groups_id и EngineGroup).
      3. Группирует данные по названиям групп и формирует JSON-ответ, соответствующий примеру из js файла.
    """
    tools_crud = EngineTools()
    group_crud = EngineGroup()

    # Предположим, что метод get_inventory() возвращает список объектов с полями:
    # id, name, groups_id, stock, machine, in_use
    inventory_tools = tools_crud.get_inventory()
    if not inventory_tools:
        raise HTTPException(status_code=404, detail="Инструменты не найдены")

    # Группируем инструменты по группам
    inventory_by_group: Dict[str, list] = {}
    for tool in inventory_tools:
        group = group_crud.get_group_by_id(tool.groups_id)
        group_name = group.name if group else "Unknown"
        if group_name not in inventory_by_group:
            inventory_by_group[group_name] = []
        inventory_by_group[group_name].append({
            "id": tool.id,
            "barcode": tool.barcode,
            "name": tool.name,
            "description": tool.description,
            "img": tool.img,
            "plan_id": tool.plan_id,
            "groups_id": tool.groups_id,
        })

    # Формируем финальный JSON в виде: { "groups": { "0": { "name": "...", "value": { "0": {..}, ... } }, ... } }
    groups_output: Dict[str, Any] = {}
    for idx, (group_name, tools_list) in enumerate(inventory_by_group.items()):
        # Преобразуем список инструментов в объект с ключами-индексами
        tools_obj = {str(j): tool for j, tool in enumerate(tools_list)}
        groups_output[str(idx)] = {
            "name": group_name,
            "value": tools_obj
        }

    return {"groups": groups_output}


# Регистрация маршрута через роутер (all_tools_router)
@all_groups_router.post(
    "/create_groups",
    response_model=GroupsAddResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка при добавлении инструментов"}}
)
def create_groups(data: GroupsCreate, db: Session = Depends(get_db)):
    """
    Создает инструменты и соответствующий тип инструмента на основе полученных данных.

    Параметры:
      - data (GroupsCreate): содержит group_name, parent_group, description, img.
      - db (Session): сессия SQLAlchemy.

    Логика:
      1. Находим верхнюю группу, если parent_group != 0.
      2. Если parent_group == 0, указываем группу как корневую
      3. Добавляем записи в таблицу Groups с правильным paren_group_id.
    """
    try:
        group_crud = EngineGroup()

        group_parent_id = 0

        if data.parent_group and data.parent_group > 0:
            group_parent_id = data.parent_group

            # Проверка существования родительской группы
            parent_group = group_crud.get_group_by_id(group_parent_id)

            if not parent_group:
                raise HTTPException(
                    status_code=400, detail="Не удалось создать или найти группу")

        else:
            group_parent_id = 0


        if data.group_name:
            existing_group = group_crud.find_groups_by_name(name=data.group_name)
            if not existing_group:
                group = group_crud.create_group(name=data.group_name,
                    description=data.description,
                    paren_group_id=group_parent_id)
                if not group:
                    raise HTTPException(
                        status_code=400, detail="Не удалось создать")
            else:
                return GroupsAddResponse(status=204, message="Группа уже существует")

        return GroupsAddResponse(status=201, message="Группа успешно добавлена")

    except HTTPException:
        # Пробрасываем HTTP ошибки дальше
        raise
    except Exception as error:
        print(error, traceback.format_exc())
        # Общая ошибка — возвращаем 400 с сообщением
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении инструментов: {error}"
        )


@all_groups_router.get(
    "/get_all_groups_from_db",
    response_model=AllGroupsOnlyResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка формирования JSON"}}
)
def get_all_groups_from_db(device_number: int, db: Session = Depends(get_db)):
    try:
        devices_crud = EngineDevice()
        tools_has_device_crud = EngineToolsHasDevice()
        tools_crud = EngineTools()
        tool_type_crud = EngineToolTypes()
        e_group = EngineGroup()

        device = devices_crud.get_device_by_number(device_number)

        # 1) Забираем все группы
        __all_groups = []
        all_groups = e_group.get_all_groups()
        for group in all_groups:
            if not group.name:
                e_group.delete_group(group.id)
            else:
                __all_groups.append(group)
        all_groups = __all_groups

        # # 2) Фильтруем только "верхнеуровневые" (paren_group_id == None или 0)
        # main_groups = [
        #     g for g in all_groups
        #     if not g.paren_group_id or g.paren_group_id == 0
        # ]  # :contentReference[oaicite:0]{index=0}

        result = {"groups": {}}
        for i, group in enumerate(all_groups):

            print(f"group {i}: {group}")

            result["groups"][str(i)] = {
                "id": group.id,
                "name": group.name,
                "parent": group.paren_group_id
            }

        return result

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка формирования JSON: {e}"
        )


@all_groups_router.get("/groups_controls")
async def get_groups_status(db: Session = Depends(get_db)):
    e_load_operations = EngineLoadOperations()
    e_drop_operations = EngineDropOperations()
    e_consumption_operations = EngineOperationsConsumption()
    tool_types_crud = EngineToolTypes()
    tools_crud = EngineTools()

    # 1. Получить все типы инструментов
    tool_types = tool_types_crud.get_all_tool_types()

    result = {"groups": {}}

    for tool_type in tool_types:
        # 2. Инициализация счетчиков
        current_stock = tool_type.count
        machine = 0
        in_use = 0
        tools = tools_crud.get_tools_by_tool_type(tool_type.id)
        loads = []
        drops = []
        consumptions = []
        # 3. Получить все операции для типа
        for tool in tools:
            loads.append(e_load_operations.get_operations_by_tool(tool.id))
            drops.append(e_drop_operations.get_operations_by_tool(tool.id))
            consumptions.append(
                e_consumption_operations.get_operations_by_tool(tool_type.id))

        # 4. Обработка операций
        all_ops = sorted(
            loads + drops + consumptions,
            key=lambda x: x.date
        )

        for op in all_ops:
            if isinstance(op, LoadOperations):
                current_stock += 1
            elif isinstance(op, DropOperations):
                if current_stock > 0:
                    current_stock -= 1
                    machine += 1
            elif isinstance(op, OperationsConsumption):
                if machine > 0:
                    machine -= 1
                    in_use += 1

        # 5. Добавить в результат
        group_key = str(tool_type.group_id)  # Предполагается связь с Group
        if group_key not in result["groups"]:
            result["groups"][group_key] = {
                "name": tool_type.group.name,
                "value": {}
            }

        tool_entry = {
            "tools": tool_type.name,
            "stock": current_stock,
            "machine": machine,
            "in_use": in_use
        }
        result["groups"][group_key]["value"][str(tool_type.id)] = tool_entry

    return result
