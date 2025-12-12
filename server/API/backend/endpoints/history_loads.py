import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from API.backend.endpoints.tool_library import tool_library_router
from API.backend.request_models import (
    HistoryLoadResponse,  # Модель для ответа: {"operation": { "0": { ... }, "1": { ... }, ... } }
    HistoryLoad,  # Модель записи истории загрузки (при чтении/обновлении)
    HistoryLoadCreate,  # Модель для создания записи загрузки
    HistoryLoadUpdate  # Модель для обновления записи загрузки
)
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolTypesCRUD import EngineToolTypes
# from DB.Engine.ToolsCRUD import EngineTools
# from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.UserCRUD import EngineUser

history_loads_router = APIRouter(tags=["History loads"])

# Словарь для преобразования статуса (например, status_id в строку)
STATUS_MAPPING = {
    0: "на загрузке",
    1: "исполнена",
    2: "отменена"
}


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y.%m.%d %H:%M:%S")


def format_id(load_id: int) -> str:
    # Форматирование идентификатора, например, как "0000 0000 0000 220"
    # Здесь можно изменить форматирование по требованиям проекта.
    return f"0000 0000 0000 {load_id:03d}"



@history_loads_router.get("/random_load", response_model=Dict[str, Dict[str, Any]])
def get_random_load(
    ID_load: int,
    db: Session = Depends(get_db)
):
    """
    Возвращает список ячеек с инструментами для конкретной загрузки ID_load
    в формате, совместимом с createTableRandomLoad:
    {
      "operation": {
        "1": { "cell": "...", "tool": "...", "plan": "...", "group": "..." },
        ...
      }
    }
    """
    # CRUD‑объекты
    mass_crud = EngineMassLoad()
    load_crud = EngineLoad()
    op_crud   = EngineLoadOperations()
    # status_crud = EngineStatus()
    cell_crud = EngineCell()
    # tools_crud = EngineTools()
    tool_types_crud = EngineToolTypes()

    # Проверяем, что такая массовая загрузка есть
    mass = mass_crud.get(ID_load)
    if not mass:
        raise HTTPException(status_code=404, detail="MassLoad не найден")

    # Берём все записи Load, привязанные к этой массовой загрузке
    loads = load_crud.filter_by(mass_load_id=ID_load)
    result: Dict[str, Dict[str, Any]] = {}

    # Для каждой записи Load — находим связанную последнюю операцию
    for idx, load in enumerate(loads, start=1):
        ops = op_crud.filter_by(load_id=load.id)
        if not ops:
            continue
        # выбираем самую позднюю по дате
        latest_op = max(ops, key=lambda o: o.date)

        # Инструмент и его тип/группа/чертёж (plan_id)
        # tool = tools_crud.get(latest_op.load_tools_id)
        tool_type = tool_types_crud.get(latest_op.load_tools_id) if latest_op else None

        # Ячейка
        cell = cell_crud.get(load.cell_id)

        # Формируем запись
        result[str(idx)] = {
            "cell": str(cell.id) if cell else "",
            "tool": tool_type.name if tool_type else "",
            "plan": "",
            "group": tool_type.groups_id and str(tool_type.groups_id) or ""
        }

    return {"operation": result}

@history_loads_router.get("/history-loads/{device_number}", response_model=HistoryLoadResponse)
def get_history_loads(device_number: int, db: Session = Depends(get_db)):
    """
    Получает записи истории загрузок для указанного устройства.

    1. Находим устройство по device_number.
    2. Через Tools_has_Device получаем все инструменты, принадлежащие устройству.
    3. Из таблицы загрузок выбираем записи, для которых tools_id входит в этот набор.
    4. Для каждой записи формируем объект с полями:
         - ID_load: отформатированный идентификатор
         - date: дата в формате dd.mm.yyyy
         - user: имя пользователя
         - status: статус в виде строки
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    load_ops_crud = EngineLoadOperations()
    load_crud = EngineLoad()
    history_crud = EngineHistory()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    # if not tool_ids:
    #     raise HTTPException(status_code=404, detail="Инструменты для данного устройства не найдены")

    loads = load_crud.all()

    # loads = load_ops_crud.get_loads_by_tool_ids(tool_ids)
    if not loads:
        raise HTTPException(status_code=404, detail="Записи загрузок не найдены")

    operations: Dict[str, dict] = {}
    for idx, load in enumerate(loads):
        history = history_crud.get(load.history_id)
        if not history:
            continue
        # Предполагается, что load имеет атрибуты: id, date (datetime), user (str), status_id (int) и tools_id
        operations[str(idx)] = {
            "ID_load": format_id(load.id),
            "date": format_date(history.date),
            "user": load.user,
            "status": STATUS_MAPPING.get(load.status_id, "неизвестно")
        }

    return {"operation": operations}



@history_loads_router.get("/history_loads", response_model=Dict[str, Dict[str, Any]])
def get_history_loads(db: Session = Depends(get_db)):
    """
    Возвращает события массовых загрузок (mass_load),
    формируя "ID_load" как "<Status.description> №<mass_load.id>"
    и выводя их в порядке создания.
    """
    mass_crud = EngineMassLoad()
    hist_crud = EngineHistory()
    op_crud   = EngineLoadOperations()
    stat_crud = EngineStatus()
    user_crud = EngineUser()
    load_crud = EngineLoad()
    # e_tools = EngineTools()
    e_tool_types = EngineToolTypes()
    e_cells = EngineCell()
    e_plans = EnginePlan()
    # 1) Получаем все mass_load-записи, сортируем по created_at по убыванию
    mass_loads = sorted(mass_crud.all(), key=lambda m: m.created_at, reverse=True)
    result_ops: Dict[str, Dict[str, Any]] = {}
    for idx, mass in enumerate(mass_loads):
        cells = []
        tools = []
        plans = []
        try:
            # 2) Находим последнюю операцию loadOperations для этой mass_load
            # 2) Находим все Load для этой mass_load
            loads = load_crud.filter_by(mass_load_id=mass.id)

            # 3) Находим все операции загрузки для этих Load
            ops = []
            for load in loads:
                ops.append(load)

                # ops.extend(op_crud.filter_by(load_id=load.id))
                # tool = e_tools.get_tool_by_id(load.tools_id)
                tool_types = e_tool_types.get_tool_type_by_id(load.tools_id)
                tools.append(tool_types.name)
                cell = e_cells.get_cell_by_id(cell_id=load.cell_id)
                if cell:
                    cell_number = cell.number
                    cells.append(cell_number)
                else:
                    cell_number = load.cell_id
                # if tool.plan_id:
                #     plan = e_plans.get_plan_by_id(tool.plan_id)
                #     plans.append(plan.name + " " + plan.description)
                if load.plan_id:
                    plan = e_plans.get_plan_by_id(load.plan_id)
                    plans.append(plan.designation + " " + plan.name)


            # 4) Берём самую свежую операцию, если есть
            latest_op = max(ops, key=lambda o: o.id) if ops else None

            print(f"latest_op = {latest_op}")

            # 6) Пользователь: из связанной истории
            history = hist_crud.get(latest_op.history_id) if latest_op and latest_op.history_id else None
            user = user_crud.get(history.user_id) if history else None
            user_name = f"{user.family} {user.first_name}" if user else "—"

            # 5) Статус: из самой операции
            status = stat_crud.get(mass.status_id) if history else None
            status_desc = status.description if status and status.description else (status.stype if status else "—")

            # 7) Формат полей
            date_str = mass.created_at.strftime("%H:%M:%S %d.%m.%Y")
            op_id_str = f"{status_desc} №{mass.id}"

            print(f"cells: {cells}")

            result_ops[str(idx)] = {
                "ID_load": op_id_str,
                "date": date_str,
                "user": user_name,
                "status": status.description.lower() if status else "—",
                "cells": cells,
                "tools": tools,
                "plans": plans
            }

        except Exception as e:
            print(traceback.format_exc())
            print(e.args)

            raise HTTPException(status_code=500, detail="Что то пошло не так:")

    return {"operation": result_ops}

@history_loads_router.post("/history-loads/{device_number}", response_model=HistoryLoad)
def create_history_load(device_number: int, load_data: HistoryLoadCreate, db: Session = Depends(get_db)):
    """
    Создает новую запись истории загрузки для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что инструмент (load_data.tools_id) принадлежит данному устройству.
    3. Создаем новую запись через EngineLoadOperations.
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    load_ops_crud = EngineLoadOperations()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # if not tools_has_device_crud.check_tool_belongs_to_device(load_data.tools_id, device.id):
    #     raise HTTPException(status_code=403, detail="Инструмент не принадлежит данному устройству")

    new_load = load_ops_crud.create_load(load_data)
    if not new_load:
        raise HTTPException(status_code=400, detail="Не удалось создать запись загрузки")

    return new_load


@history_loads_router.put("/history-loads/{device_number}/{load_id}", response_model=HistoryLoad)
def update_history_load(device_number: int, load_id: int, load_data: HistoryLoadUpdate, db: Session = Depends(get_db)):
    """
    Обновляет запись истории загрузки для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что запись загрузки (по load_id) существует.
    3. Проверяем, что инструмент записи принадлежит устройству.
    4. Обновляем запись через EngineLoadOperations.
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    load_ops_crud = EngineLoadOperations()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_load = load_ops_crud.get_load_by_id(load_id)
    if not existing_load:
        raise HTTPException(status_code=404, detail="Запись загрузки не найдена")

    # if not tools_has_device_crud.check_tool_belongs_to_device(existing_load.tools_id, device.id):
    #     raise HTTPException(status_code=403, detail="Запись загрузки не принадлежит данному устройству")

    updated_load = load_ops_crud.update_load(load_id, load_data)
    if not updated_load:
        raise HTTPException(status_code=400, detail="Не удалось обновить запись загрузки")

    return updated_load


@history_loads_router.delete("/history-loads/{device_number}/{load_id}")
def delete_history_load(device_number: int, load_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запись истории загрузки для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что запись загрузки принадлежит инструменту, связанному с устройством.
    3. Удаляем запись через EngineLoadOperations.
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    load_ops_crud = EngineLoadOperations()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_load = load_ops_crud.get_load_by_id(load_id)
    if not existing_load:
        raise HTTPException(status_code=404, detail="Запись загрузки не найдена")

    # if not tools_has_device_crud.check_tool_belongs_to_device(existing_load.tools_id, device.id):
    #     raise HTTPException(status_code=403, detail="Запись загрузки не принадлежит данному устройству")

    deleted = load_ops_crud.delete_load(load_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Не удалось удалить запись загрузки")

    return {"message": "Запись загрузки успешно удалена"}
