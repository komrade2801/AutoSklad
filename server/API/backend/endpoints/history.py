from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from API.backend.request_models import HistoryResponse, History, HistoryCreate, HistoryUpdate  # Pydantic-модели для истории
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice

history_router = APIRouter(tags=["History"])

@history_router.get("/history/{device_number}", response_model=HistoryResponse)
def get_history(device_number: int, db: Session = Depends(get_db)):
    """
    Получает историю операций для устройства (по серийному номеру).
    Алгоритм:
      1. Находим устройство по device_number.
      2. Получаем через Tools_has_Device все инструменты данного устройства.
      3. Из History выбираем записи, у которых tools_id входит в найденный набор.
      4. Для каждой записи получаем:
         - ячейку (через EngineCell.get_cell_by_tool_id)
         - группу инструмента (через EngineGroup)
         - план (через EnginePlan).
      5. Формируем итоговый объект с операциями, где ключи — порядковые номера записей.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    history_crud = EngineHistory()
    tools_crud = EngineTools()
    cell_crud = EngineCell()
    group_crud = EngineGroup()
    plan_crud = EnginePlan()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # Получаем все инструменты, связанные с устройством
    tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    if not tool_ids:
        raise HTTPException(status_code=404, detail="Инструменты для данного устройства не найдены")

    # Выбираем записи истории для данных инструментов
    histories = history_crud.get_history_by_tool_ids(tool_ids)
    if not histories:
        raise HTTPException(status_code=404, detail="История не найдена")

    operations: Dict[str, dict] = {}
    for idx, hist in enumerate(histories, start=1):
        tool = tools_crud.get_tool_by_id(hist.tools_id)
        if not tool:
            continue  # пропускаем, если инструмент не найден

        # Получаем ячейку, в которой находится инструмент
        cell = cell_crud.get_cell_by_tool_id(tool.id)
        cell_val = str(cell.number) if cell and hasattr(cell, 'number') else "Unknown"

        group = group_crud.get_group_by_id(tool.groups_id) if tool.groups_id else None
        group_index = str(group.id) if group else "0"
        group_name = group.name if group else "Unknown"

        plan = plan_crud.get_plan_by_id(tool.plan_id) if tool.plan_id else None
        plan_val = plan.barcode if plan else "None"

        operations[str(idx)] = {
            "cell": cell_val,
            "tool": tool.name,
            "groupIndex": group_index,
            "groupName": group_name,
            "plan": plan_val
        }

    return {"operation": operations}


@history_router.post("/history/{device_number}", response_model=History)
def create_history(device_number: int, history_data: HistoryCreate, db: Session = Depends(get_db)):
    """
    Создает новую запись истории для инструмента, принадлежащего устройству.
    1. Находим устройство по device_number.
    2. Проверяем, что инструмент (history_data.tools_id) принадлежит данному устройству.
    3. Создаем запись истории.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    history_crud = EngineHistory()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # Проверяем принадлежность инструмента устройству
    if not tools_has_device_crud.check_tool_belongs_to_device(history_data.tools_id, device.id):
        raise HTTPException(status_code=403, detail="Инструмент не принадлежит данному устройству")

    new_history = history_crud.create_history(history_data)
    if not new_history:
        raise HTTPException(status_code=400, detail="Не удалось создать запись истории")

    return new_history


@history_router.put("/history/{device_number}/{history_id}", response_model=History)
def update_history(device_number: int, history_id: int, history_data: HistoryUpdate, db: Session = Depends(get_db)):
    """
    Обновляет запись истории.
    1. Находим устройство по device_number.
    2. Проверяем, что запись истории относится к инструменту, принадлежащему устройству.
    3. Обновляем запись.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    history_crud = EngineHistory()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_history = history_crud.get_history_by_id(history_id)
    if not existing_history:
        raise HTTPException(status_code=404, detail="Запись истории не найдена")

    # Проверяем, что инструмент записи истории принадлежит устройству
    if not tools_has_device_crud.check_tool_belongs_to_device(existing_history.tools_id, device.id):
        raise HTTPException(status_code=403, detail="Запись истории не принадлежит данному устройству")

    updated_history = history_crud.update_history_from_data(history_id, history_data)
    if not updated_history:
        raise HTTPException(status_code=400, detail="Не удалось обновить запись истории")
    return updated_history


@history_router.delete("/history/{device_number}/{history_id}")
def delete_history(device_number: int, history_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запись истории.
    1. Находим устройство по device_number.
    2. Проверяем, что запись истории принадлежит инструменту, связанному с устройством.
    3. Удаляем запись.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    history_crud = EngineHistory()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_history = history_crud.get_history_by_id(history_id)
    if not existing_history:
        raise HTTPException(status_code=404, detail="Запись истории не найдена")

    if not tools_has_device_crud.check_tool_belongs_to_device(existing_history.tools_id, device.id):
        raise HTTPException(status_code=403, detail="Запись истории не принадлежит данному устройству")

    deleted = history_crud.delete_history(history_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Не удалось удалить запись истории")
    return {"message": "Запись истории успешно удалена"}
