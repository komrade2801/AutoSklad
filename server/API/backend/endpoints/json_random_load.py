from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from API.backend.request_models import (
    HistoryRandomLoadResponse,  # Pydantic-модель для ответа: {"operation": { "1": { ... }, ... } }
    HistoryRandomLoad,  # Модель записи истории (ответ при создании/обновлении)
    HistoryRandomLoadCreate,  # Модель для создания записи
    HistoryRandomLoadUpdate  # Модель для обновления записи
)
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice

json_random_load_router = APIRouter(tags=["Json random load"])


@json_random_load_router.get("/history-random-load/{device_number}", response_model=HistoryRandomLoadResponse)
def get_history_random_load(device_number: int, db: Session = Depends(get_db)):
    """
    Получает записи истории "random load" для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем через Tools_has_Device все инструменты, принадлежащие устройству.
    3. Выбираем записи истории для этих инструментов.
    4. Для каждой записи:
       - получаем ячейку (через EngineCell.get_cell_by_tool_id),
       - инструмент (через EngineTools),
       - группу (через EngineGroup),
       - план (через EnginePlan).
    5. Формируем объект операции, где для каждой записи возвращаются поля:
       - cell (номер ячейки),
       - tool (название инструмента),
       - plan (штрих-код плана или "None"),
       - group (название группы).
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

    # Получаем записи истории для найденных инструментов
    histories = history_crud.get_history_by_tool_ids(tool_ids)
    if not histories:
        raise HTTPException(status_code=404, detail="Записи истории не найдены")

    operations: Dict[str, dict] = {}
    for idx, hist in enumerate(histories, start=1):
        tool = tools_crud.get_tool_by_id(hist.tools_id)
        if not tool:
            continue  # пропускаем запись, если инструмент не найден

        # Получаем ячейку, где находится инструмент (метод должен вернуть одну ячейку для данного инструмента)
        cell = cell_crud.get_cell_by_tool_id(tool.id)
        cell_val = str(cell.number) if cell and hasattr(cell, "number") else "Unknown"

        group = group_crud.get_group_by_id(tool.groups_id) if tool.groups_id else None
        group_val = group.name if group else "Unknown"

        plan = plan_crud.get_plan_by_id(tool.plan_id) if tool.plan_id else None
        plan_val = plan.barcode if plan else "None"

        operations[str(idx)] = {
            "cell": cell_val,
            "tool": tool.name,
            "plan": plan_val,
            "group": group_val
        }

    return {"operation": operations}


@json_random_load_router.post("/history-random-load/{device_number}", response_model=HistoryRandomLoad)
def create_history_random_load(device_number: int, history_data: HistoryRandomLoadCreate,
                               db: Session = Depends(get_db)):
    """
    Создает новую запись истории "random load" для указанного устройства.

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

    if not tools_has_device_crud.check_tool_belongs_to_device(history_data.tools_id, device.id):
        raise HTTPException(status_code=403, detail="Инструмент не принадлежит данному устройству")

    new_history = history_crud.create_history(history_data)
    if not new_history:
        raise HTTPException(status_code=400, detail="Не удалось создать запись истории")

    return new_history


@json_random_load_router.put("/history-random-load/{device_number}/{history_id}", response_model=HistoryRandomLoad)
def update_history_random_load(device_number: int, history_id: int, history_data: HistoryRandomLoadUpdate,
                               db: Session = Depends(get_db)):
    """
    Обновляет запись истории "random load" для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем запись истории по history_id.
    3. Проверяем, что запись истории принадлежит инструменту, связанному с устройством.
    4. Обновляем запись.
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

    updated_history = history_crud.update_history_from_data(history_id, history_data)
    if not updated_history:
        raise HTTPException(status_code=400, detail="Не удалось обновить запись истории")

    return updated_history


@json_random_load_router.delete("/history-random-load/{device_number}/{history_id}")
def delete_history_random_load(device_number: int, history_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запись истории "random load" для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем запись истории по history_id.
    3. Проверяем, что запись принадлежит инструменту, связанному с устройством.
    4. Удаляем запись.
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
