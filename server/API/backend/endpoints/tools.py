from fastapi import status
# from typing import Dict
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.ToolLocationCRUD import EngineToolLocation
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.GroupCRUD import EngineGroup
# from DB.Data.db_depends import get_db
from DB.session import get_db

tools_router = APIRouter(tags=["Tools"])

@tools_router.get("/tools/{device_number}", response_model=dict)
def get_tools(device_number: int, db: Session = Depends(get_db)):
    # Инициализация CRUD
    device_crud = EngineDevice()
    tools_crud = EngineTools()
    plan_crud = EnginePlan()
    group_crud = EngineGroup()

    # 1. Получение устройства по серийному номеру
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # 2. Получение инструментов для drop и load
    drop_tools = tools_crud.get_tools_for_drop(device.id)
    load_tools = tools_crud.get_tools_for_load(device.id)

    # 3. Структуризация данных
    def structure_tools(tools_list):
        plans = defaultdict(lambda: {"groups": defaultdict(lambda: {"value": []})})
        for tool in tools_list:
            plan = plan_crud.get_plan_by_id(tool.plan_id)
            group = group_crud.get_group_by_id(tool.groups_id)
            if not plan or not group:
                continue  # Пропуск инструментов с отсутствующими связями

            # Группировка по планам и группам
            plan_dict = plans[plan.id]
            plan_dict["name"] = plan.name
            group_dict = plan_dict["groups"][group.id]
            group_dict["name"] = group.name

            # Подсчёт количества инструментов
            existing = next(
                (item for item in group_dict["value"] if item["tools"] == tool.name),
                None
            )
            if existing:
                existing["sum"] = str(int(existing["sum"]) + 1)
            else:
                group_dict["value"].append({"tools": tool.name, "sum": "1"})

        # Преобразование в требуемый формат
        return {
            "plans": {
                str(plan_id): {
                    "name": data["name"],
                    "groups": {
                        str(group_id): {
                            "name": group_data["name"],
                            "value": {
                                str(i): item for i, item in enumerate(group_data["value"])
                            }
                        } for group_id, group_data in data["groups"].items()
                    }
                } for plan_id, data in plans.items()
            }
        }

    # Формирование финального ответа
    return {
        "load": structure_tools(load_tools),
        "drop": structure_tools(drop_tools)
    }

@tools_router.post("/tools/{device_number}", status_code=status.HTTP_201_CREATED)
def link_tool_to_device(
    device_number: int,
    tool_id: int,
    db: Session = Depends(get_db)
):
    """Связывает инструмент с устройством (операция DROP)"""
    device_crud = EngineDevice()
    tools_crud = EngineTools()
    tools_has_device_crud = EngineToolsHasDevice()
    tool_location_crud = EngineToolLocation()

    # Проверка существования устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(404, "Устройство не найдено")

    # Проверка существования инструмента
    tool = tools_crud.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(404, "Инструмент не найден")

    # Проверка, что инструмент не связан с другим устройством
    existing_link = tools_has_device_crud.get_link(tool_id, device.id)
    if existing_link:
        raise HTTPException(409, "Инструмент уже связан с устройством")

    # Создание связи
    tools_has_device_crud.create_link(tool_id, device.id)

    # Обновление статуса инструмента (2 - "в автомате")
    tool_location_crud.update_status(tool_id, status_id=2)

    return {"status": "success", "detail": "Инструмент успешно связан с устройством"}

@tools_router.put("/tools/{device_number}/{tool_id}")
def update_tool(
    device_number: int,
    tool_id: int,
    tool_data: dict,  # Заменить на конкретную Pydantic-модель при необходимости
    db: Session = Depends(get_db)
):
    """Обновляет данные инструмента и его статус"""
    device_crud = EngineDevice()
    tools_crud = EngineTools()
    tool_location_crud = EngineToolLocation()

    # Проверка устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(404, "Устройство не найдено")

    # Проверка связи инструмента с устройством
    link = tools_crud.get_link(tool_id, device.id)
    if not link:
        raise HTTPException(403, "Инструмент не связан с устройством")

    # Обновление данных инструмента
    updated_tool = tools_crud.update_tool_from_data(tool_id, tool_data)
    if not updated_tool:
        raise HTTPException(404, "Инструмент не найден")

    # Обновление статуса (если передан)
    if "status_id" in tool_data:
        tool_location_crud.update_status(tool_id, tool_data["status_id"])

    return {"status": "success", "data": updated_tool}

@tools_router.delete("/tools/{device_number}/{tool_id}")
def unlink_tool_from_device(
    device_number: int,
    tool_id: int,
    db: Session = Depends(get_db)
):
    """Удаляет связь инструмента с устройством (операция LOAD)"""
    device_crud = EngineDevice()
    tools_crud = EngineTools()
    tools_has_device_crud = EngineToolsHasDevice()
    tool_location_crud = EngineToolLocation()

    # Проверка устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(404, "Устройство не найдено")

    # Проверка связи
    link = tools_has_device_crud.get_link(tool_id, device.id)
    if not link:
        raise HTTPException(404, "Связь не найдена")

    # Удаление связи
    tools_has_device_crud.delete_link(tool_id, device.id)

    # Обновление статуса (1 - "на складе")
    tool_location_crud.update_status(tool_id, status_id=1)

    return {"status": "success", "detail": "Связь успешно удалена"}