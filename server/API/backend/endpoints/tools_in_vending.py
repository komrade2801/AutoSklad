from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
# , List
from API.backend.request_models import ToolsInVendingUpdate, PlanRequest
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice

tools_in_vending_router = APIRouter(tags=["Tools in vending"])


def get_and_validate_device(device_number: int, db: Session):
    device_crud = EngineDevice()
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return device


def check_plan_belongs_to_device(plan_id: int, device_id: int, db: Session):
    tools_has_device_crud = EngineToolsHasDevice()
    tools_crud = EngineTools()

    # Получаем все инструменты устройства
    tool_ids = tools_has_device_crud.get_tools_by_device_id(device_id)
    tools = tools_crud.get_tools_by_ids(tool_ids)

    # Проверяем принадлежность плана
    for tool in tools:
        if tool.plan_id == plan_id:
            return True
    return False


@tools_in_vending_router.get("/tools-in-vending/{device_number}", response_model=Dict[str, Any])
def get_tools_in_vending(device_number: int, db: Session = Depends(get_db)):
    device = get_and_validate_device(device_number, db)

    # Получаем инструменты устройства
    tools_has_device_crud = EngineToolsHasDevice()
    tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)

    if not tool_ids:
        raise HTTPException(status_code=404, detail="Нет инструментов для данного устройства")

    tools_crud = EngineTools()
    tools = tools_crud.get_tools_by_ids(tool_ids)

    plan_crud = EnginePlan()
    group_crud = EngineGroup()
    cell_crud = EngineCell()

    result = {"plans": {}}

    # Собираем уникальные планы
    plan_ids = {tool.plan_id for tool in tools if tool.plan_id is not None}
    if not plan_ids:
        raise HTTPException(status_code=404, detail="Планы не найдены")

    all_plans = plan_crud.get_plans_by_ids(plan_ids)

    for plan_idx, plan in enumerate(all_plans):
        # Фильтруем инструменты текущего плана
        plan_tools = [t for t in tools if t.plan_id == plan.id]

        groups_dict = {}
        for tool in plan_tools:
            group = group_crud.get_group_by_id(tool.groups_id) if tool.groups_id else None
            group_name = group.name if group else "Без группы"

            cell = cell_crud.get_cell_by_tool_id(tool.id)
            cell_number = str(cell.number) if cell else "N/A"

            if group_name not in groups_dict:
                groups_dict[group_name] = {
                    "name": group_name,
                    "value": {}
                }

            group_data = groups_dict[group_name]
            tool_idx = len(group_data["value"])
            group_data["value"][str(tool_idx)] = {
                "tools": tool.name,
                "cell": cell_number
            }

        formatted_groups = {}
        for group_idx, (_, group) in enumerate(groups_dict.items()):
            formatted_groups[str(group_idx)] = group

        result["plans"][str(plan_idx)] = {
            "name": plan.name,
            "groups": formatted_groups
        }

    return result


@tools_in_vending_router.post("/tools-in-vending/{device_number}", response_model=Dict[str, Any])
def create_tools_structure(
        device_number: int,
        data: ToolsInVendingUpdate,
        db: Session = Depends(get_db)
):
    device = get_and_validate_device(device_number, db)
    tools_has_device_crud = EngineToolsHasDevice()

    try:
        db.begin()
        plan_crud = EnginePlan()
        group_crud = EngineGroup()
        tools_crud = EngineTools()
        cell_crud = EngineCell()

        result = {"plans": {}}

        for plan_key, plan_data in data.plans.items():
            new_plan = plan_crud.create_plan(name=plan_data.name)

            groups_dict = {}
            for group in plan_data.groups:
                new_group = group_crud.create_group(
                    name=group.name,
                    description=f"Группа для {plan_data.name}"
                )

                tools_list = []
                for tool in group.tools:
                    new_tool = tools_crud.create_tool(
                        name=tool.tools,
                        plan_id=new_plan.id,
                        groups_id=new_group.id
                    )

                    # Привязка инструмента к устройству
                    tools_has_device_crud.link_tool_to_device(
                        tool_id=new_tool.id,
                        device_id=device.id
                    )

                    cell = cell_crud.get_cell_by_number(tool.cell)
                    if not cell:
                        cell = cell_crud.create_cell(
                            number=tool.cell,
                            description=f"Ячейка для {tool.tools}"
                        )

                    tools_crud.link_tool_to_cell(new_tool.id, cell.id)
                    tools_list.append({
                        "tools": new_tool.name,
                        "cell": str(cell.number)
                    })

                groups_dict[str(new_group.id)] = {
                    "name": new_group.name,
                    "value": {str(i): t for i, t in enumerate(tools_list)}
                }

            result["plans"][plan_key] = {
                "name": new_plan.name,
                "groups": groups_dict
            }

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@tools_in_vending_router.put("/tools-in-vending/{device_number}/{plan_id}", response_model=Dict[str, Any])
def update_tools_structure(
        device_number: int,
        plan_id: int,
        data: PlanRequest,
        db: Session = Depends(get_db)
):
    device = get_and_validate_device(device_number, db)

    if not check_plan_belongs_to_device(plan_id, device.id, db):
        raise HTTPException(status_code=403, detail="План не принадлежит устройству")

    try:
        db.begin()
        plan_crud = EnginePlan()
        group_crud = EngineGroup()
        tools_crud = EngineTools()
        cell_crud = EngineCell()
        tools_has_device_crud = EngineToolsHasDevice()

        plan = plan_crud.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        updated_plan = plan_crud.update_plan_by_name(plan_id, {"name": data.name})

        # Удаляем старые данные
        for group in plan.groups:
            for tool in group.tools:
                tools_has_device_crud.unlink_tool_from_device(tool.id, device.id)
                tools_crud.delete_tool(tool.id)
            group_crud.delete_group(group.id)

        # Создаем новые данные
        groups_dict = {}
        for group in data.groups:
            new_group = group_crud.create_group(
                name=group.name,
                description=f"Обновленная группа для {data.name}"
            )

            tools_list = []
            for tool in group.tools:
                new_tool = tools_crud.create_tool(
                    name=tool.tools,
                    plan_id=plan_id,
                    groups_id=new_group.id
                )

                tools_has_device_crud.link_tool_to_device(
                    tool_id=new_tool.id,
                    device_id=device.id
                )

                cell = cell_crud.get_cell_by_number(tool.cell)
                if not cell:
                    cell = cell_crud.create_cell(number=tool.cell, description="")

                tools_crud.link_tool_to_cell(new_tool.id, cell.id)
                tools_list.append({"tools": new_tool.name, "cell": tool.cell})

            groups_dict[str(new_group.id)] = {
                "name": new_group.name,
                "value": {str(i): t for i, t in enumerate(tools_list)}
            }

        db.commit()
        return {
            "name": updated_plan.name,
            "groups": groups_dict
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@tools_in_vending_router.delete("/tools-in-vending/{device_number}/{plan_id}")
def delete_plan_structure(
        device_number: int,
        plan_id: int,
        db: Session = Depends(get_db)
):
    device = get_and_validate_device(device_number, db)

    if not check_plan_belongs_to_device(plan_id, device.id, db):
        raise HTTPException(status_code=403, detail="План не принадлежит устройству")

    try:
        db.begin()
        plan_crud = EnginePlan()
        group_crud = EngineGroup()
        tools_crud = EngineTools()
        tools_has_device_crud = EngineToolsHasDevice()

        plan = plan_crud.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        # Удаляем связи
        for group in plan.groups:
            for tool in group.tools:
                tools_has_device_crud.unlink_tool_from_device(tool.id, device.id)
                tools_crud.unlink_tool_from_cell(tool.id)
                tools_crud.delete_tool(tool.id)
            group_crud.delete_group(group.id)

        plan_crud.delete_plan(plan_id)
        db.commit()
        return {"message": f"Plan {plan_id} и связанные данные удалены"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))