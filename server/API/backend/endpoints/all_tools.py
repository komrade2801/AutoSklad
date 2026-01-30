import traceback

from Core.app_logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, status

logger = get_logger(__name__)
from sqlalchemy.orm import Session
from typing import Dict, Any

# InventoryResponse,
from API.backend.request_models import ToolsCreate, ToolsAddResponse, AllGroupsResponse, AllToolTypesResponse
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.DropOperationsCRUD import EngineDropOperations
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations

# from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.LoadCRUD import EngineLoad
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


# # , response_model=InventoryResponse
# @all_tools_router.get("/")
# def get_inventory(db: Session = Depends(get_db)):
#     """
#     Получает информацию для экрана "упрinventoryавление запасами".
#     Метод:
#       1. Получает список инструментов с информацией о наличии (stock, machine, in_use) через EngineTools.
#       2. Для каждого инструмента определяет группу (через groups_id и EngineGroup).
#       3. Группирует данные по названиям групп и формирует JSON-ответ, соответствующий примеру из js файла.
#     """
#     tools_crud = EngineTools()
#     group_crud = EngineGroup()
#
#     # Предположим, что метод get_inventory() возвращает список объектов с полями:
#     # id, name, groups_id, stock, machine, in_use
#     inventory_tools = tools_crud.get_inventory()
#     if not inventory_tools:
#         raise HTTPException(status_code=404, detail="Инструменты не найдены")
#
#     # Группируем инструменты по группам
#     inventory_by_group: Dict[str, list] = {}
#     for tool in inventory_tools:
#         group = group_crud.get_group_by_id(tool.groups_id)
#         group_name = group.name if group else "Unknown"
#         if group_name not in inventory_by_group:
#             inventory_by_group[group_name] = []
#         inventory_by_group[group_name].append({
#             "id": tool.id,
#             "barcode": tool.barcode,
#             "name": tool.name,
#             "description": tool.description,
#             "img": tool.img,
#             "plan_id": tool.plan_id,
#             "groups_id": tool.groups_id,
#         })
#
#     # Формируем финальный JSON в виде: { "groups": { "0": { "name": "...", "value": { "0": {..}, ... } }, ... } }
#     groups_output: Dict[str, Any] = {}
#     for idx, (group_name, tools_list) in enumerate(inventory_by_group.items()):
#         # Преобразуем список инструментов в объект с ключами-индексами
#         tools_obj = {str(j): tool for j, tool in enumerate(tools_list)}
#         groups_output[str(idx)] = {
#             "name": group_name,
#             "value": tools_obj
#         }
#
#     return {"groups": groups_output}


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
        # tools_crud = EngineTools()
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

        # Если передан tool_type_id, обновляем существующий инструмент
        if data.tool_type_id and data.tool_type_id > 0:
            logger.debug("[create_tools] Режим обновления инструмента с ID: %s", data.tool_type_id)
            existing_tool = tool_type_crud.get_tool_type_by_id(data.tool_type_id)
            if not existing_tool:
                logger.error("[create_tools] Инструмент для обновления с ID %s не найден", data.tool_type_id)
                raise HTTPException(
                    status_code=404, detail="Инструмент для обновления не найден")
            
            # Проверяем, изменились ли данные (избегаем лишних команд синхронизации)
            has_changes = (
                existing_tool.name != data.tool_name or
                existing_tool.description != data.description or
                existing_tool.count != data.count or
                existing_tool.img != data.img or
                existing_tool.groups_id != data.group_id
            )
            
            if not has_changes:
                logger.debug("[create_tools] Данные не изменились, пропускаем UPDATE")
                return ToolsAddResponse(status=200, message="Инструмент не изменился")
            
            # Обновляем инструмент (декоратор @sync_aware создаст команду синхронизации)
            logger.debug("[create_tools] Обновление инструмента: name=%s, description=%s, count=%s, groups_id=%s",
                         data.tool_name, data.description, data.count, data.group_id)
            success = tool_type_crud.update_tool_type(
                id=data.tool_type_id,
                name=data.tool_name,
                description=data.description,
                count=data.count,
                img=data.img,
                groups_id=data.group_id,
            )
            if not success:
                logger.error("[create_tools] Не удалось обновить инструмент с ID %s", data.tool_type_id)
                raise HTTPException(
                    status_code=400, detail="Не удалось обновить инструмент")
            
            # Очищаем кеш ПОСЛЕ успешного обновления
            tool_type_crud._cache.clear()
            logger.info("[create_tools] Инструмент успешно обновлен")
            return ToolsAddResponse(status=200, message="Инструмент успешно обновлен")
        else:
            # Создаём новый инструмент
            existing_tool = tool_type_crud.find_tool_types_by_name(name=data.tool_name)
            logger.debug("[create_tools] Поиск существующего инструмента с именем '%s': %s", data.tool_name, existing_tool)
            if not existing_tool:
                # Создать новый тип инструмента (декоратор @sync_aware создаст команду синхронизации)
                new_tt_id = max(tool_type_crud.get_all_ids(), default=0) + 1
                logger.debug("[create_tools] Создание нового инструмента с ID %s", new_tt_id)
                tool_type_crud.add_tool_type(
                    tool_type_id=new_tt_id,
                    name=data.tool_name,
                    description=data.description,
                    count=data.count,
                    img=data.img,
                    groups_id=data.group_id,
                )
                logger.info("[create_tools] Инструмент %s успешно создан", new_tt_id)
            else:
                # Инструмент существует - увеличиваем count (декоратор @sync_aware создаст команду UPDATE)
                tool_type = existing_tool[0]
                logger.debug("[create_tools] Инструмент существует (ID %s), увеличиваем count: %s + %s",
                             tool_type.id, tool_type.count, data.count)
                tool_type_crud.update_tool_type(
                    id=tool_type.id,
                    name=tool_type.name,
                    description=tool_type.description,
                    count=tool_type.count + data.count,
                    img=tool_type.img,
                    groups_id=tool_type.groups_id,
                )
                logger.debug("[create_tools] Count обновлен для инструмента %s", tool_type.id)
            
            # Очищаем кеш ПОСЛЕ успешной операции
            tool_type_crud._cache.clear()

        # # 4. Добавить каждую единицу инвентаря
        # for inv in data.tools.values():
        #     tool_id = max(tools_crud.get_all_ids(), default=0) + 1
        #     tools_crud.add_tool(
        #         tool_id=tool_id,
        #         inventory_number=inv,
        #         plan_id=None,
        #         tool_type_id=new_tt_id,
        #         name=data.tool_name,
        #         description=data.description,
        #         count=data.count,
        #         img=data.img,
        #         groups_id=data.group_id,
        #     )

        return ToolsAddResponse(status=200, message="Инструменты успешно добавлены")

    except HTTPException:
        # Пробрасываем HTTP ошибки дальше
        raise
    except Exception as error:
        logger.exception("create_tools: %s", error)
        # Общая ошибка — возвращаем 400 с сообщением
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении инструментов: {error}"
        )


@all_tools_router.get(
    "/get_groups_from_db",
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка формирования JSON"}}
)
def get_groups_from_db(device_number: int, db: Session = Depends(get_db)):
    logger.debug("get_groups_from_db")
    try:
        # devices_crud = EngineDevice()
        # tools_has_device_crud = EngineToolsHasDevice()
        # tools_crud = EngineTools()
        tool_type_crud = EngineToolTypes()
        e_group = EngineGroup()
        e_load = EngineLoad()

        # device = devices_crud.get_device_by_number(device_number)

        all_tool_types = tool_type_crud.get_all_tool_types()

        tool_list = []
        group_list = []
        group_set = set()
        idx = 0
        for tool in all_tool_types:
            logger.debug("tool: %s", tool)
            count = tool.count
            # Вычитаем занятые инструменты (зарезервированные в massload, загруженные в vending, или потребленные)
            # Логика соответствует mass_load.py: export_tools
            loads = e_load.find_by_tools_id(tool.id)
            if loads:
                count -= len(loads)
            if count <= 0:
                count = '-'
            # # Compute sum of free tools
            # tools = tools_crud.get_tools_by_tool_type(tool.id)
            # count_elements = 0
            # links = tools_has_device_crud.get_tools_by_device_id(device.id)
            # for __tool in tools:
            #     if __tool.id in links:
            #         continue
            #     count_elements += 1
            # if count_elements == 0:
            #     continue

            # Get immediate group
            immediate_group_obj = e_group.get_group_by_id(tool.groups_id)
            immediate_group = immediate_group_obj.name if immediate_group_obj else "Unknown"

            # Get parent group
            parent_group = "-"
            full_path = immediate_group
            if immediate_group_obj and immediate_group_obj.paren_group_id and immediate_group_obj.paren_group_id != 0:
                parent_group_obj = e_group.get_group_by_id(immediate_group_obj.paren_group_id)
                parent_group = parent_group_obj.name if parent_group_obj else "-"

                cur_parent_group_id = parent_group_obj.id if parent_group_obj else 0
                while cur_parent_group_id != 0:
                    cur_parent_group = e_group.get_group_by_id(cur_parent_group_id)
                    cur_parent_group_id = cur_parent_group.paren_group_id if cur_parent_group else 0
                    full_path = cur_parent_group.name + "/" + full_path


            tool_list.append({
                "id": tool.id,
                "group": immediate_group,
                "name": tool.name,
                "description": tool.description,
                "sum": count
            })
            if immediate_group_obj and immediate_group_obj.id not in group_set:
                group_list.append({
                    "id": immediate_group_obj.id,
                    "group": immediate_group,
                    "parent_group": parent_group,
                    "description": immediate_group_obj.description,
                    "full": full_path
                })
                group_set.add(immediate_group_obj.id)
            idx += 1

        # Добавляем все группы без инструментов
        all_groups = e_group.get_all_groups()
        for group in all_groups:
            if group.id not in group_set:
                # Построение полного пути для группы (логика аналогична обработке групп из инструментов)
                parent_group = "-"
                full_path = group.name if group.name else "Unknown"
                
                if group.paren_group_id and group.paren_group_id != 0:
                    parent_group_obj = e_group.get_group_by_id(group.paren_group_id)
                    parent_group = parent_group_obj.name if parent_group_obj else "-"
                    
                    cur_parent_group_id = parent_group_obj.id if parent_group_obj else 0
                    while cur_parent_group_id != 0:
                        cur_parent_group = e_group.get_group_by_id(cur_parent_group_id)
                        cur_parent_group_id = cur_parent_group.paren_group_id if cur_parent_group else 0
                        if cur_parent_group:
                            full_path = cur_parent_group.name + "/" + full_path
                
                group_list.append({
                    "id": group.id,
                    "group": group.name if group.name else "Unknown",
                    "parent_group": parent_group,
                    "description": group.description if group.description else "",
                    "full": full_path
                })
                group_set.add(group.id)

        return {"tools": tool_list, "groups": group_list}

    except Exception as e:
        logger.exception("")
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
        # devices_crud = EngineDevice()
        # tools_has_device_crud = EngineToolsHasDevice()
        # tools_crud = EngineTools()
        tool_type_crud = EngineToolTypes()
        # e_group = EngineGroup()

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
        logger.exception("")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка формирования JSON: {e}"
        )


# @all_tools_router.get("/tools_controls")
# async def get_tools_status(db: Session = Depends(get_db)):
#     e_load_operations = EngineLoadOperations()
#     e_drop_operations = EngineDropOperations()
#     e_consumption_operations = EngineOperationsConsumption()
#     tool_types_crud = EngineToolTypes()
#     tools_crud = EngineTools()
#
#     # 1. Получить все типы инструментов
#     tool_types = tool_types_crud.get_all_tool_types()
#
#     result = {"groups": {}}
#
#     for tool_type in tool_types:
#         # 2. Инициализация счетчиков
#         current_stock = tool_type.count
#         machine = 0
#         in_use = 0
#         tools = tools_crud.get_tools_by_tool_type(tool_type.id)
#         loads = []
#         drops = []
#         consumptions = []
#         # 3. Получить все операции для типа
#         for tool in tools:
#             loads.append(e_load_operations.get_operations_by_tool(tool.id))
#             drops.append(e_drop_operations.get_operations_by_tool(tool.id))
#             consumptions.append(
#                 e_consumption_operations.get_operations_by_tool(tool_type.id))
#
#         # 4. Обработка операций
#         all_ops = sorted(
#             loads + drops + consumptions,
#             key=lambda x: x.date
#         )
#
#         for op in all_ops:
#             if isinstance(op, LoadOperations):
#                 current_stock += 1
#             elif isinstance(op, DropOperations):
#                 if current_stock > 0:
#                     current_stock -= 1
#                     machine += 1
#             elif isinstance(op, OperationsConsumption):
#                 if machine > 0:
#                     machine -= 1
#                     in_use += 1
#
#         # 5. Добавить в результат
#         group_key = str(tool_type.group_id)  # Предполагается связь с Group
#         if group_key not in result["groups"]:
#             result["groups"][group_key] = {
#                 "name": tool_type.group.name,
#                 "value": {}
#             }
#
#         tool_entry = {
#             "tools": tool_type.name,
#             "stock": current_stock,
#             "machine": machine,
#             "in_use": in_use
#         }
#         result["groups"][group_key]["value"][str(tool_type.id)] = tool_entry
#
#     return result


@all_tools_router.get(
    "/get_tool_type_by_id/{tool_type_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Инструмент не найден"}}
)
def get_tool_type_by_id(tool_type_id: int, db: Session = Depends(get_db)):
    """
    Получает информацию об инструменте по его ID.
    """
    try:
        tool_type_crud = EngineToolTypes()
        tool_type = tool_type_crud.get_tool_type_by_id(tool_type_id)
        
        if not tool_type:
            raise HTTPException(
                status_code=404, 
                detail="Инструмент не найден"
            )
        
        return {
            "id": tool_type.id,
            "name": tool_type.name,
            "description": tool_type.description if tool_type.description else "",
            "count": tool_type.count,
            "group_id": tool_type.groups_id if tool_type.groups_id else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка получения инструмента: {e}"
        )


@all_tools_router.get(
    "/check_tool_busy/{tool_type_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Инструмент не найден"}}
)
def check_tool_busy(tool_type_id: int, db: Session = Depends(get_db)):
    """
    Проверяет, занят ли инструмент (есть ли у него записи в Load, DropOperations или OperationsConsumption).
    Возвращает True, если инструмент занят (есть в massload/loaded/consumed).
    """
    try:
        tool_type_crud = EngineToolTypes()
        e_load = EngineLoad()
        e_drop_operations = EngineDropOperations()
        e_consumption_operations = EngineOperationsConsumption()
        
        tool_type = tool_type_crud.get_tool_type_by_id(tool_type_id)
        if not tool_type:
            raise HTTPException(
                status_code=404, 
                detail="Инструмент не найден"
            )
        
        # Проверяем Load (массовая загрузка)
        loads = e_load.find_by_tools_id(tool_type_id)
        if loads:
            return {"is_busy": True, "message": "Инструмент используется в массовой загрузке"}
        
        # Проверяем DropOperations (выгрузка - инструмент загружен в вендинг)
        drop_operations = e_drop_operations.get_operations_by_tool(tool_type_id)
        if drop_operations:
            return {"is_busy": True, "message": "Инструмент загружен в вендинг"}
        
        # Проверяем OperationsConsumption (выдача - инструмент выдан в вендинге)
        consumption_operations = e_consumption_operations.get_operations_by_tool(tool_type_id)
        if consumption_operations:
            return {"is_busy": True, "message": "Инструмент выдан в вендинге"}
        
        return {"is_busy": False, "message": "Инструмент свободен"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка проверки инструмента: {e}"
        )


@all_tools_router.delete(
    "/delete_tool_type/{tool_type_id}",
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Инструмент занят или ошибка удаления"}, 404: {"description": "Инструмент не найден"}}
)
def delete_tool_type(tool_type_id: int, db: Session = Depends(get_db)):
    """
    Удаляет инструмент, если он свободен (нет записей в Load, DropOperations или OperationsConsumption).
    
    ВАЖНО: Использует обычные CRUD методы с декоратором @sync_aware для автоматической синхронизации.
    """
    try:
        tool_type_crud = EngineToolTypes()
        e_load = EngineLoad()
        e_drop_operations = EngineDropOperations()
        e_consumption_operations = EngineOperationsConsumption()
        
        # Проверяем существование инструмента
        tool_type = tool_type_crud.get_tool_type_by_id(tool_type_id)
        if not tool_type:
            raise HTTPException(
                status_code=404, 
                detail="Инструмент не найден"
            )
        
        # Проверяем занятость инструмента
        loads = e_load.find_by_tools_id(tool_type_id)
        if loads:
            raise HTTPException(
                status_code=400,
                detail=f"Данный инструмент используется в массовой загрузке.\nУдалить можно только свободный инструмент."
            )
        
        drop_operations = e_drop_operations.get_operations_by_tool(tool_type_id)
        if drop_operations:
            raise HTTPException(
                status_code=400,
                detail="Данный инструмент загружен в вендинг.\nУдалить можно только свободный инструмент."
            )
        
        consumption_operations = e_consumption_operations.get_operations_by_tool(tool_type_id)
        if consumption_operations:
            raise HTTPException(
                status_code=400,
                detail=f"Данный инструмент выдан в вендинге.\nУдалить можно только свободный инструмент."
            )
        
        # Выполняем удаление
        # Декоратор @sync_aware автоматически создаст команду синхронизации DELETE
        logger.debug("[delete_tool_type] Удаление инструмента %s...", tool_type_id)
        success = tool_type_crud.delete_tool_type(tool_type_id)
        
        if success:
            logger.info("[delete_tool_type] Инструмент %s успешно удален из БД", tool_type_id)
            
            # Очищаем кеш ПОСЛЕ успешного удаления (чтобы синхронизация успела отработать)
            tool_type_crud._cache.clear()
            
            # Проверка удаления (для диагностики)
            tool_type_after = tool_type_crud.get_tool_type_by_id(tool_type_id)
            if tool_type_after:
                logger.warning("[delete_tool_type] Инструмент %s все еще существует после удаления!", tool_type_id)
            else:
                logger.debug("[delete_tool_type] Подтверждено: инструмент %s удален из БД", tool_type_id)
        else:
            logger.error("[delete_tool_type] delete_tool_type вернул False для %s", tool_type_id)
            raise HTTPException(
                status_code=400,
                detail="Не удалось удалить инструмент"
            )
        
        return {
            "status": 200,
            "message": "Инструмент успешно удален"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка удаления инструмента: {e}"
        )
