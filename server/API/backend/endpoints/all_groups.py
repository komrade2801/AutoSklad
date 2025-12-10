import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Tuple

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
        print(f"[create_groups] Начало создания группы. Данные: group_name={data.group_name}, parent_group={data.parent_group}, group_id={data.group_id}, description={data.description}")
        group_crud = EngineGroup()

        group_parent_id = 0

        if data.parent_group and data.parent_group > 0:
            group_parent_id = data.parent_group
            print(f"[create_groups] Установлен parent_group_id: {group_parent_id}")

            # Проверка существования родительской группы
            parent_group = group_crud.get_group_by_id(group_parent_id)
            print(f"[create_groups] Родительская группа найдена: {parent_group}")

            if not parent_group:
                print(f"[create_groups] ОШИБКА: Родительская группа с ID {group_parent_id} не найдена")
                raise HTTPException(
                    status_code=400, detail="Не удалось создать или найти группу")

        else:
            group_parent_id = 0
            print(f"[create_groups] Родительская группа не указана, устанавливаем 0")


        if data.group_name:
            # Если передан group_id, обновляем существующую группу
            if data.group_id and data.group_id > 0:
                print(f"[create_groups] Режим обновления группы с ID: {data.group_id}")
                existing_group = group_crud.get_group_by_id(data.group_id)
                if not existing_group:
                    print(f"[create_groups] ОШИБКА: Группа для обновления с ID {data.group_id} не найдена")
                    raise HTTPException(
                        status_code=404, detail="Группа для обновления не найдена")
                
                # Проверяем, изменились ли данные (избегаем лишних команд синхронизации)
                has_changes = (
                    existing_group.name != data.group_name or
                    existing_group.description != data.description or
                    existing_group.paren_group_id != group_parent_id
                )
                
                if not has_changes:
                    print(f"[create_groups] Данные не изменились, пропускаем UPDATE (избегаем лишней синхронизации)")
                    return GroupsAddResponse(status=200, message="Группа не изменилась")
                
                # Обновляем группу (декоратор @sync_aware создаст команду синхронизации)
                print(f"[create_groups] Обновление группы: name={data.group_name}, description={data.description}, paren_group_id={group_parent_id}")
                success = group_crud.update_group(
                    group_id=data.group_id,
                    name=data.group_name,
                    description=data.description,
                    paren_group_id=group_parent_id
                )
                if not success:
                    print(f"[create_groups] ОШИБКА: Не удалось обновить группу с ID {data.group_id}")
                    raise HTTPException(
                        status_code=400, detail="Не удалось обновить группу")
                
                # Очищаем кеш ПОСЛЕ успешного обновления
                group_crud._cache.clear()
                print(f"[create_groups] Группа успешно обновлена")
                return GroupsAddResponse(status=200, message="Группа успешно обновлена")
            else:
                # Создаём новую группу
                print(f"[create_groups] Режим создания новой группы")
                existing_groups = group_crud.find_groups_by_name(name=data.group_name)
                print(f"[create_groups] Поиск существующих групп с именем '{data.group_name}': найдено {len(existing_groups)} групп")
                
                if len(existing_groups) == 0:
                    print(f"[create_groups] Группа с именем '{data.group_name}' не найдена, создаём новую")
                    print(f"[create_groups] Параметры создания: name={data.group_name}, description={data.description}, paren_group_id={group_parent_id}")
                    # Декоратор @sync_aware автоматически создаст команду синхронизации ADD
                    group = group_crud.create_group(
                        name=data.group_name,
                        description=data.description,
                        paren_group_id=group_parent_id
                    )
                    print(f"[create_groups] Результат create_group: {group}")
                    if not group:
                        print(f"[create_groups] ОШИБКА: create_group вернул None. Возможные причины: ошибка при добавлении в БД или генерации ID")
                        raise HTTPException(
                            status_code=400, detail="Не удалось создать группу")
                    
                    # Очищаем кеш ПОСЛЕ успешного создания
                    group_crud._cache.clear()
                    print(f"[create_groups] Группа успешно создана с ID: {group.id}")
                else:
                    print(f"[create_groups] Группа с именем '{data.group_name}' уже существует (ID: {[g.id for g in existing_groups]})")
                    return GroupsAddResponse(status=204, message="Группа уже существует")

        print(f"[create_groups] Успешное завершение")
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


@all_groups_router.get(
    "/get_group_by_id/{group_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Группа не найдена"}}
)
def get_group_by_id(group_id: int, db: Session = Depends(get_db)):
    """
    Получает информацию о группе по её ID.
    """
    try:
        group_crud = EngineGroup()
        group = group_crud.get_group_by_id(group_id)
        
        if not group:
            raise HTTPException(
                status_code=404, 
                detail="Группа не найдена"
            )
        
        return {
            "id": group.id,
            "name": group.name,
            "description": group.description if group.description else "",
            "parent_group": group.paren_group_id if group.paren_group_id else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка получения группы: {e}"
        )


@all_groups_router.get(
    "/check_group_busy/{group_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Группа не найдена"}}
)
def check_group_busy(group_id: int, db: Session = Depends(get_db)):
    """
    Проверяет, занята ли группа (есть ли у неё инструменты в Load).
    Возвращает True, если группа занята (есть инструменты в massload/loaded/consumed).
    """
    try:
        group_crud = EngineGroup()
        tool_type_crud = EngineToolTypes()
        e_load = EngineLoad()
        
        group = group_crud.get_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=404, 
                detail="Группа не найдена"
            )
        
        # Получаем все типы инструментов этой группы
        tool_types = tool_type_crud.get_by_group(group_id)
        
        # Проверяем, есть ли у любого типа инструментов записи в Load
        for tool_type in tool_types:
            loads = e_load.find_by_tools_id(tool_type.id)
            if loads:
                return {"is_busy": True, "message": "Группа содержит занятые инструменты"}
        
        return {"is_busy": False, "message": "Группа свободна"}
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка проверки группы: {e}"
        )


@all_groups_router.delete(
    "/delete_group/{group_id}",
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Группа занята или ошибка удаления"}, 404: {"description": "Группа не найдена"}}
)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """
    Рекурсивно удаляет группу, все вложенные группы и все связанные номенклатуры (ToolTypes), 
    если все группы свободны. Если любая группа занята (есть инструменты в Load), возвращает ошибку.
    
    ВАЖНО: Использует обычные CRUD методы с декоратором @sync_aware для автоматической синхронизации.
    """
    try:
        group_crud = EngineGroup()
        tool_type_crud = EngineToolTypes()
        e_load = EngineLoad()
        
        def get_all_nested_groups(parent_group_id: int) -> List[int]:
            """Рекурсивно получает все ID вложенных групп"""
            all_group_ids = [parent_group_id]
            child_groups = group_crud.get_groups_by_paren_group_id(parent_group_id)
            for child_group in child_groups:
                all_group_ids.extend(get_all_nested_groups(child_group.id))
            return all_group_ids
        
        def check_group_busy_recursive(group_id: int) -> Tuple[bool, str]:
            """Рекурсивно проверяет занятость группы и всех вложенных групп"""
            e_drop_operations = EngineDropOperations()
            e_consumption_operations = EngineOperationsConsumption()
            
            all_group_ids = get_all_nested_groups(group_id)
            
            for gid in all_group_ids:
                tool_types = tool_type_crud.get_by_group(gid)
                for tool_type in tool_types:
                    # Проверяем Load (массовая загрузка)
                    loads = e_load.find_by_tools_id(tool_type.id)
                    if loads:
                        group = group_crud.get_group_by_id(gid)
                        group_name = group.name if group else f"ID {gid}"
                        return True, f"Группа '{group_name}' (ID: {gid}) содержит инструменты в массовой загрузке"
                    
                    # Проверяем DropOperations (загружен в вендинг)
                    drop_operations = e_drop_operations.get_operations_by_tool(tool_type.id)
                    if drop_operations:
                        group = group_crud.get_group_by_id(gid)
                        group_name = group.name if group else f"ID {gid}"
                        return True, f"Группа '{group_name}' (ID: {gid}) содержит инструменты, загруженные в вендинг"
                    
                    # Проверяем OperationsConsumption (выдан в вендинге)
                    consumption_operations = e_consumption_operations.get_operations_by_tool(tool_type.id)
                    if consumption_operations:
                        group = group_crud.get_group_by_id(gid)
                        group_name = group.name if group else f"ID {gid}"
                        return True, f"Группа '{group_name}' (ID: {gid}) содержит инструменты, выданные в вендинге"
            
            return False, ""
        
        def delete_group_recursive(group_id: int) -> Tuple[int, int]:
            """
            Рекурсивно удаляет группу, все вложенные группы и их номенклатуры.
            Использует обычные CRUD методы - декоратор @sync_aware автоматически создаст команды синхронизации.
            """
            deleted_groups_count = 0
            deleted_tool_types_count = 0
            
            all_group_ids = get_all_nested_groups(group_id)
            print(f"[delete_group] Группы для удаления (рекурсивно): {all_group_ids}")
            
            # Удаляем ToolTypes для всех групп (в обратном порядке)
            for gid in reversed(all_group_ids):
                tool_types = tool_type_crud.get_by_group(gid)
                print(f"[delete_group] Удаление номенклатур для группы {gid}: найдено {len(tool_types)}")
                for tool_type in tool_types:
                    # Декоратор @sync_aware автоматически создаст команду синхронизации DELETE
                    print(f"[delete_group] Удаление номенклатуры {tool_type.id} ({tool_type.name})")
                    success = tool_type_crud.delete_tool_type(tool_type.id)
                    if success:
                        deleted_tool_types_count += 1
                        print(f"[delete_group] Номенклатура {tool_type.id} успешно удалена")
                    else:
                        print(f"[delete_group] ОШИБКА: Не удалось удалить номенклатуру {tool_type.id}")
                
                # Очищаем кеш после удаления всех номенклатур группы
                if tool_types:
                    tool_type_crud._cache.clear()
            
            # Удаляем группы (в обратном порядке - сначала дочерние)
            for gid in reversed(all_group_ids):
                group_before = group_crud.get_group_by_id(gid)
                group_name = group_before.name if group_before else f"ID {gid}"
                
                print(f"[delete_group] Попытка удаления группы {gid} ({group_name})")
                # Декоратор @sync_aware автоматически создаст команду синхронизации DELETE
                success = group_crud.delete_group(gid)
                
                if success:
                    deleted_groups_count += 1
                    print(f"[delete_group] Группа {gid} ({group_name}) успешно удалена из БД")
                    
                    # Проверка удаления (для диагностики)
                    group_after = group_crud.get_group_by_id(gid)
                    if group_after:
                        print(f"[delete_group] ВНИМАНИЕ: Группа {gid} все еще существует после удаления!")
                    else:
                        print(f"[delete_group] Подтверждено: группа {gid} удалена из БД")
                else:
                    print(f"[delete_group] ОШИБКА: delete_group вернул False для {gid} ({group_name})")
            
            # Очищаем кеш после удаления всех групп
            if deleted_groups_count > 0:
                group_crud._cache.clear()
            
            return deleted_groups_count, deleted_tool_types_count
        
        # Проверяем существование группы
        group = group_crud.get_group_by_id(group_id)
        if not group:
            raise HTTPException(
                status_code=404, 
                detail="Группа не найдена"
            )
        
        # Рекурсивно проверяем занятость группы и всех вложенных групп
        is_busy, busy_message = check_group_busy_recursive(group_id)
        if is_busy:
            raise HTTPException(
                status_code=400,
                detail=f"Данный инструмент используется в вендинге.\nУдалить можно только свободный инструмент.\n{busy_message}"
            )
        
        # Выполняем рекурсивное удаление
        # Декоратор @sync_aware автоматически создаст команды синхронизации для каждой операции
        # ВАЖНО: Каждая операция DELETE создаст отдельную команду в CommandQueue
        print(f"[delete_group] Начало рекурсивного удаления группы {group_id}...")
        deleted_groups_count, deleted_tool_types_count = delete_group_recursive(group_id)
        print(f"[delete_group] Удаление завершено: групп={deleted_groups_count}, номенклатур={deleted_tool_types_count}")
        
        # Финальная очистка кеша (если еще не очищен)
        group_crud._cache.clear()
        tool_type_crud._cache.clear()
        
        return {
            "status": 200,
            "message": f"Удалено групп: {deleted_groups_count}, номенклатур: {deleted_tool_types_count}"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка удаления группы: {e}"
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
