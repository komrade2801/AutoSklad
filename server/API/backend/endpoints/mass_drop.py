import datetime
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request
# status,
from pydantic import BaseModel
# from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# from API.backend.endpoints.color_map import STATUS_COLORS
from Core.authorization import AuthService
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
from typing import Dict  # , Optional  # Добавлен Optional
# from collections import defaultdict
from fastapi.responses import RedirectResponse


# import json

auth_service = AuthService()
mass_drop_router = APIRouter(tags=["MassDrop"])


class History(BaseModel):
    cell: str
    tool: str
    plan: str


class MassDropCreate(BaseModel):
    operation: Dict[str, History]

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
        print(device_number)
        print(mass_drop)
        device = e_device.get_device_by_number(device_number)
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не обнаружено!")

        # e_plan = EnginePlan()
        e_tools = EngineTools()
        e_tool_types = EngineToolTypes()
        # e_group = EngineGroup()
        e_drop = EngineDrop()
        e_drop_operation = EngineDropOperations()
        e_operation_has_device = EngineDropOperationsHasDevice()
        e_mass_drop = EngineMassDrop()
        e_cells = EngineCell()
        e_cell_has_device = EngineCellHasDevice()
        e_stories = EngineHistory()
        e_status = EngineStatus()
        e_user = EngineUser()
        e_tools_has_device = EngineToolsHasDevice()
        stories = mass_drop.operation
        # mass_drop_id = None
        # new_mass_drop = None
        name_steps = 1
        try:
            mass_drop_id = max(e_mass_drop.get_all_ids(), default=0) + 1
            e_mass_drop.add_task(
                index=mass_drop_id,
                description=f"Инициализирована новая массовая выгрузка инструмента из аппарат {device.name}, "
                            f"время: {datetime.datetime.now()}"
            )

            new_mass_drop = e_mass_drop.get_task(task_id=mass_drop_id)
            for story, key in enumerate(stories):
                request_cell = stories[key].cell
                request_tool = stories[key].tool
                # request_plan = stories[key].plan
                tool_names = request_tool.split(" ")

                tool_type = None
                tool_types = None
                tool_name = ""
                for name in tool_names:
                    if not tool_name:
                        tool_name = name
                    tool_types = e_tool_types.find_by_name(tool_name)
                    if tool_types:
                        break
                    if name not in tool_name:
                        tool_name = tool_name + " " + name
                        name_steps += 1

                if not tool_types:
                    raise HTTPException(status_code=404, detail="Подходящий инструмент не найден")
                for tool_type_iteration in tool_types:
                    if len(tool_names) <= name_steps:
                        name_steps -= 1
                    if tool_names[name_steps] in tool_type_iteration.description or tool_names[name_steps] in tool_type_iteration.name:
                        tool_type = tool_type_iteration
                        break
                if not tool_type:
                    raise HTTPException(status_code=404, detail="Подходящий инструмент не найден")

                e_tool_types.update_tool_type(
                    tool_type_id=tool_type.id,
                    name=tool_type.name,
                    description=tool_type.description,
                    count=tool_type.count - 1,
                    img=tool_type.img,
                    groups_id=tool_type.groups_id,
                )

                db_tools = e_tools.get_tools_by_tool_type(tool_type.id)
                drop_id = max(e_drop.get_all_ids(), default=0) + 1
                tool_to_drop = None
                for tool in db_tools:
                    drop = e_drop.get_by_tools_id(tool.id)
                    if not drop:
                        tool_to_drop = tool
                        break
                if not tool_to_drop:
                    raise HTTPException(status_code=404, detail="Подходящий инструмент не найден")
                cell = e_cells.get_cell_by_number(int(request_cell))
                if not cell:
                    raise HTTPException(status_code=404, detail="Система не инициирована")

                mass_drop_status = e_status.find_by_name("mass_drop_init")

                if not mass_drop_status:
                    index = max(e_status.get_all_ids(), default=0) + 1
                    e_status.add(
                        index=index,
                        stype="mass_drop_init",
                        description="Объявлена массовая загрузка"
                    )

                status_drop = e_status.find_by_name("mass_drop_init")

                if not status_drop:
                    index = max(e_status.get_all_ids(), default=0)
                    e_status.add(
                        index=index + 1,
                        stype="mass_drop_init",
                        description="Инициализирована массовая загрузка"
                    )
                    status_drop = e_status.get_status_by_id(status_id=index)

                e_tools_has_device.unlink_tool_from_device(
                    tools_id=tool_to_drop.id,
                    device_id=device.id,
                )

                e_cells.update_cell(
                    cell_id=cell.id,
                    number=cell.number,
                    description=f"Старт",
                    groups_id=0,
                    tools_id=0,
                    status_id=0,
                )

                e_drop.add_drop(
                    index=drop_id,
                    created_at=datetime.datetime.now(),
                    cell_id=cell.id,
                    mass_drop_id=new_mass_drop.id,
                    tools_id=tool_to_drop.id,
                    description=""
                )

                # e_cell_has_device.add_link(
                #     cell_id=cell.id,
                #     device_id=device.id,
                # )

                story_id = max(e_stories.get_all_ids(), default=0) + 1
                bardcode = validation.user_barcode
                user = e_user.get_user_by_barcode(bardcode)

                if not user:
                    raise HTTPException(status_code=402, detail="Пользователь не найден")

                e_stories.add_history(
                    history_id=story_id,
                    user_id=user.id,
                    role_id=user.role_id,
                    tools_id=tool_to_drop.id,
                    datetime_value=datetime.datetime.now(),
                    status=0,
                    description=f"Массовая выгрузка инициирована",
                )

                operation_id = max(e_drop_operation.get_all_ids(), default=0) + 1

                e_drop_operation.add_operation(
                    index=operation_id,
                    drop_id=drop_id,
                    tools_id=tool_to_drop.id,
                    status_id=status_drop.id,
                    history_id=story_id,
                    description="",
                )
                e_operation_has_device.add_link(
                    drop_operations_id=operation_id,
                    device_id=device.id,
                )

            return {"status": "ok", "message": new_mass_drop.description}
        except Exception as e:
            # TODO реализовать откат данных, если что-то пошло не так
            print(e)
            print(traceback.format_exc())
            raise HTTPException(status_code=404, detail=f"Всё плохо{e}")
        finally:
            pass
