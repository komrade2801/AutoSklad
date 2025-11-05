from __future__ import annotations

import json
from io import BytesIO
# from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File  # , Body, Form
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import pandas as pd

from API.backend.request_models import (
    ToolLibraryResponse,  # Pydantic-модель для ответа: { "groups": { ... } }
    ToolLibrary,  # Модель инструмента (ответ при создании/обновлении)
    ToolLibraryCreate,  # Модель для создания записи
    ToolLibraryUpdate  # Модель для обновления записи
)
# , DEFAULT_FIELD_MAP
from API.backend.upload.config import update_field_map, load_field_map
from API.backend.upload.mappers import normalize_record  # , ColumnsMapModel

# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from typing import Dict, Optional, Any
from fastapi import Form

tool_library_router = APIRouter(tags=["Tool library"])

# Какие поля обязательны для загрузки
REQUIRED = [
    "tool_types_name"
]


@tool_library_router.post("/upload")
async def upload_xlsx(
        file: UploadFile = File(...),
        columns_map: Optional[str] = Form(
            None, description="JSON‑строка с дополнительным маппингом"),
        db: Session = Depends(get_db)
):
    # 1) Попытаться распарсить columns_map, но не падать, если оно не JSON
    field_map = load_field_map()
    if columns_map:
        try:
            cm_dict = json.loads(columns_map)
            if isinstance(cm_dict, dict):
                update_field_map(cm_dict)
                field_map = load_field_map()
            # иначе — это не dict, игнорируем
        except json.JSONDecodeError:
            # просто пропускаем, не обновляем маппинг
            pass

    # 2) Считываем Excel
    try:
        data = await file.read()
        df = pd.read_excel(BytesIO(data), keep_default_na=False)
        df = df.replace({pd.NA: None})
        records = df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(422, f"Cannot parse Excel: {e}")

    # 3) Инстансы CRUD
    e_group = EngineGroup()
    e_tool_types = EngineToolTypes()
    tools_crud = EngineTools()

    processed = 0
    errors = []
    seen_inv = set()

    tool_type_counts = {}

    last_seen = {k: None for k in field_map.keys()}
    print(f"last_seen {last_seen}")
    # 4) Обрабатываем построчно
    for idx, rec in enumerate(records, start=1):
        print(f"{idx} / {len(records)}")
        try:

            norm, last_seen = normalize_record(
                rec, REQUIRED, field_map, last_seen)
            print(f"norm {norm}")
            inv = norm["tool_inventory_number"]

            if inv and inv in seen_inv:
                raise ValueError(f"Duplicate inventory_number: {inv}")
            seen_inv.add(inv)

            # Group
            grp_id = norm.get("group_id")
            if not grp_id:
                grp = e_group.find(name=norm.get("group_name") or "Default",
                                   description=norm.get("group_description") or "")
                grp_id = grp.id

            # ToolTypes
            tt = e_tool_types.find_by_name(
                name=norm["tool_types_name"],
                # groups_id=grp_id
            )
            print(f"tt {tt}")
            tool_type = None
            if not tt:
                tool_type_id = max(e_tool_types.get_all_ids(), default=0) + 1
                e_tool_types.add_tool_type(
                    tool_type_id=tool_type_id,
                    name=norm["tool_types_name"],
                    description=norm.get("tool_types_description", ""),
                    count=0,
                    img=norm.get("tool_types_img", ""),
                    groups_id=grp_id
                )
                tool_type = e_tool_types.get_tool_type_by_id(tool_type_id)
            else:
                tool_type = tt[0]

            if tool_type.id in tool_type_counts:
                tool_type_counts[tool_type.id] = tool_type_counts[tool_type.id] + 1
            else:
                tool_type_counts[tool_type.id] = 1

            # Tools
            tl = tools_crud.get_by_inventory_number(inv)
            if not tl:
                tool_id = max(tools_crud.get_all_ids(), default=0) + 1
                tools_crud.add_tool(
                    tool_id=tool_id,
                    inventory_number=inv,
                    plan_id=norm.get("tool_plan_id"),
                    tool_type_id=tool_type.id,
                    name=tool_type.name,
                    description=tool_type.description,
                    count=1,
                    img=tool_type.img,
                    groups_id=tool_type.groups_id,
                )
            else:
                # for i in range(0, tool_type.count):
                tool_id = max(tools_crud.get_all_ids(), default=0) + 1
                tools_crud.add_tool(
                    tool_id=tool_id,
                    inventory_number=tool_type.count + tool_type_counts[tool_type.id],
                    plan_id=norm.get("tool_plan_id"),
                    tool_type_id=tool_type.id,
                    name=tool_type.name,
                    description=tool_type.description,
                    count=1,
                    img=tool_type.img,
                    groups_id=tool_type.groups_id,
                )
            processed += 1

        except (ValueError, SQLAlchemyError) as e:
            db.rollback()
            errors.append({"row": idx, "error": str(e)})

            print(e)

    print(f"found tool type counts {tool_type_counts}")
    if tool_type_counts:
        for id, count in tool_type_counts.items():
            tool_type = e_tool_types.get_tool_type_by_id(id)
            print(f"tool_type {tool_type}")

            e_tool_types.update_tool_type(
                id=tool_type.id,
                name=tool_type.name,
                description=tool_type.description,
                count=tool_type.count + count,
                img=tool_type.img,
                groups_id=tool_type.groups_id,
            )

    return {
        "processed": processed,
        "errors": errors,
        "field_map": field_map
    }


# @tool_library_router.post("/upload")
# async def upload_xlsx(file: UploadFile = File(...)):
#     contents = await file.read()
#     if not contents:
#         raise HTTPException(400, "Empty file")
#
#     # try:
#     df = pd.read_excel(BytesIO(contents))
#     # except Exception as e:
#     #     raise HTTPException(422, f"Cannot parse Excel: {e}")
#
#     records = df.to_dict(orient="records")
#     return JSONResponse({
#         "filename": file.filename,
#         "rows": len(records),
#         "sample": records[:5]
#     })


@tool_library_router.get("/tool-library/{device_number}", response_model=ToolLibraryResponse)
def get_tool_library(device_number: int, db: Session = Depends(get_db)):
    """
    Возвращает библиотеку инструментов для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем через Tools_has_Device все инструменты, связанные с устройством.
    3. Для каждого инструмента:
       - Получаем группу (через EngineGroup) по tool.groups_id.
       - Получаем тип инструмента (подгруппу) через EngineToolType по tool.id. Если тип не найден, используем "-".
    4. Группируем инструменты по имени группы, а затем по типу (подгруппе).
    5. Формируем итоговый JSON, где ключами являются числовые индексы, как в примере.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    tools_crud = EngineTools()
    group_crud = EngineGroup()
    # tool_norms_crud = EngineToolsNorm()
    tool_type_crud = EngineToolTypes()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    if not tool_ids:
        raise HTTPException(status_code=404, detail="Инструменты не найдены")

    tools = tools_crud.get_tools_by_ids(tool_ids)
    if not tools:
        raise HTTPException(status_code=404, detail="Инструменты не найдены")

    # Get status for pending mass load
    e_load_operations = EngineLoadOperations()
    e_status = EngineStatus()
    mass_load_init_status = e_status.find_by_name("mass_load_init")
    if not mass_load_init_status:
        mass_load_init_status = None
    else:
        mass_load_init_status = mass_load_init_status.id

    # Группируем: { group_name: { tool_type_name: [tool.name, ...] } }
    grouped: Dict[str, Dict[str, list]] = {}
    for tool in tools:
        # Check if tool has pending mass load operation
        if mass_load_init_status:
            operations = e_load_operations.get_operations_by_tool(tool.id)
            has_pending_load = any(
                op.status_id == mass_load_init_status for op in operations)
            if has_pending_load:
                continue  # Skip tools with pending mass load

        # Получаем группу инструмента
        tool_type = tool_type_crud.get(tool.tool_type_id)
        group = group_crud.get_group_by_id(
            tool_type.groups_id) if tool_type.groups_id else None
        group_name = group.name if group else "Unknown"
        # Получаем тип инструмента (подгруппу)
        # tool_type = tool_type_crud.get_tools_norm_by_tool_id(tool.id)
        sg_name = tool_type.name if tool_type else "-"
        # Группировка
        if group_name not in grouped:
            grouped[group_name] = {}
        if sg_name not in grouped[group_name]:
            grouped[group_name][sg_name] = []
        grouped[group_name][sg_name].append(
            {"description": tool_type.description, "inventory": tool.inventory_number, "id": tool.id})

    # Преобразуем сгруппированные данные в требуемую структуру с числовыми индексами
    groups_output: Dict[str, Any] = {}
    for group_idx, (group_name, subgroups) in enumerate(grouped.items()):
        subgroups_output = {}
        for sg_idx, (sg_name, tool_names) in enumerate(subgroups.items()):
            value_obj = {str(i): name for i, name in enumerate(tool_names)}
            subgroups_output[str(sg_idx)] = {
                "SGName": sg_name,
                "value": value_obj
            }
        groups_output[str(group_idx)] = {
            "name": group_name,
            "subgroup": subgroups_output
        }

    return {"tools": groups_output}


@tool_library_router.post("/tool-library/{device_number}", response_model=ToolLibrary)
def create_tool_library_entry(device_number: int, tool_data: ToolLibraryCreate, db: Session = Depends(get_db)):
    """
    Создает новую запись в библиотеке инструментов для указанного устройства.

    1. Находим устройство по device_number.
    2. Создаем инструмент через EngineTools.
    3. Связываем созданный инструмент с устройством через Tools_has_Device.
    """
    devices_crud = EngineDevice()
    tools_crud = EngineTools()
    tools_has_device_crud = EngineToolsHasDevice()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    new_tool = tools_crud.create_tool(
        index=tool_data.index,
        name=tool_data.name,
        description=tool_data.description,
        img=tool_data.img,
        plan_id=tool_data.img,
        groups_id=tool_data.groups_id,
        inventory_number=tool_data.inventory_number,
    )  # name, plan_id, groups_id
    if not new_tool:
        raise HTTPException(
            status_code=400, detail="Не удалось создать инструмент")

    tools_has_device_crud.link_tool_to_device(new_tool.id, device.id)
    return new_tool


@tool_library_router.put("/tool-library/{device_number}/{tool_id}", response_model=ToolLibrary)
def update_tool_library_entry(device_number: int, tool_id: int, tool_data: ToolLibraryUpdate,
                              db: Session = Depends(get_db)):
    """
    Обновляет запись об инструменте в библиотеке для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что инструмент с tool_id принадлежит данному устройству.
    3. Обновляем данные инструмента.
    """
    devices_crud = EngineDevice()
    tools_crud = EngineTools()
    tools_has_device_crud = EngineToolsHasDevice()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    if not tools_has_device_crud.check_tool_belongs_to_device(tool_id, device.id):
        raise HTTPException(
            status_code=403, detail="Инструмент не принадлежит данному устройству")
    tool = tools_crud.get_tool_by_id(tool_id=tool_id)
    updated_tool = tools_crud.update_tool_from_data(
        tool_id=tool_id,
        data={
            "name": tool_data.name,  #
            "description": tool_data.description,  #
            "img": tool.img,  #
            "plan_id": tool.plan_id,  #
            "groups_id": tool_data.group_id,  #
            "inventory_number": tool.inventory_number,  #
        }
    )
    if not updated_tool:
        raise HTTPException(status_code=404, detail="Инструмент не найден")
    return updated_tool


@tool_library_router.delete("/tool-library/{device_number}/{tool_id}")
def delete_tool_library_entry(device_number: int, tool_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запись об инструменте из библиотеки для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что инструмент принадлежит устройству.
    3. Удаляем запись об инструменте и разрываем связь в Tools_has_Device.
    """
    devices_crud = EngineDevice()
    tools_crud = EngineTools()
    tools_has_device_crud = EngineToolsHasDevice()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    if not tools_has_device_crud.check_tool_belongs_to_device(tool_id, device.id):
        raise HTTPException(
            status_code=403, detail="Инструмент не принадлежит данному устройству")

    deleted = tools_crud.delete_tool(tool_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Инструмент не найден")

    tools_has_device_crud.unlink_tool_from_device(tool_id, device.id)
    return {"message": "Инструмент успешно удален"}
