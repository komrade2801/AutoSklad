import traceback

from Core.app_logging import get_logger
from fastapi import APIRouter, Depends, HTTPException

logger = get_logger(__name__)
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime

from API.backend.endpoints.tool_library import tool_library_router
from API.backend.request_models import (
    HistoryLoadResponse,  # Модель для ответа: {"operation": { "0": { ... }, "1": { ... }, ... } }
    HistoryLoad,  # Модель записи истории загрузки (при чтении/обновлении)
    HistoryLoadCreate,  # Модель для создания записи загрузки
    HistoryLoadUpdate, HistoryDropResponse, HistoryDropCreate  # Модель для обновления записи загрузки
)
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.MassDropCRUD import EngineMassDrop
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

history_drops_router = APIRouter(tags=["History drops"])

# Словарь для преобразования статуса (например, status_id в строку)
STATUS_MAPPING = {
    0: "на выгрузке",
    1: "исполнена",
    2: "отменена"
}


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y.%m.%d %H:%M:%S")


def format_id(load_id: int) -> str:
    # Форматирование идентификатора, например, как "0000 0000 0000 220"
    # Здесь можно изменить форматирование по требованиям проекта.
    return f"0000 0000 0000 {load_id:03d}"



@history_drops_router.get("/random_drop", response_model=Dict[str, List[Any]])
def get_random_drop(
    ID_drop: int,
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
    # mass_crud = EngineMassLoad()
    mass_drop_crud = EngineMassDrop()
    # load_crud = EngineLoad()
    drop_crud = EngineDrop()
    # op_crud   = EngineLoadOperations()
    # status_crud = EngineStatus()
    cell_crud = EngineCell()
    # tools_crud = EngineTools()
    tool_types_crud = EngineToolTypes()
    plan_crud = EnginePlan()
    group_crud = EngineGroup()

    # Проверяем, что такая массовая загрузка есть
    mass = mass_drop_crud.get(ID_drop)
    if not mass:
        raise HTTPException(status_code=404, detail="MassDrop не найден")

    # Берём все записи Load, привязанные к этой массовой загрузке
    drops = drop_crud.filter_by(mass_drop_id=ID_drop)
    # result: Dict[str, Dict[str, Any]] = {}
    result: List[Dict[str, Any]] = []

    # Для каждой записи Drop — находим связанную последнюю операцию
    for idx, drop in enumerate(drops, start=1):
        # ops = op_crud.filter_by(load_id=drop.id)
        # if not ops:
        #     continue
        # выбираем самую позднюю по дате
        # latest_op = max(ops, key=lambda o: o.date)

        # Инструмент и его тип/группа/чертёж (plan_id)
        # tool = tools_crud.get(latest_op.load_tools_id)
        tool_type = tool_types_crud.get(drop.tools_id)

        group = group_crud.get(tool_type.groups_id)

        # Ячейка
        cell = cell_crud.get(drop.cell_id)

        plan = plan_crud.get(drop.plan_id)

        # Формируем запись
        result.append({
            "cell": str(cell.id) if cell else "",
            "tool": tool_type.name if tool_type else "",
            "plan": plan.designation if plan else "",
            "group": group.name if group else ""
        })

    return {"operation": result}

@history_drops_router.get("/history_drops", response_model=Dict[str, List[Any]])
def get_history_drops(db: Session = Depends(get_db)):
    """
    Возвращает события массовых загрузок (mass_load),
    формируя "ID_load" как "<Status.description> №<mass_load.id>"
    и выводя их в порядке создания.
    """
    # mass_crud = EngineMassLoad()
    mass_drop_crud = EngineMassDrop()
    hist_crud = EngineHistory()
    # op_crud   = EngineLoadOperations()
    stat_crud = EngineStatus()
    user_crud = EngineUser()
    # load_crud = EngineLoad()
    drop_crud = EngineDrop()
    # e_tools = EngineTools()
    e_tool_types = EngineToolTypes()
    e_cells = EngineCell()
    e_plans = EnginePlan()
    # 1) Получаем все mass_load-записи, сортируем по created_at по убыванию
    mass_drops = sorted(mass_drop_crud.all(), key=lambda m: m.created_at, reverse=True)
    # result_ops: Dict[str, Dict[str, Any]] = {}
    result_ops: List[Dict[str, Any]] = []
    for idx, mass in enumerate(mass_drops):
        cells = []
        tools = []
        plans = []
        try:
            # 2) Находим все Load для этой mass_load
            drops = drop_crud.filter_by(mass_drop_id=mass.id)
            op_status = stat_crud.find_by_name("mass_drop_ready")
            if op_status:
                op_status = op_status.id
            else:
                op_status = 4

            # 3) Находим все операции загрузки для этих Load
            ops = []
            for drop in drops:
                ops.append(drop)

                # ops.extend(op_crud.filter_by(load_id=load.id))
                # tool = e_tools.get_tool_by_id(load.tools_id)
                tool_types = e_tool_types.get_tool_type_by_id(drop.tools_id)
                tools.append(tool_types.name)
                cell = e_cells.get_cell_by_id(cell_id=drop.cell_id)
                if cell:
                    cell_number = cell.number
                    cells.append({'cell': cell_number, 'status': drop.status_id})
                else:
                    cell_number = drop.cell_id
                # if tool.plan_id:
                #     plan = e_plans.get_plan_by_id(tool.plan_id)
                #     plans.append(plan.name + " " + plan.description)
                if drop.plan_id:
                    plan = e_plans.get_plan_by_id(drop.plan_id)
                    plans.append(plan.designation + " " + plan.name)

                if drop.status_id == 4:
                    op_status = drop.status_id


            # 4) Берём самую свежую операцию, если есть
            latest_op = max(ops, key=lambda o: o.id) if ops else None

            logger.debug("latest_op: %s", latest_op)

            # 6) Пользователь: из связанной истории
            history = hist_crud.get(latest_op.history_id) if latest_op and latest_op.history_id else None
            user = user_crud.get(history.user_id) if history else None
            if user:
                patronymic_initial = (user.second_name[0] + '.') if (user.second_name and len(user.second_name) > 0) else ''
                user_name = f"{user.family} {user.first_name[0] if user.first_name else ''}. {patronymic_initial}".strip()
            else:
                user_name = "—"

            # 5) Статус: из самой операции
            status = stat_crud.get(op_status) if op_status else None
            status_desc = status.description if status and status.description else (status.stype if status else "—")

            # 7) Формат полей
            date_str = mass.created_at.strftime("%H:%M:%S %d.%m.%Y")
            op_id_str = f"{status_desc} №{mass.id}"

            logger.debug("cells: %s", cells)

            result_ops.append({
                "mass_id": mass.id,
                "ID_drop": op_id_str,
                "date": date_str,
                "user": user_name,
                "status": status.description.lower() if status else "—",
                "cells": cells,
                "tools": tools,
                "plans": plans
            })

        except Exception as e:
            logger.exception("history_drops: %s", e)
            raise HTTPException(status_code=500, detail="Что то пошло не так:")

    return {"operation": result_ops}
