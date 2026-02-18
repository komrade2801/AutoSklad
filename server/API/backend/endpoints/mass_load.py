import datetime
import traceback

from Core.app_logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, status, Request

from DB.Engine.ConsumptionCRUD import EngineConsumption
from DB.Engine.DropCRUD import EngineDrop

logger = get_logger(__name__)
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import dbSync
from API.backend.endpoints.all_users import user_barcode
from API.backend.endpoints.color_map import STATUS_COLORS
from Core.authorization import AuthService
from DB.Engine.HelpCRUD import EngineHelp
from DB.Engine.HistoryHasDeviceCRUD import EngineHistoryHasDevice
from DB.Engine.PlanToolTypesCRUD import EnginePlanToolTypes
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
# from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.MassLoadHasDeviceCRUD import EngineMassLoadHasDevice
from typing import Dict, List, Optional
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
    sum: str


class GroupForPlan(BaseModel):
    name: str
    value: Dict[str, ToolValue]


class PlanExport(BaseModel):
    name: str
    groups: Dict[str, GroupForPlan]


class PlansResponse(BaseModel):
    plans: Dict[str, PlanExport]

class ToolTypesResponse(BaseModel):
    tools: List[ToolValue]


class History(BaseModel):
    # cell: int
    tool: int
    plan: Optional[int] = None
    sum: int = 1


class MassLoadCreate(BaseModel):
    operation: Dict[str, History]


# Pydantic‑модели
class Content(BaseModel):
    tool: str
    group: str
    plan: str
    load: str
    status_id: int | None = None


class CellResponse(BaseModel):
    id: int
    number: int
    type: str
    backgroundColor: str
    content: Content
    block: bool


class RowResponse(BaseModel):
    cells: Dict[str, CellResponse]


class CellsMapResponse(BaseModel):
    rows: Dict[str, RowResponse]

class CellsStatusResponse(BaseModel):
    free: int
    occupied: int


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
    "/cells_status",
    response_model=CellsStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка формирования cells map JSON"}}
)
def cells_status(device_number: int, db: Session = Depends(get_db)):
    # 1. Достаём устройство и парсим details
    e_dev = EngineDevice()
    device = e_dev.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # try:
    #     details = json.loads(device.details or "{}")
    #     sig = details.get("signature", {})
    #     cols = sig["cells"]["columns"]
    #     rows = sig["cells"]["rows"]
    # except Exception:
    #     raise HTTPException(400, "Неверный формат Device.details")

    # 2. Берём все связи Cell ←→ Device
    e_chd = EngineCellHasDevice()
    # предполагается list of models, у которых .cell_id
    linked_cells = e_chd.get_cells_by_device_id(device.id)

    free_cells = 0
    occupied_cells = 0

    # 3. Для быстрого поиска
    e_cell = EngineCell()

    for cell_id in linked_cells:
        cell = e_cell.get_cell_by_id(cell_id)

        if cell.status_id in {1, 8}:
            free_cells += 1
        else:
            occupied_cells += 1

    print(f"free {free_cells}, occupied {occupied_cells}")

    return CellsStatusResponse(free=free_cells, occupied=occupied_cells)

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
    # e_chd = EngineCellHasDevice()
    # предполагается list of models, у которых .cell_id
    # linked_cells = e_chd.get_cells_by_device_id(device.id)

    # linked_ids = linked_cells

    # 3. Для быстрого поиска
    e_cell = EngineCell()
    e_tool_types = EngineToolTypes()
    e_group = EngineGroup()
    e_plan = EnginePlan()
    e_status = EngineStatus()
    e_load = EngineLoad()

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
        # print(f"status.stype: {status.stype}, color: {cmap}")
        if isinstance(cmap, dict):
            return cmap.get(has_plan, STATUS_COLORS["__default__"])
        return cmap

    # 4. Сборка JSON
    result_rows: Dict[str, RowResponse] = {}

    # mass_load_max_id = e_mass_load.get_max_id()

    for r in range(1, rows + 1):
        cells_in_row: Dict[str, CellResponse] = {}
        for c in range(1, cols + 1):
            try:
                number = (r - 1) * cols + c
                cell = e_cell.get_cell_by_number(number)
                loads = e_load.find_by_tools_id(cell.tools_id)

                # mass_load_id = ""
                #
                # if loads and not loads == []:
                #     mass_load_id = str(loads[0].mass_load_id)

                if not cell:
                    continue

                loads = e_load.find_by_cell_id(cell.id)
                _status = cell.status_id
                # print(f"cell: {cell.number}, status: {cell.status_id}")
                plan = None
                load = None

                plan_name = ""

                if loads:
                    load = max(loads, key=lambda rec: rec.id)

                    plan = e_plan.get_plan_by_id(load.plan_id)
                    # history = e_history.get_history_by_id(load.history_id)

                    if plan:
                        plan_name = plan.designation

                # 4.1 Определяем block
                block = cell.tools_id is not None and cell.tools_id != 0

                tool_name = "None"
                group_name = "Группа неизвестна"

                # 4.2 Контент (tool, plan)
                if block:
                    # tool = e_tools.get_tool_by_id(cell.tools_id)
                    # название инструмента — inventory_number, а не тип
                    tool_type = e_tool_types.get_tool_type_by_id(
                        cell.tools_id)
                    if tool_type:
                        tool_name = tool_type.name or ""

                        group_name = e_group.get_group_by_id(tool_type.groups_id).name or ""

                # 4.3 Цвет по статусу и наличию чертежа
                bg = get_background_color(_status, bool(plan), db)

                # 4.4 Тип ячейки — берём из конфига, если есть, иначе "big"
                cell_type = sig.get("type", "big")

                cells_in_row[str(c)] = CellResponse(
                    id=cell.id,
                    number=cell.number,
                    type=cell_type,
                    backgroundColor=bg,
                    content=Content(tool=tool_name, group=group_name, plan=plan_name,
                                    load=str(load.id) if load else '',
                                    status_id=_status),
                    block=block
                )
            except Exception as e:
                logger.exception("mass_load cell/row error: %s", e)

        result_rows[str(r)] = RowResponse(cells=cells_in_row)

    return CellsMapResponse(rows=result_rows)


@mass_load_router.get(
    "/mass_load_tools",
    response_model=ToolTypesResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка при формировании tools JSON"}}
)
def export_tools(device_number: int, db: Session = Depends(get_db)):
    try:
        e_tool_types = EngineToolTypes()
        e_load = EngineLoad()
        e_drop = EngineDrop()
        # e_consumption = EngineConsumption()
        e_device = EngineDevice()
        all_tool_types = e_tool_types.get_all_tool_types()

        device = e_device.get_device_by_number(device_number)
        if not device:
            raise HTTPException(
                status_code=404, detail="Устройство не найдено")

        tool_type_list = []

        for tool_type in all_tool_types:
            count = tool_type.count

            if count == 0:
                count = '-'
            else:
                loads = e_load.find_by_tools_id_and_status_list(tool_type.id, [3,5])
                drops = e_drop.find_by_tools_id_and_status_list(tool_type.id, [2,4])
                # consumptions = e_consumption.get_by_tool_id(tool_type.id)
                if loads:
                    count -= len(loads)
                if drops:
                    count += len(drops)
                count = str(count)

            tool_type_list.append({"id": tool_type.id, "name": tool_type.name, "description": tool_type.description or "", "sum": count})

        return {"tools": tool_type_list}

    except Exception as e:
        logger.exception("export_tools error")
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
    logger.debug("save_mass_load request: %s, device_number: %s, mass_load: %s", request, device_number, mass_load)
    # 1) авторизация
    validation = auth_service.validation_user(request)
    if isinstance(validation, RedirectResponse) or ("status" in getattr(validation, "data", {})):
        raise HTTPException(
            status_code=401, detail="Неавторизованный доступ запрещён")

    try:
        validation.user_barcode
    except Exception as e:
        logger.exception("save_mass_load auth")
        raise HTTPException(
            status_code=401, detail="Неавторизованный доступ запрещён")

    # 2) получаем устройство (используем общую сессию db при вызове из create_plan)
    e_device = EngineDevice(session=db)
    device = e_device.get_device_by_number(device_number)
    if not device:
        raise HTTPException(
            status_code=404, detail="Устройство не обнаружено!")

    # 3) создаём остальные движки с той же сессией (план и массовая загрузка в одной транзакции)
    e_plan = EnginePlan(session=db)
    # e_tools = EngineTools()
    e_tool_types = EngineToolTypes(session=db)
    e_group = EngineGroup(session=db)
    e_load = EngineLoad(session=db)
    e_drop = EngineDrop(session=db)
    e_load_operation = EngineLoadOperations(session=db)
    e_operation_has_device = EngineLoadOperationsHasDevice(session=db)
    e_history_has_device = EngineHistoryHasDevice(session=db)
    e_mass_load = EngineMassLoad(session=db)
    e_mass_load_has_device = EngineMassLoadHasDevice(session=db)
    e_cells = EngineCell(session=db)
    e_cell_has_device = EngineCellHasDevice(session=db)
    e_stories = EngineHistory(session=db)
    e_status = EngineStatus(session=db)
    e_user = EngineUser(session=db)
    # e_tools_has_device = EngineToolsHasDevice()

    group_name_to_id = {g.name: g.id for g in e_group.all()}

    # 4) подготовка переменных
    stories: Dict[str, History] = mass_load.operation
    mass_load_id = None
    new_mass_load = None
    loads: list = []
    cell_backs: list = []
    device_id = device.id  # PK в БД (для связей HasDevice и т.д.)
    # Ключ очереди синхронизации на сервере — device_number (int, как в main.py start_sync(dev.number))
    queue_device_id = int(device_number)
    operation_ids: list[int] = []
    story_ids: list[int] = []

    # Проверка наличия очереди синхронизации для устройства (очередь зарегистрирована по device_number)
    from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES
    queue_in = INBOUND_QUEUES.get(queue_device_id)
    logger.debug("[save_mass_load] device_id=%s, device_number=%s, queue_device_id=%s, queue_in=%s, available_devices=%s",
                 device_id, device_number, queue_device_id, 'EXISTS' if queue_in else 'NOT FOUND', list(INBOUND_QUEUES.keys()))
    if not queue_in:
        logger.warning("[save_mass_load] Очередь синхронизации не найдена для queue_device_id=%s! Команды синхронизации НЕ будут созданы.", queue_device_id)

    # Устанавливаем device_id для CRUD так, чтобы декоратор @sync_aware клал команды в правильную очередь (по device_number)
    e_cells.device_id = queue_device_id
    e_stories.device_id = queue_device_id
    e_load.device_id = queue_device_id
    e_load_operation.device_id = queue_device_id
    e_mass_load.device_id = queue_device_id
    e_mass_load_has_device.device_id = queue_device_id
    logger.debug("[save_mass_load] Установлен device_id=%s для CRUD-объектов (ключ очереди)", queue_device_id)

    # 6) разворачиваем операции: каждый инструмент с sum > 1 превращается в sum отдельных записей
    flat_stories = []
    for key, story in stories.items():

        # проверяем, что инструмент ещё в наличии

        request_tool_type_id = story.tool
        request_count = story.sum
        tool_type = e_tool_types.get_tool_type_by_id(request_tool_type_id)
        if tool_type:
            count = tool_type.count

            if count > 0:
                loads = e_load.find_by_tools_id_and_status_list(request_tool_type_id, [3,5])
                drops = e_drop.find_by_tools_id_and_status_list(request_tool_type_id, [2,4])
                # consumptions = e_consumption.get_by_tool_id(tool_type.id)
                if loads:
                    count -= len(loads)
                if drops:
                    count += len(drops)

                if count < request_count:
                    error_msg = f"Инструмента с id '{request_tool_type_id}' недостаточно на складе. Требуется: {request_count}, имеется: {count}"
                    logger.error(f"[save_mass_load] {error_msg})")
                    raise HTTPException(status_code=400, detail=error_msg)

        for _i in range(story.sum):
            flat_stories.append((key, story))

    empty_cells = e_cells.get_all_empty_cells()
    total_tools = sum(s.sum for s in stories.values())

    logger.debug("[create_plan] create_mass_load=True: empty_cells count=%s, total_tools=%s",
                 len(empty_cells) if empty_cells else 0, total_tools)

    if total_tools <= 0:
        raise HTTPException(status_code=400, detail="В чертеже не указаны инструменты или количество равно 0")
    if not empty_cells or len(empty_cells) == 0:
        logger.warning("[create_plan] Не хватает свободных ячеек: empty_cells=0, total_tools=%s", total_tools)
        raise HTTPException(status_code=400, detail="Не хватает свободных ячеек")

    # БЛОКИРОВАННЫЕ ЯЧЕЙКИ: первый столбец каждой строки (1, 36, 71, 106, 141, 176)
    BLOCKED_CELL_NUMBERS = {1, 36, 71, 106, 141, 176}

    # Симулируем логику цикла для точного подсчета необходимых ячеек
    # Каждая заблокированная ячейка требует дополнительную ячейку из списка
    cell_index = 0
    cells_needed = 0

    # Подсчитываем, сколько ячеек фактически понадобится
    for _ in range(total_tools):
        if cell_index >= len(empty_cells):
            # Недостаточно ячеек
            raise HTTPException(status_code=400, detail="Не хватает свободных ячеек")

        # Если текущая ячейка заблокирована, пропускаем её
        if empty_cells[cell_index].number in BLOCKED_CELL_NUMBERS:
            cell_index += 1
            cells_needed += 1  # Заблокированная ячейка требует дополнительную
            # Проверяем, что есть еще одна ячейка после заблокированной
            if cell_index >= len(empty_cells):
                raise HTTPException(status_code=400, detail="Не хватает свободных ячеек")

        cell_index += 1
        cells_needed += 1

    # Проверяем, достаточно ли ячеек с учетом заблокированных
    if cells_needed > len(empty_cells):
        logger.warning("[create_plan] Не хватает свободных ячеек: cells_needed=%s, len(empty_cells)=%s", cells_needed,
                       len(empty_cells))
        raise HTTPException(status_code=400, detail="Не хватает свободных ячеек")

    logger.debug("[create_plan] Достаточно ячеек: cells_needed=%s, приступаем к save_mass_load", cells_needed)

    try:
        # 5) создаём запись MassLoad
        mass_load_id = max(e_mass_load.get_all_ids(), default=0) + 1
        mass_load_status = e_status.find_by_name("mass_load_init")
        e_mass_load.add_mass_load(
            index=mass_load_id,
            status_id=mass_load_status.id,
            description=(
                f"Инициализирована новая массовая загрузка инструмента в аппарат "
                f"{device.name}, время: {datetime.datetime.now()}"
            ),
        )
        new_mass_load = e_mass_load.get_mass_load_by_id(mass_load_id)

        if not mass_load_status:
            idx = max(e_status.get_all_ids(), default=0) + 1
            e_status.add(index=idx, stype="mass_load_init",
                         description="Инициализирована массовая загрузка")
            mass_load_status = e_status.get_status_by_id(idx)
        status_load = e_status.find_by_name("mass_load_init")

        # Создаём связь MassLoad с Device для синхронизации и отображения в клиенте
        logger.debug("[save_mass_load] Создание связи MassLoadHasDevice: mass_load_id=%s, device_id=%s", mass_load_id, device_id)
        e_mass_load_has_device.add_link(mass_load_id=mass_load_id, device_id=device_id)
        logger.info("[save_mass_load] Связь MassLoadHasDevice создана успешно")


        total_operations = len(flat_stories)
        processed_count = 0
        failed_operations = []
        
        logger.debug("[save_mass_load] Начало обработки массовой загрузки. Всего операций: %s, device_id=%s, mass_load_id=%s",
                     total_operations, device_id, mass_load_id)

        cell_checked = 0
        cell_used = 0

        for key, story in flat_stories:
            print(f"create_plan key: {key}, story={story}")
            processed_count += 1
            operation_start_time = datetime.datetime.now()

            cell = empty_cells[cell_checked]
            print(f"check sell: {cell}")
            cell_checked += 1
            while cell.number in BLOCKED_CELL_NUMBERS:
                print(f"blocked")
                cell = empty_cells[cell_checked]
                cell_checked += 1
            cell_used += 1
            logger.debug(f"create_plan cell: {cell}")
            
            try:
                logger.debug("[save_mass_load] Обработка операции {}/{} (key={}): tool={}, plan={}".format(
                             processed_count, total_operations, key, story.tool, story.plan))
                
                # разбираем вход
                # print(f"save_mass_load story: {story}")
                request_cell = cell.id
                request_tool = story.tool
                request_plan = story.plan
                logger.debug("[save_mass_load][{}/{}] story.plan (сырое)={}".format(processed_count, total_operations, request_plan))

                if not request_plan or request_plan == "":
                    request_plan = None
                    logger.debug("[save_mass_load][{}/{}] plan_id сброшен: пустое значение".format(processed_count, total_operations))
                else:
                    plan = e_plan.get_plan_by_id(request_plan)
                    if not plan:
                        logger.warning("[save_mass_load][{}/{}] Plan id={} не найден в БД, plan_id будет null для History/Load".format(
                                       processed_count, total_operations, request_plan))
                        request_plan = None
                    else:
                        logger.debug("[save_mass_load][{}/{}] Plan id={} найден, plan_id передаётся в History и Load".format(
                                     processed_count, total_operations, request_plan))

                # print(f"request_cell: {request_cell}, request_tool: {request_tool}, request_plan: {request_plan}")

                # подбор типа инструмента по группе и имени
                # parts = request_tool.split(' ', 1)
                # if len(parts) == 2:
                #     group_name, tool_name = parts
                #     group_id = group_name_to_id.get(group_name)
                #     if group_id is None:
                #         raise HTTPException(status_code=404, detail=f"Группа '{group_name}' не найдена")
                #     tool_type = e_tool_types.find_by_name_and_group(tool_name, group_id)
                #     if not tool_type:
                #         raise HTTPException(status_code=404, detail=f"Инструмент '{tool_name}' не найден в группе '{group_name}'")
                # else:

                # tool_types = e_tool_types.find_by_name(request_tool)
                logger.debug("[save_mass_load][%s/%s] Получение tool_type для tool_id=%s".format(processed_count, total_operations, request_tool))
                tool_type = e_tool_types.get_tool_type_by_id(request_tool)
                if not tool_type:
                    error_msg = f"Подходящий инструмент '{request_tool}' не найден для операции {processed_count}/{total_operations}"
                    logger.error("[save_mass_load][%s/%s] %s", processed_count, total_operations, error_msg)
                    raise HTTPException(status_code=404, detail=error_msg)
                logger.debug("[save_mass_load][%s/%s] Tool_type найден: id=%s, name=%s".format(processed_count, total_operations, tool_type.id, tool_type.name))
                # tool_type = tool_types[0]

                # создаём History
                logger.debug("[save_mass_load][%s/%s] Создание History записи".format(processed_count, total_operations))
                story_id = max(e_stories.get_all_ids(), default=0) + 1
                story_ids.append(story_id)
                user = e_user.get_user_by_barcode(validation.user_barcode)
                if not user:
                    error_msg = f"Пользователь не найден для операции {processed_count}/{total_operations}"
                    logger.error("[save_mass_load][%s/%s] %s".format(processed_count, total_operations, error_msg))
                    raise HTTPException(status_code=402, detail=error_msg)
                logger.debug("[save_mass_load][%s/%s] Пользователь найден: id=%s, barcode=%s".format(processed_count, total_operations, user.id, validation.user_barcode))
                # print(f"add_history: {story_id}")
                logger.debug("[save_mass_load][%s/%s] add_history с plan_id=%s".format(processed_count, total_operations, request_plan))
                e_stories.add_history(
                    history_id=story_id,
                    user_id=user.id,
                    role_id=user.role_id,
                    tools_id=tool_type.id,
                    datetime_value=datetime.datetime.now(),
                    status=status_load.id,
                    description=status_load.description,
                    plan_id=request_plan,
                )
                new_history = e_stories.get_history_by_id(story_id)
                if not new_history:
                    error_msg = f"Не удалось получить History после добавления для операции {processed_count}/{total_operations}, story_id={story_id}"
                    logger.error("[save_mass_load][%s/%s] %s".format(processed_count, total_operations, error_msg))
                    raise HTTPException(status_code=500, detail=error_msg)
                logger.debug("[save_mass_load][%s/%s] History создана: id=%s".format(processed_count, total_operations, new_history.id))
                e_history_has_device.add_link(
                    history_id=new_history.id, device_id=device.id)

                # # выбираем конкретный инструмент
                # db_tools = e_tools.get_tools_by_tool_type(tool_type.id)
                # tool_to_load = next(
                #     (t for t in db_tools if not e_load.find_by_tools_id(t.id)), None)
                # if not tool_to_load:
                #     raise HTTPException(
                #         status_code=404, detail="Подходящий инструмент не найден")

                # получаем и обновляем cell
                # cell = e_cells.get_cell_by_number(int(request_cell))
                logger.debug("[save_mass_load][%s/%s] Получение ячейки cell_id=%s".format(processed_count, total_operations, request_cell))
                cell = e_cells.get_cell_by_id(int(request_cell))
                if not cell:
                    error_msg = f"Ячейка не найдена для операции {processed_count}/{total_operations}, cell_id={request_cell}"
                    logger.error("[save_mass_load][%s/%s] %s", processed_count, total_operations, error_msg)
                    raise HTTPException(status_code=404, detail=error_msg)
                logger.debug("[save_mass_load][%s/%s] Ячейка найдена: id=%s, number=%s".format(processed_count, total_operations, cell.id, cell.number))

                # # привязываем инструмент к устройству
                # e_tools_has_device.add_link(
                #     tools_id=tool_to_load.id, device_id=device.id)
                # if not e_tools_has_device.this_tool_is_linked(tool_to_load.id):
                #     raise HTTPException(
                #         status_code=500,
                #         detail=f"Связь инструмента ID={tool_to_load.id} с устройством не установлена",
                #     )

                # backup и обновление ячейки
                cell_backs.append(e_cells.get_cell_by_id(cell.id))
                logger.debug("[save_mass_load][%s/%s] update_cell: cell_id=%s, number=%s, tools_id=%s, groups_id=%s, e_cells.device_id=%s",
                             processed_count, total_operations, cell.id, cell.number, tool_type.id, tool_type.groups_id, getattr(e_cells, 'device_id', 'NOT SET'))
                e_cells.update_cell(
                    cell_id=cell.id,
                    number=cell.number,
                    description=f"Объявлена новая загрузка {new_mass_load.description}",
                    groups_id=tool_type.groups_id,
                    tools_id=tool_type.id,
                    status_id=mass_load_status.id,
                )
                logger.debug("[save_mass_load][%s/%s] update_cell выполнен успешно для cell_id=%s", processed_count, total_operations, cell.id)

                load_id = max(e_load.get_all_ids(), default=0) + 1
                logger.debug("[save_mass_load][%s/%s] Создание Load: load_id=%s, plan_id=%s", processed_count, total_operations, load_id, request_plan)
                # создаём Load
                e_load.add_load(
                    load_id=load_id,
                    description="",
                    tools_id=tool_type.id,
                    mass_load_id=new_mass_load.id,
                    cell_id=cell.id,
                    plan_id=request_plan,
                    history_id=new_history.id,
                    status_id=status_load.id
                )
                load = e_load.get_load_by_id(load_id)
                if not load:
                    error_msg = f"Не удалось получить Load после создания для операции {processed_count}/{total_operations}, load_id={load_id}"
                    logger.error("[save_mass_load][%s/%s] %s", processed_count, total_operations, error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                logger.debug("[save_mass_load][%s/%s] Load создан: id=%s", processed_count, total_operations, load.id)
                loads.append(load)

                # привязываем cell к устройству
                e_cell_has_device.add_link(cell_id=cell.id, device_id=device.id)

                # # создаём History
                # story_id = max(e_stories.get_all_ids(), default=0) + 1
                # story_ids.append(story_id)
                # user = e_user.get_user_by_barcode(validation.user_barcode)
                # if not user:
                #     raise HTTPException(
                #         status_code=402, detail="Пользователь не найден")
                # print(f"add_history: {story_id}")
                # e_stories.add_history(
                #     history_id=story_id,
                #     user_id=user.id,
                #     role_id=user.role_id,
                #     tools_id=tool_type.id,
                #     datetime_value=datetime.datetime.now(),
                #     status=status_load.id,
                #     description=status_load.description
                # )
                # new_history = e_stories.get_history_by_id(story_id)
                # if not new_history:
                #     raise HTTPException(
                #         status_code=500, detail="Не удалось получить History после добавления")

                # создаём LoadOperation и привязываем к устройству
                operation_id = max(e_load_operation.get_all_ids(), default=0) + 1
                operation_ids.append(operation_id)
                logger.debug("[save_mass_load][%s/%s] Создание LoadOperation: operation_id=%s", processed_count, total_operations, operation_id)
                e_load_operation.add_operation(
                    operation_id=operation_id,
                    date=datetime.datetime.now(),
                    load_id=load_id,
                    load_tools_id=tool_type.id,
                    status_id=status_load.id,
                    history_id=story_id,
                    description=status_load.description,
                )
                operation = e_load_operation.get_load_by_id(operation_id)
                if not operation:
                    error_msg = f"Не удалось получить Operation после добавления для операции {processed_count}/{total_operations}, operation_id={operation_id}"
                    logger.error("[save_mass_load][%s/%s] %s", processed_count, total_operations, error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)
                logger.debug("[save_mass_load][%s/%s] LoadOperation создан: id=%s", processed_count, total_operations, operation.id)
                e_operation_has_device.add_link(
                    load_operations_id=operation_id, device_id=device.id)
                
                operation_duration = (datetime.datetime.now() - operation_start_time).total_seconds()
                logger.debug("[save_mass_load][%s/%s] Операция завершена успешно за %s сек", processed_count, total_operations, f"{operation_duration:.3f}")
            
            except Exception as op_error:
                failed_operations.append({
                    "operation": processed_count,
                    "key": key,
                    "error": str(op_error),
                    "traceback": traceback.format_exc()
                })
                error_msg = (
                    f"ОШИБКА при обработке операции {processed_count}/{total_operations} (key={key}): {op_error}. "
                    f"cell={getattr(story, 'cell', 'N/A')}, tool={getattr(story, 'tool', 'N/A')}"
                )
                logger.error("[save_mass_load][%s/%s] %s", processed_count, total_operations, error_msg)
                logger.exception("[save_mass_load] Traceback для операции %s/%s", processed_count, total_operations)
                # Продолжаем обработку следующих операций, но запоминаем ошибку
                continue

        # Итоговая статистика
        successful_count = processed_count - len(failed_operations)
        logger.info("[save_mass_load] ИТОГИ: всего=%s, успешно=%s, ошибок=%s", total_operations, successful_count, len(failed_operations))
        if failed_operations:
            logger.warning("[save_mass_load] Список неудачных операций: %s", failed_operations)
            for failed in failed_operations:
                logger.warning("[save_mass_load] Операция %s (key=%s): %s", failed['operation'], failed['key'], failed['error'])
            # Если были ошибки, но не все операции провалились, возвращаем частичный успех
            if successful_count > 0:
                return {
                    "status": "partial",
                    "message": f"Обработано {successful_count} из {total_operations} операций",
                    "successful": successful_count,
                    "failed": len(failed_operations),
                    "errors": failed_operations
                }
        
        return {"status": "ok", "message": new_mass_load.description}

    except Exception as e:
        logger.exception("save_mass_load rollback: %s", e)
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
                # e_tools_has_device.delete_link(
                #     tools_id=ld.tools_id, device_id=device_id)
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
                e_mass_load_has_device.delete_link(mass_load_id=mass_load_id, device_id=device_id)
                e_mass_load.delete(mass_load_id)
        except Exception:
            logger.exception("save_mass_load rollback inner")
            pass

        raise HTTPException(
            status_code=500, detail=f"Не удалось сохранить массовую загрузку: {e}")
