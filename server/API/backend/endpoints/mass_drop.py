import datetime
import traceback

from Core.app_logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Request

logger = get_logger(__name__)
# status,
from pydantic import BaseModel
# from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# from API.backend.endpoints.color_map import STATUS_COLORS
from Core.authorization import AuthService
from DB.Engine.HistoryHasDeviceCRUD import EngineHistoryHasDevice
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.PlanCRUD import EnginePlan
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.DropOperationsHasDeviceCRUD import EngineDropOperationsHasDevice
# from DB.Engine.MassDropCRUD import EngineMassDrop
# from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.ToolsCRUD import EngineTools
# from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.DropOperationsCRUD import EngineDropOperations 
from DB.Engine.MassDropCRUD import EngineMassDrop
from typing import Dict, List  # , Optional  # Добавлен Optional
# from collections import defaultdict
from fastapi.responses import RedirectResponse


# import json

auth_service = AuthService()
mass_drop_router = APIRouter(tags=["MassDrop"])


class History(BaseModel):
    cell: str
    # number: str
    # tool: str
    # plan: str


class MassDropCreate(BaseModel):
    operation: List[History]

@mass_drop_router.post("/mass_drop_tools/{device_number}")
def save_mass_drop(request: Request, device_number: int, mass_drop: MassDropCreate, db: Session = Depends(get_db)):
    validation = auth_service.validation_user(request)
    if isinstance(validation, RedirectResponse):
        raise HTTPException(status_code=402, detail="Неавторизованный доступ запрещён")
    if "status" in validation:
        raise HTTPException(status_code=402, detail="Неавторизованный доступ запрещён")
    elif isinstance(validation, RedirectResponse):
        raise HTTPException(status_code=402, detail="Неавторизованный доступ запрещён")
    else:
        e_device = EngineDevice()
        logger.debug("device_number: %s, mass_drop: {}".format(device_number, mass_drop))
        device = e_device.get_device_by_number(device_number)
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не обнаружено!")

        e_plan = EnginePlan()
        # e_tools = EngineTools()
        e_tool_types = EngineToolTypes()
        # e_group = EngineGroup()
        e_load = EngineLoad()
        e_drop = EngineDrop()
        e_drop_operation = EngineDropOperations()
        # e_operation_has_device = EngineDropOperationsHasDevice()
        e_history_has_device = EngineHistoryHasDevice()
        e_mass_drop = EngineMassDrop()
        e_cells = EngineCell()
        # e_cell_has_device = EngineCellHasDevice()
        e_stories = EngineHistory()
        e_status = EngineStatus()
        e_user = EngineUser()

        stories = mass_drop.operation

        barcode = validation.user_barcode
        user = e_user.get_user_by_barcode(barcode)

        if not user:
            raise HTTPException(status_code=402, detail="Пользователь не найден")

        result = True

        try:
            mass_drop_id = max(e_mass_drop.get_all_ids(), default=0) + 1
            e_mass_drop.add_task(
                index=mass_drop_id,
                created_at=datetime.datetime.now(),
                description=f"Инициализирована новая массовая выгрузка инструмента из аппарат {device.name}, "
                            f"время: {datetime.datetime.now()}"
            )

            new_mass_drop = e_mass_drop.get_task(task_id=mass_drop_id)
            logger.debug("stories: {}".format(stories))
            for story in stories:
                logger.debug("story: {}".format(story))
                request_cell_id = story.cell
                logger.debug("request_cell: {}".format(request_cell_id))
                cell = e_cells.get_cell_by_id(int(request_cell_id))
                logger.debug("cell: {}".format(cell))
                tool_type = e_tool_types.get_tool_type_by_id(cell.tools_id)
                logger.debug("tool_type: {}".format(tool_type))

                loads = e_load.find_by_cell_id(cell.id)
                logger.debug("loads: {}".format(loads))

                if loads:
                    load = max(loads, key=lambda rec: rec.id)
                    logger.debug("load: {}".format(load))

                    plan = e_plan.get_plan_by_id(load.plan_id)

                    plan_id = None

                    if plan:
                        plan_id = plan.id

                    drop_id = max(e_drop.get_all_ids(), default=0) + 1

                    mass_drop_status = e_status.find_by_name("mass_drop_init")

                    if not mass_drop_status:
                        index = max(e_status.get_all_ids(), default=0) + 1
                        e_status.add(
                            index=index,
                            stype="mass_drop_init",
                            description="Объявлена массовая загрузка"
                        )
                        mass_drop_status = e_status.get_status_by_id(status_id=index)

                    e_cells.update_cell(
                        cell_id=cell.id,
                        groups_id=cell.groups_id,
                        tools_id=cell.tools_id,
                        description=mass_drop_status.description,
                        status_id=mass_drop_status.id
                    )

                    history_id = max(e_stories.get_all_ids()) + 1
                    result = result and e_stories.add_history(
                        user_id=user.id,
                        role_id=user.role_id,
                        tools_id=tool_type.id,
                        datetime_value=datetime.datetime.now(),
                        status=mass_drop_status.id,
                        description=mass_drop_status.description,
                        plan_id=plan_id,
                        history_id=history_id
                    )
                    logger.debug("history_id: %s, result: {}".format(history_id, result))

                    e_drop.add_drop(
                        history_id=history_id,
                        index=drop_id,
                        created_at=datetime.datetime.now(),
                        cell_id=cell.id,
                        mass_drop_id=new_mass_drop.id,
                        tools_id=tool_type.id,
                        status_id=mass_drop_status.id,
                        description=mass_drop_status.description,
                        plan_id=plan_id
                    )

                    operation_id = max(e_drop_operation.get_all_ids(), default=0) + 1

                    e_drop_operation.add_operation(
                        index=operation_id,
                        drop_id=drop_id,
                        tools_id=tool_type.id,
                        status_id=mass_drop_status.id,
                        history_id=history_id,
                        description="",
                    )
                    e_history_has_device.add_link(
                        history_id=history_id,
                        device_id=device.id,
                    )

            return {"status": "ok", "message": new_mass_drop.description}
        except Exception as e:
            # TODO реализовать откат данных, если что-то пошло не так
            logger.exception("save_mass_drop: {}".format(e))
            raise HTTPException(status_code=404, detail=f"Всё плохо{e}")
        finally:
            pass
