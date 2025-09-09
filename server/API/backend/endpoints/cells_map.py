from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
# , List
from API.backend.request_models import CellsResponse, Cell, CellCreate, CellUpdate  # Pydantic-модели для ячеек
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.PlanCRUD import EnginePlan

cells_map_router = APIRouter(tags=["Cells Map"])


@cells_map_router.get("/cells/{device_number}", response_model=CellsResponse)
def get_cells(device_number: int, db: Session = Depends(get_db)):
    """
    Получает данные для экрана 'управление ячейками' по серийному номеру устройства.
    Алгоритм:
      1. Находим устройство по device_number.
      2. Из таблицы Cell_has_Device получаем ячейки, связанные с устройством.
      3. Для каждой ячейки через EngineCell получаем основные данные.
      4. По tools_id ячейки получаем инструмент, затем группу (через EngineGroup) и план (через EnginePlan).
      5. Формируем объект ячейки с полями id, type, backgroundColor, content (с полями tool, groupIndex, groupName, plan) и block.
      6. Группируем ячейки в строки (например, по 4 ячейки на строку) и возвращаем итоговый JSON.
    """
    devices_crud = EngineDevice()
    cell_has_device_crud = EngineCellHasDevice()
    cell_crud = EngineCell()
    tools_crud = EngineTools()
    group_crud = EngineGroup()
    plan_crud = EnginePlan()

    # 1. Находим устройство
    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # 2. Получаем ID ячеек, связанных с устройством
    cell_ids = cell_has_device_crud.get_cells_by_device_id(device.id)
    if not cell_ids:
        raise HTTPException(status_code=404, detail="Ячейки для данного устройства не найдены")

    # 3. Получаем данные ячеек
    cells = cell_crud.get_cells_by_ids(cell_ids)
    if not cells:
        raise HTTPException(status_code=404, detail="Ячейки не найдены")

    # 4. Собираем данные для каждой ячейки
    cell_data_list = []
    for cell in cells:
        # Получаем инструмент для ячейки
        tool = tools_crud.get_tool_by_id(cell.tools_id)
        if not tool:
            continue  # можно пропустить или вернуть ошибку, если данные критичны

        # Получаем группу, связанную с инструментом
        group = group_crud.get_group_by_id(tool.groups_id) if tool.groups_id else None
        group_index = str(group.id) if group else "0"
        group_name = group.name if group else "Unknown"

        # Получаем план, если он есть
        plan = plan_crud.get_plan_by_id(tool.plan_id) if tool.plan_id else None
        plan_str = plan.barcode if plan else "None"

        cell_obj = {
            "id": str(cell.id),
            "type": "small",
            "backgroundColor": "#69696910",
            "content": {
                "tool": tool.name,
                "groupIndex": group_index,
                "groupName": group_name,
                "plan": plan_str
            },
            "block": "false"
        }
        cell_data_list.append(cell_obj)

    # 5. Группируем ячейки в строки (например, по 4 ячейки на строку)
    rows: Dict[str, Dict[str, dict]] = {}
    cells_per_row = 4
    for i, cell_obj in enumerate(cell_data_list):
        row_num = i // cells_per_row + 1
        row_key = str(row_num)
        if row_key not in rows:
            rows[row_key] = {}
        cell_key = str(len(rows[row_key]) + 1)
        rows[row_key][cell_key] = cell_obj

    # Формируем финальный ответ: { "rows": { "1": { "cells": { ... } }, ... } }
    output_rows = {row_key: {"cells": cells_dict} for row_key, cells_dict in rows.items()}

    return {"rows": output_rows}


@cells_map_router.post("/cells/{device_number}", response_model=Cell)
def create_cell(device_number: int, cell_data: CellCreate, db: Session = Depends(get_db), description=""):
    """
    Создает новую ячейку и связывает её с устройством.
    1. Находит устройство по device_number.
    2. Создает новую ячейку через EngineCell.
    3. Создает связь между ячейкой и устройством через таблицу Cell_has_Device.
    """
    devices_crud = EngineDevice()
    cell_crud = EngineCell()
    cell_has_device_crud = EngineCellHasDevice()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    cell_id = max(cell_crud.get_all_ids(), default=0) + 1
    new_cell = cell_crud.create_cell(
        index=cell_id,
        number=cell_data.number,
        tools_id=cell_data.tools_id,
        status_id=cell_data.status_id,
        groups_id=cell_data.groups_id,
        description=cell_data.description,
    )

    if not new_cell:
        raise HTTPException(status_code=400, detail="Не удалось создать ячейку")

    cell_has_device_crud.link_cell_to_device(new_cell.id, device.id)
    return new_cell


@cells_map_router.put("/cells/{device_number}/{cell_id}", response_model=Cell)
def update_cell(device_number: int, cell_id: int, cell_data: CellUpdate, db: Session = Depends(get_db)):
    """
    Обновляет данные ячейки, предварительно проверяя, что ячейка принадлежит данному устройству.
    """
    devices_crud = EngineDevice()
    cell_crud = EngineCell()
    cell_has_device_crud = EngineCellHasDevice()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    if not cell_has_device_crud.check_cell_belongs_to_device(cell_id, device.id):
        raise HTTPException(status_code=403, detail="Ячейка не принадлежит данному устройству")

    updated_cell = cell_crud.update_cell_from_data(cell_id, cell_data)
    if not updated_cell:
        raise HTTPException(status_code=404, detail="Ячейка не найдена")
    return updated_cell


@cells_map_router.delete("/cells/{device_number}/{cell_id}")
def delete_cell(device_number: int, cell_id: int, db: Session = Depends(get_db)):
    """
    Удаляет ячейку, предварительно проверяя, что она принадлежит данному устройству, и удаляет связь в Cell_has_Device.
    """
    devices_crud = EngineDevice()
    cell_crud = EngineCell()
    cell_has_device_crud = EngineCellHasDevice()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    if not cell_has_device_crud.check_cell_belongs_to_device(cell_id, device.id):
        raise HTTPException(status_code=403, detail="Ячейка не принадлежит данному устройству")

    deleted = cell_crud.delete_cell(cell_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ячейка не найдена")

    cell_has_device_crud.unlink_cell_from_device(cell_id, device.id)
    return {"message": "Ячейка успешно удалена"}
