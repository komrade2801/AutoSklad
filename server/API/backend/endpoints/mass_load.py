import datetime
import traceback

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import dbSync
from API.backend.endpoints.color_map import STATUS_COLORS
from Core.authorization import AuthService
from DB.Engine.HelpCRUD import EngineHelp
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.HistoryCRUD import EngineHistory
# from DB.Engine.LoadCRUD import EngineLoad
# from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.LoadOperationsHasDeviceCRUD import EngineLoadOperationsHasDevice
# from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.MassLoadCRUD import EngineMassLoad
from typing import Dict  # , Optional  # Добавлен Optional
from collections import defaultdict
from fastapi.responses import RedirectResponse

import json

auth_service = AuthService()
mass_load_router = APIRouter(tags=["MassLoad"])


# Обновлённые модели
class ToolValue(BaseModel):
    id: int
    name: str
    description: str
    sum: int


class GroupForPlan(BaseModel):
    name: str
    value: Dict[str, ToolValue]


class PlanExport(BaseModel):
    name: str
    groups: Dict[str, GroupForPlan]


class PlansResponse(BaseModel):
    plans: Dict[str, PlanExport]


class History(BaseModel):
    cell: str
    tool: str
    plan: str


class MassLoadCreate(BaseModel):
    operation: Dict[str, History]


# Pydantic‑модели
class Content(BaseModel):
    tool: str
    plan: str
    mass_load: str


class CellResponse(BaseModel):
    id: int
    type: str
    backgroundColor: str
    content: Content
    block: bool


class RowResponse(BaseModel):
    cells: Dict[str, CellResponse]


class CellsMapResponse(BaseModel):
    rows: Dict[str, RowResponse]


#   {
#       "1": {
#           "cell": "2",
#           "tool": "Сверло 0,5 мм",
#           "plan": "None"
#       },
#       "2": {
#           "cell": "1",
#           "tool": "Сверло 0,7 мм",
#           "plan": "None"
#       }
#   }


@mass_load_router.get(
    "/cells_map/{device_number}",
    response_model=CellsMapResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка формирования cells map JSON"}}
)
def cells_map(device_number: int, db: Session = Depends(get_db)):
    # 1. Достаём устройство и парсим details
    e_dev = EngineDevice()
    device = e_dev.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    try:
        details = json.loads(device.details or "{}")
        sig = details.get("signature", {})
        cols = sig["cells"]["columns"]
        rows = sig["cells"]["rows"]
    except Exception:
        raise HTTPException(400, "Неверный формат Device.details")

    # 2. Берём все связи Cell ←→ Device
    e_chd = EngineCellHasDevice()
    # предполагается list of models, у которых .cell_id
    linked_cells = e_chd.get_cells_by_device_id(device.id)

    # linked_ids = linked_cells

    # 3. Для быстрого поиска
    e_cell = EngineCell()
    e_tools = EngineTools()
    e_tool_types = EngineToolTypes()
    e_plan = EnginePlan()
    e_status = EngineStatus()
    e_load = EngineLoad()
    e_load_operations = EngineLoadOperations()
    e_mass_load = EngineMassLoad()

    def get_background_color(
            status_id: int,
            has_plan: bool,
            db: Session
    ) -> str:
        """
        Возвращает цвет фона для данного статуса.
        Определяет stype по status_id, затем отдаёт цвет из STATUS_COLORS.
        """
        try:
            status = e_status.get(status_id)
        except SQLAlchemyError:
            return STATUS_COLORS.get("__default__")

        if not status or not status.stype:
            return STATUS_COLORS.get("__default__")

        cmap = STATUS_COLORS.get(status.stype, STATUS_COLORS["__default__"])
        if isinstance(cmap, dict):
            return cmap.get(has_plan, STATUS_COLORS["__default__"])
        return cmap

    # 4. Сборка JSON
    result_rows: Dict[str, RowResponse] = {}

    mass_load_max_id = e_mass_load.get_max_id()

    for r in range(1, rows + 1):
        cells_in_row: Dict[str, CellResponse] = {}
        for c in range(1, cols + 1):
            try:
                number = (r - 1) * cols + c
                cell = e_cell.get_cell_by_number(number)
                load = e_load.find_by_tools_id(cell.tools_id)

                mass_load_id = ""

                if load and not load == []:
                    mass_load_id = str(load[0].mass_load_id)

                if not cell:
                    continue

                # 4.1 Определяем block
                block = cell.tools_id is not None and cell.tools_id != 0

                # 4.2 Контент (tool, plan)
                if block:
                    tool = e_tools.get_tool_by_id(cell.tools_id)
                    # название инструмента — inventory_number, а не тип
                    tool_name = e_tool_types.get_tool_type_by_id(
                        tool.tool_type_id).name or ""
                    plan = e_plan.get(
                        tool.plan_id) if tool and tool.plan_id else None
                    plan_name = plan.name if plan else ""
                else:
                    tool_name = "None"
                    plan_name = "None"

                # 4.3 Цвет по статусу и наличию чертежа
                bg = get_background_color(cell.status_id, bool(plan_name), db)

                # 4.4 Тип ячейки — берём из конфига, если есть, иначе "big"
                cell_type = sig.get("type", "big")

                cells_in_row[str(c)] = CellResponse(
                    id=cell.number,
                    type=cell_type,
                    backgroundColor=bg,
                    content=Content(tool=tool_name, plan=plan_name,
                                    mass_load=mass_load_id + ":" + str(mass_load_max_id)),
                    block=block
                )
            except Exception as e:
                print(e)
                print(traceback.format_exc())

        result_rows[str(r)] = RowResponse(cells=cells_in_row)

    return CellsMapResponse(rows=result_rows)


@mass_load_router.get(
    "/mass_load_tools",
    response_model=PlansResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка при формировании tools JSON"}}
)
def export_tools(device_number: int, db: Session = Depends(get_db)):
    try:
        e_plan = EnginePlan()
        e_tools = EngineTools()
        e_tool_types = EngineToolTypes()
        e_group = EngineGroup()
        e_load = EngineLoad()
        e_load_operations = EngineLoadOperations()
        e_load_operations_has_device = EngineLoadOperationsHasDevice()
        e_tools_has_device = EngineToolsHasDevice()
        e_mass_load = EngineMassLoad()
        e_device = EngineDevice()
        e_cells = EngineCell()
        e_status = EngineStatus()
        all_tool_types = e_tool_types.get_all_tool_types()
        all_tools = e_tools.get_all_tools()
        all_plans = e_plan.get_all_plans()
        all_groups = e_group.get_all_groups()

        device = e_device.get_device_by_number(device_number)
        if not device:
            raise HTTPException(
                status_code=404, detail="Устройство не найдено")

        last_mass_load_id = e_mass_load.get_max_id()
        loads_by_mass_loads = e_load.get_loads_by_mass_load_id(
            mass_load_id=last_mass_load_id
        )
        load = loads_by_mass_loads[0].id if loads_by_mass_loads else 0
        load_operations = e_load_operations.get_operations_by_load_id(load)
        if load_operations:
            loads_by_mass_load = max(load_operations, key=lambda rec: rec.id)
            operations_has_device = e_load_operations_has_device.get_by_device(
                device.id)

            # loads_by_mass_load = loads_by_mass_loads[0]  # .first()
            load = e_load.get_load_by_id(loads_by_mass_load.load_id)
            cell = e_cells.get_cell_by_id(load.cell_id)

            _status = e_status.get_status_by_id(loads_by_mass_load.status_id)

            if not _status:
                # return {"redirect_to": "/screen_23_mass_locked.html"}
                return RedirectResponse("/screen_23_mass_locked.html", status_code=302)

            if 'init' in _status.stype:
                # return {"redirect_to": "/screen_23_mass_locked.html"}
                return RedirectResponse("/screen_23_mass_locked.html", status_code=302)

        plan_id_to_name = {plan.id: plan.name for plan in all_plans}
        group_id_to_obj = {group.id: group for group in all_groups}
        tool_type_id_to_obj = {tt.id: tt for tt in all_tool_types}
        tool_type_map = {}  # to store tool_type obj per concatenated name

        # Собираем данные
        plan_map = defaultdict(lambda: {
            "name": "None",
            "groups": defaultdict(lambda: {
                "name": "None",
                "value": defaultdict(int)
            })
        })

        for tool in all_tools:

            is_linked = e_tools_has_device.this_tool_is_linked(tool.id)
            if is_linked:
                continue

            load = e_load.find_by_tools_id(
                tools_id=tool.id
            )

            if load:
                continue
            tool_type = tool_type_id_to_obj.get(tool.tool_type_id)
            if not tool_type:
                continue

            group = group_id_to_obj.get(tool_type.groups_id)
            group_name = group.name if group else "None"  # None вместо "Без группы"

            plan_id = tool.plan_id
            plan_name = plan_id_to_name.get(plan_id)  # None если нет плана
            if not plan_name:
                plan_name = "None"
            plan_entry = plan_map[plan_name]
            plan_entry["name"] = plan_name  # Прямое присвоение

            group_entry = plan_entry["groups"][group_name]
            group_entry["name"] = group_name
            tool_type_name = ""
            if tool_type.description and tool_type.name:
                tool_type_name = tool_type.name + " " + tool_type.description
            else:
                tool_type_name = tool_type.name
            tool_type_map[tool_type_name] = tool_type  # store for later
            tool_type_id = tool_type.id
            group_entry["value"][tool_type_name] += 1
            # group_entry["value"]["id"] = tool_type_id

            # Преобразование в ответ
        plans_dict = {}
        for plan_idx, (plan_name, plan_data) in enumerate(plan_map.items()):
            groups_dict = {}
            for group_idx, (group_name, group_data) in enumerate(plan_data["groups"].items()):
                value_dict = {}
                for tool_idx, (tool_name, count) in enumerate(group_data["value"].items()):
                    tt = tool_type_map[tool_name]
                    value_dict[str(tool_idx)] = {
                        "id": tool_idx, "name": tt.name, "description": tt.description or "", "sum": count}

                groups_dict[str(group_idx)] = {
                    "name": group_data["name"],
                    "value": value_dict
                }

            plans_dict[str(plan_idx)] = {
                "name": plan_data["name"],
                "groups": groups_dict
            }

        return {"plans": plans_dict}

    except Exception as e:
        print(traceback.format_exc())

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при формировании Plans JSON: {str(e)}"
        )


@mass_load_router.post("/mass_load_tools/{device_number}")
def save_mass_load(
    request: Request,
    device_number: int,
    mass_load: MassLoadCreate,
    db: Session = Depends(get_db),
):
    # 1) авторизация
    validation = auth_service.validation_user(request)
    if isinstance(validation, RedirectResponse) or ("status" in getattr(validation, "data", {})):
        raise HTTPException(
            status_code=402, detail="Неавторизованный доступ запрещён")

    # 2) получаем устройство
    e_device = EngineDevice()
    device = e_device.get_device_by_number(device_number)
    if not device:
        raise HTTPException(
            status_code=404, detail="Устройство не обнаружено!")

    # 3) создаём остальные движки
    e_plan = EnginePlan()
    e_tools = EngineTools()
    e_tool_types = EngineToolTypes()
    e_group = EngineGroup()
    e_load = EngineLoad()
    e_load_operation = EngineLoadOperations()
    e_operation_has_device = EngineLoadOperationsHasDevice()
    e_mass_load = EngineMassLoad()
    e_cells = EngineCell()
    e_cell_has_device = EngineCellHasDevice()
    e_stories = EngineHistory()
    e_status = EngineStatus()
    e_user = EngineUser()
    e_tools_has_device = EngineToolsHasDevice()

    group_name_to_id = {g.name: g.id for g in e_group.all()}

    # 4) подготовка переменных
    stories: Dict[str, History] = mass_load.operation
    mass_load_id = None
    new_mass_load = None
    loads: list = []
    cell_backs: list = []
    device_id = device.id
    operation_ids: list[int] = []
    story_ids: list[int] = []

    try:
        # 5) создаём запись MassLoad
        mass_load_id = max(e_mass_load.get_all_ids(), default=0) + 1
        e_mass_load.add_mass_load(
            index=mass_load_id,
            description=(
                f"Инициализирована новая массовая загрузка инструмента в аппарат "
                f"{device.name}, время: {datetime.datetime.now()}"
            ),
        )
        new_mass_load = e_mass_load.get_mass_load_by_id(mass_load_id)

        # 6) обрабатываем каждую операцию
        for key, story in stories.items():
            # разбираем вход
            request_cell = story.cell
            request_tool = story.tool
            request_plan = story.plan

            # подбор типа инструмента по группе и имени
            parts = request_tool.split(' ', 1)
            if len(parts) == 2:
                group_name, tool_name = parts
                group_id = group_name_to_id.get(group_name)
                if group_id is None:
                    raise HTTPException(status_code=404, detail=f"Группа '{group_name}' не найдена")
                tool_type = e_tool_types.find_by_name_and_group(tool_name, group_id)
                if not tool_type:
                    raise HTTPException(status_code=404, detail=f"Инструмент '{tool_name}' не найден в группе '{group_name}'")
            else:
                # fallback to old parsing
                tool_types = e_tool_types.find_by_name(request_tool)
                if not tool_types:
                    raise HTTPException(
                        status_code=404, detail=f"Подходящий инструмент '{request_tool}' не найден")
                tool_type = tool_types[0]

            # выбираем конкретный инструмент
            db_tools = e_tools.get_tools_by_tool_type(tool_type.id)
            load_id = max(e_load.get_all_ids(), default=0) + 1
            tool_to_load = next(
                (t for t in db_tools if not e_load.find_by_tools_id(t.id)), None)
            if not tool_to_load:
                raise HTTPException(
                    status_code=404, detail="Подходящий инструмент не найден")

            # получаем и обновляем cell
            cell = e_cells.get_cell_by_number(int(request_cell))
            if not cell:
                raise HTTPException(
                    status_code=404, detail="Система не инициирована")

            mass_load_status = e_status.find_by_name("mass_load_init")
            if not mass_load_status:
                idx = max(e_status.get_all_ids(), default=0) + 1
                e_status.add(index=idx, stype="mass_load_init",
                             description="Инициализирована массовая загрузка")
                mass_load_status = e_status.get_status_by_id(idx)
            status_load = e_status.find_by_name("mass_load_init")

            # привязываем инструмент к устройству
            e_tools_has_device.add_link(
                tools_id=tool_to_load.id, device_id=device.id)
            if not e_tools_has_device.this_tool_is_linked(tool_to_load.id):
                raise HTTPException(
                    status_code=500,
                    detail=f"Связь инструмента ID={tool_to_load.id} с устройством не установлена",
                )

            # backup и обновление ячейки
            cell_backs.append(e_cells.get_cell_by_id(cell.id))
            e_cells.update_cell(
                cell_id=cell.id,
                number=cell.number,
                description=f"Объявлена новая загрузка {new_mass_load.description}",
                groups_id=tool_type.groups_id,
                tools_id=tool_to_load.id,
                status_id=mass_load_status.id,
            )

            # создаём Load
            e_load.add_load(
                load_id=load_id,
                description="",
                tools_id=tool_to_load.id,
                mass_load_id=new_mass_load.id,
                cell_id=cell.id,
            )
            load = e_load.get_load_by_id(load_id)
            if not load:
                raise HTTPException(
                    status_code=500, detail="Не удалось получить Load после создания")
            loads.append(load)

            # привязываем cell к устройству
            e_cell_has_device.add_link(cell_id=cell.id, device_id=device.id)

            # создаём History
            story_id = max(e_stories.get_all_ids(), default=0) + 1
            story_ids.append(story_id)
            user = e_user.get_user_by_barcode(validation.user_barcode)
            if not user:
                raise HTTPException(
                    status_code=402, detail="Пользователь не найден")
            e_stories.add_history(
                history_id=story_id,
                user_id=user.id,
                role_id=user.role_id,
                tools_id=tool_to_load.id,
                datetime_value=datetime.datetime.now(),
                status=0,
                description=(
                    f"Массовая загрузка инициирована"
                ),
            )
            new_history = e_stories.get_history_by_id(story_id)
            if not new_history:
                raise HTTPException(
                    status_code=500, detail="Не удалось получить History после добавления")

            # создаём LoadOperation и привязываем к устройству
            operation_id = max(e_load_operation.get_all_ids(), default=0) + 1
            operation_ids.append(operation_id)
            e_load_operation.add_operation(
                operation_id=operation_id,
                date=datetime.datetime.now(),
                load_id=load_id,
                load_tools_id=tool_to_load.id,
                status_id=status_load.id,
                history_id=story_id,
                description="",
            )
            operation = e_load_operation.get_load_by_id(operation_id)
            if not operation:
                raise HTTPException(
                    status_code=500, detail="Не удалось получить Operation после добавления")
            e_operation_has_device.add_link(
                load_operations_id=operation_id, device_id=device.id)

        return {"status": "ok", "message": new_mass_load.description}

    except Exception as e:
        print(traceback.format_exc())
        # откат в обратном порядке
        try:
            for op_id in operation_ids:
                e_operation_has_device.delete_link(
                    load_operations_id=op_id, device_id=device_id)
            for op_id in operation_ids:
                e_load_operation.delete(index=op_id)
            for st_id in story_ids:
                e_stories.delete(st_id)
            for cb in cell_backs:
                e_cell_has_device.delete_link(
                    cell_id=cb.id, device_id=device_id)
            for ld in loads:
                e_load.delete(ld.id)
                e_tools_has_device.delete_link(
                    tools_id=ld.tools_id, device_id=device_id)
            for cb in cell_backs:
                e_cells.update_cell(
                    cell_id=cb.id,
                    number=cb.number,
                    description=cb.description,
                    groups_id=cb.groups_id,
                    tools_id=cb.tools_id,
                    status_id=cb.status_id,
                )

            if mass_load_id is not None:
                e_mass_load.delete(mass_load_id)
        except Exception:
            print(traceback.format_exc())
            pass

        raise HTTPException(
            status_code=500, detail=f"Не удалось сохранить массовую загрузку: {e}")
