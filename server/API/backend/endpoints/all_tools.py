import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

# InventoryResponse,
from API.backend.request_models import ToolsCreate, ToolsAddResponse, AllGroupsResponse, AllToolTypesResponse
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

all_tools_router = APIRouter(tags=["All Tools"])


# , response_model=InventoryResponse
@all_tools_router.get("/")
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
@all_tools_router.post(
    "/create_tools",
    response_model=ToolsAddResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка при добавлении инструментов"}}
)
def create_tools(data: ToolsCreate, db: Session = Depends(get_db)):
    """
    Создает инструменты и соответствующий тип инструмента на основе полученных данных.

    Параметры:
      - data (ToolsCreate): содержит group_id, tool_name, description, count, img, tools.
      - db (Session): сессия SQLAlchemy.

    Логика:
      1. Находим группу по id (data.group_id)
      2. Используем группу для fields.groups_id при создании ToolType.
      3. Добавляем записи в таблицу Tools с правильным tool_type_id.
    """
    try:
        tools_crud = EngineTools()
        tool_type_crud = EngineToolTypes()
        group_crud = EngineGroup()

        # 1. Найти группу
        group = group_crud.get_group_by_id(data.group_id)
        # top_group = group_crud.find(data.group, data.description or "")
        if not group:
            raise HTTPException(
                status_code=400, detail="Не удалось найти группу")

        # # Гарантируем, что родитель верхней группы = 0
        # if top_group.paren_group_id not in (None, 0):
        #     group_crud.update_group(
        #         group_id=top_group.id,
        #         name=top_group.name,
        #         description=top_group.description,
        #         paren_group_id=0
        #     )

        # 3. Создать новый тип инструмента
        new_tt_id = max(tool_type_crud.get_all_ids(), default=0) + 1
        tool_type_crud.add_tool_type(
            tool_type_id=new_tt_id,
            name=data.tool_name,
            description=data.description,
            count=data.count,
            img=data.img,
            groups_id=data.group_id,
        )

        # 4. Добавить каждую единицу инвентаря
        for inv in data.tools.values():
            tool_id = max(tools_crud.get_all_ids(), default=0) + 1
            tools_crud.add_tool(
                tool_id=tool_id,
                inventory_number=inv,
                plan_id=None,
                tool_type_id=new_tt_id,
                name=data.tool_name,
                description=data.description,
                count=data.count,
                img=data.img,
                groups_id=data.group_id,
            )

        return ToolsAddResponse(status=200, message="Инструменты успешно добавлены")

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


@all_tools_router.get(
    "/get_groups_from_db",
    response_model=AllGroupsResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка формирования JSON"}}
)
def get_groups_from_db(device_number: int, db: Session = Depends(get_db)):
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

        # 2) Фильтруем только "верхнеуровневые" (paren_group_id == None или 0)
        main_groups = [
            g for g in all_groups
            if not g.paren_group_id or g.paren_group_id == 0
        ]  # :contentReference[oaicite:0]{index=0}

        result = {"groups": {}}
        for i, group in enumerate(main_groups):
            # 3) Ищем его подгруппы и всегда проверяем прямые инструменты
            subgroup_dict = {}
            subgroups = e_group.get_groups_by_paren_group_id(group.id)
            direct_instruments = tool_type_crud.get_tools_by_group(group.id)

            # Сначала добавляем прямые инструменты, если они есть
            if direct_instruments:
                values_dict = {}
                for k, tool in enumerate(direct_instruments):
                    if tool.count <= 0:
                        continue
                    # Проверить есть ли свободный инструмент.
                    tools = tools_crud.get_tools_by_tool_type(tool.id)
                    count_elements = 0
                    links = tools_has_device_crud.get_tools_by_device_id(
                        device.id)
                    for __tool in tools:
                        if __tool.id in links:
                            continue
                        count_elements += 1
                    if count_elements == 0:
                        continue

                    key = str(k)
                    tool_info = f"{tool.name} {tool.description}"
                    values_dict[key] = {
                        "tools": tool_info,
                        "sum": str(count_elements)
                    }

                subgroup_dict["direct"] = {
                    "SGName": "-",
                    "value": values_dict
                }

            # Затем добавляем подгруппы, если они есть
            if subgroups:
                # Начинаем нумерацию после ключей предыдущих
                current_key = len(subgroup_dict)
                for j, subgroup in enumerate(subgroups):
                    instruments = tool_type_crud.get_tools_by_group(
                        subgroup.id)
                    values_dict = {}
                    if instruments:
                        for k, tool in enumerate(instruments):
                            # Пропускаем инструменты с count == 0
                            if tool.count <= 0:
                                continue
                            # Проверить есть ли свободный инструмент.
                            tools = tools_crud.get_tools_by_tool_type(tool.id)
                            count_elements = 0
                            links = tools_has_device_crud.get_tools_by_device_id(
                                device.id)
                            for __tool in tools:
                                if __tool.id in links:
                                    continue
                                count_elements += 1
                            if count_elements == 0:
                                continue

                            key = str(k)
                            tool_info = f"{tool.name} {tool.description}"
                            values_dict[key] = {
                                "tools": tool_info,
                                "sum": str(count_elements)
                            }

                        subgroup_dict[str(current_key + j)] = {
                            "SGName": subgroup.name,
                            "value": values_dict
                        }

            result["groups"][str(i)] = {
                "name": group.name,
                "subgroup": subgroup_dict
            }

        return result

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка формирования JSON: {e}"
        )

@all_tools_router.get(
    "/get_tool_types_from_db",
    response_model=AllToolTypesResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка формирования JSON"}}
)
def get_tool_types_from_db(device_number: int, db: Session = Depends(get_db)):
    try:
        devices_crud = EngineDevice()
        tools_has_device_crud = EngineToolsHasDevice()
        tools_crud = EngineTools()
        tool_type_crud = EngineToolTypes()
        e_group = EngineGroup()

        tool_types = tool_type_crud.get_all_tool_types()

        tool_dict = {}
        for i, tool_type in enumerate(tool_types):

            tool_dict[tool_type.id] = {
                'id': tool_type.id,
                'name': tool_type.name,
                'description': tool_type.description,
                'count': tool_type.count,
                'amount': 1,
            }
        result = {"tools": tool_dict}

        return result

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка формирования JSON: {e}"
        )


@all_tools_router.get("/tools_controls")
async def get_tools_status(db: Session = Depends(get_db)):
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
