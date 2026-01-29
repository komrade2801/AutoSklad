# from typing import List
import random
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from Core.authorization import AuthService
from DB.Engine.CellCRUD import EngineCell
from API.backend.endpoints.mass_load import save_mass_load, MassLoadCreate, History
# from typing import List

from API.backend.request_models import PlanResponse, Plan, PlanCreate, PlanUpdate, PlanAddResponse, PlanCreateRequest
# # from DB.Data.db_depends import get_db
# from DB.session import get_db
from DB.session import get_db
# from DB.session import get_db
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.ToolTypesCRUD import EngineToolTypes
# from DB.Engine.ToolsCRUD import EngineTools
# from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.PlanToolTypesCRUD import EnginePlanToolTypes
# from fastapi.responses import StreamingResponse
# from io import BytesIO
# from PIL import Image, ImageDraw, ImageFont
# from barcode.codex import Code128
# from barcode import get_barcode_class
# from barcode.writer import ImageWriter
from barcode.codex import Code128
from barcode.writer import ImageWriter
from io import BytesIO
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

auth_service = AuthService()

all_plans_router = APIRouter(tags=["All Plans"])


@all_plans_router.get("/get_all_plans/{device_number}", response_model=PlanResponse)
def get_all_plans(device_number: int, db: Session = Depends(get_db)):
    print(f"get_all_plans Device number: {device_number}")
    """
    Получает чертежи для устройства по серийному номеру.
    Связь реализуется через таблицу Tools: выбираем инструменты устройства и собираем уникальные plan_id.
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    # tools_crud = EngineTools()
    plans_crud = EnginePlan()
    tool_types_crud = EngineToolTypes()
    plan_tool_types_crud = EnginePlanToolTypes()

    # device = devices_crud.get_device_by_number(device_number)
    # if not device:
    #     raise HTTPException(status_code=404, detail="Устройство не найдено")
    #
    # tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    # if not tool_ids:
    #     raise HTTPException(status_code=404, detail="Нет инструментов, связанных с данным устройством")
    #
    # tools = tools_crud.get_tools_by_ids(tool_ids)
    # if not tools:
    #     raise HTTPException(status_code=404, detail="Инструменты не найдены")
    #
    # # Собираем уникальные идентификаторы Чертёжов из инструментов
    # plan_ids = list({tool.plan_id for tool in tools if tool.plan_id is not None})
    # if not plan_ids:
    #     raise HTTPException(status_code=200, detail="Чертёжы для данного устройства не найдены")
    #
    # plans = plans_crud.get_plans_by_ids(plan_ids)

    plans = plans_crud.get_all_plans()
    print(f"plans: {plans}")
    if not plans:
        raise HTTPException(status_code=404, detail="Чертёжы не найдены")
    plan_dicts = {}
    plan_list = []

    for plan in plans:
        tool_by_plan = {}
        tools_by_plan = []
        plan_dicts["id"] = plan.id
        plan_dicts["enterprise"] = plan.enterprise
        plan_dicts["barcode"] = plan.barcode
        plan_dicts["name"] = plan.name
        plan_dicts["description"] = plan.description
        plan_dicts["designation"] = plan.designation
        plan_dicts["index_list"] = plan.index_list
        plan_dicts["list_count"] = plan.list_count
        plan_dicts["parent_plan_id"] = plan.parent_plan_id
        plan_dicts["parent_plan"] = plan.parent_plan
        # tools = tools_crud.get_tools_by_plan(plan.id)
        plan_tool_types = plan_tool_types_crud.get_plan_tool_types_by_plan_id(plan.id)
        print(f"plan: {plan}, plan_tool_types: {plan_tool_types}")
        for plan_tool_type in plan_tool_types:
            tool_type = tool_types_crud.get_tool_type_by_id(tool_type_id=plan_tool_type.tool_types_id)
            print(f"tool_type: {tool_type}")

            tool_by_plan["id"] = tool_type.id
            # tool_by_plan["barcode"] = tool_type.barcode
            tool_by_plan["name"] = tool_type.name
            tool_by_plan["description"] = tool_type.description
            tool_by_plan["img"] = tool_type.img
            tool_by_plan["plan_id"] = plan.id
            tool_by_plan["groups_id"] = tool_type.groups_id
            tool_by_plan["tool_types_count"] = plan_tool_type.tool_types_count
            tools_by_plan.append(tool_by_plan)
            tool_by_plan = {}
        plan_dicts["tools"] = tools_by_plan
        plan_list.append(plan_dicts)
        plan_dicts = {}

    return PlanResponse(plans=plan_list)



@all_plans_router.get(
    "/plan_barcode",
    responses={200: {"content": {"image/png": {}}}},
    response_class=StreamingResponse,
)
def plan_barcode(barcode_index: str, db: Session = Depends(get_db)):
    e_plan = EnginePlan()
    plan = e_plan.get_plan_by_barcode(barcode=barcode_index)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # 1) Генерируем штрих-код как PIL.Image
    data = str(plan.barcode)
    barcode_obj = Code128(data, writer=ImageWriter())
    # вместо .write(buf) используем .render()
    code_img: Image.Image = barcode_obj.render()
    w, h = code_img.size

    # 2) Дорисовываем текст
    padding = 40
    canvas = Image.new("RGBA", (w, h + padding), "WHITE")
    canvas.paste(code_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    # путь к шрифту с поддержкой кириллицы

    try:
        # Попробуем системный шрифт
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except (OSError, IOError):
        # Аварийно — встроенный bitmap-шрифт
        try:
            # Windows
            font = ImageFont.truetype("arial.ttf", 32)
        except (OSError, IOError):
            # Ничего другого не нашли — используем дефолт (без контроля размера)
            font = ImageFont.load_default()

    text = plan.designation or ""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - text_w) // 2
    y = h + (padding - text_h) // 2
    draw.text((x, y), text, fill="black", font=font)

    # 3) Сохраняем в BytesIO и возвращаем
    out_buf = BytesIO()
    canvas.convert("RGB").save(out_buf, format="PNG")
    out_buf.seek(0)
    return StreamingResponse(out_buf, media_type="image/png")


# @all_plans_router.get(
#     "/plan_barcode",
#     responses={200: {"content": {"image/png": {}}}},
#     response_class=StreamingResponse,
# )
# def plan_barcode(barcode_index:str, db: Session = Depends(get_db)):
#     # 1. Получаем пользователя
#     e_plan = EnginePlan()
#     plan = e_plan.get_plan_by_barcode(
#         barcode=barcode_index
#     )
#     if not plan:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     # 2. Генерируем штрих‑код в памяти
#     data = str(plan.barcode)
#     CODE = barcode.get_barcode_class('code128')
#     barcode_obj = CODE(data, writer=ImageWriter())
#     buf = BytesIO()
#     barcode_obj.write(buf)
#     buf.seek(0)
#
#     # 3. Открываем как PIL
#     code_img = Image.open(buf).convert("RGBA")
#     w, h = code_img.size
#
#     # 4. Создаём холст с запасом по высоте
#     padding = 40
#     canvas = Image.new("RGBA", (w, h + padding), "WHITE")
#     canvas.paste(code_img, (0, 0))
#
#     # 5. Рисуем русское имя и фамилию размером 14pt
#     draw = ImageDraw.Draw(canvas)
#
#     # Указываем путь к TTF‑шрифту, поддерживающему кириллицу.
#     # На Windows обычно доступен Arial, на Linux можно поставить DejaVuSans.
#     font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
#     font = ImageFont.truetype(font_path, 32)
#
#     text = plan.designation
#     # Используем textbbox для размера
#     bbox = draw.textbbox((0, 0), text, font=font)
#     text_w = bbox[2] - bbox[0]
#     text_h = bbox[3] - bbox[1]
#
#     x = (w - text_w) // 2
#     y = h + (padding - text_h) // 2
#     draw.text((x, y), text, fill="black", font=font)
#
#     # 6. Сохраняем в буфер и возвращаем
#     out_buf = BytesIO()
#     canvas.convert("RGB").save(out_buf, format="PNG")
#     out_buf.seek(0)
#     return StreamingResponse(out_buf, media_type="image/png")


@all_plans_router.post(
    "/create_plan/{device_number}",
    response_model=PlanAddResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"description": "Ошибка при добавлении чертежа"}}
)
def create_plan(
    request: Request,
    device_number: int,
    plan_request: PlanCreateRequest, db: Session = Depends(get_db)):
    """
    Создает новые чертежи. Поскольку прямой связи между Plan и Device нет,
    создание Чертёжа осуществляется независимо, а привязка к устройству может быть реализована
    на уровне инструмента (через поле plan_id в Tools).
    """
    print(f"create_plan. request: {request}, Device number: {device_number}, plan_request: {plan_request}")
    plan = plan_request.plan
    create_mass_load = plan_request.create_mass_load

    devices_crud = EngineDevice()
    plans_crud = EnginePlan()
    plan_tool_types_crud = EnginePlanToolTypes()
    cells_crud = EngineCell()
    # tools_has_device_crud = EngineToolsHasDevice()
    # tools_crud = EngineTools()
    tool_types_crud = EngineToolTypes()
    device = devices_crud.get_device_by_number(device_number)
    tool_ids = []
    plan_id = None
    __exception = False
    __e = None

    # 1) авторизация
    validation = auth_service.validation_user(request)
    if isinstance(validation, RedirectResponse) or ("status" in getattr(validation, "data", {})):
        raise HTTPException(
            status_code=401, detail="Неавторизованный доступ запрещён")

    try:
        validation.user_barcode
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=401, detail="Неавторизованный доступ запрещён")

    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    try:

        active_plan = plans_crud.get_plan_by_designation(plan.designation)

        if not active_plan:
            # created_plans = []
            # for plan in plan_data.plans:
            plan_id = max(plans_crud.get_all_ids(), default=0) + 1
            if not plan.barcode:
                plan.barcode = random.randint(111111111, 999999999)
            result = plans_crud.add_plan(
                index=plan_id,
                enterprise=plan.enterprise,
                barcode=plan.barcode,
                name=plan.name,
                description=plan.description,
                designation=plan.designation,
                index_list=plan.index_list,
                list_count=plan.list_count,
                parent_plan=plan.parent_plan,
                parent_plan_id=plan.parent_plan_id,
            )
        else:
            plan_id = active_plan.id
        # tools_has_device_crud

        for idx, tool in enumerate(plan.tools):
            # tool[""]
            # tool_types_name = name['name'].split(' ')[0]
            tool_types_id = tool['id']
            tool_types_name = tool['name']
            tool_quantity = tool['quantity']
            quantity = 0
            tool_type = tool_types_crud.get_tool_type_by_id(tool_types_id)
            print(f"create_plan tool_types_name: {tool_types_name}, tool_quantity: {tool_quantity}, tool_types_id: {tool_types_id}")
            # tool_types_ids = tool_types_crud.get_all_ids()
            # for index in tool_types_ids:
            #     tool_types = tool_types_crud.get_tool_type_by_id(tool_type_id=index)
            #     if tool_types.name in tool_types_name:

            print(f"create_plan tool_type: {tool_type}")

            plan_tool_types_crud_id = max(plan_tool_types_crud.get_all_ids(), default=0) + 1

            plan_tool_types_crud.create_plan_tool_types(plan_tool_types_crud_id, tool_type.id, tool_quantity, plan_id)

        print(f"create_plan create_mass_load: {create_mass_load}")
        if create_mass_load:
            empty_cells = cells_crud.get_all_empty_cells()
            total_tools = 0

            print(f"create_plan empty_cells: {empty_cells}")

            for tool in plan.tools:
                total_tools += tool['quantity']

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
                raise HTTPException(status_code=400, detail="Не хватает свободных ячеек")

            operation = {}
            number = 1
            cell_checked = 0
            cell_used = 0
            for tool in plan.tools:
                for count in range(tool['quantity']):
                    print(f"create_plan tool: {tool}, cell_used: {cell_checked}")
                    cell = empty_cells[cell_checked]
                    cell_checked += 1
                    if cell.number in BLOCKED_CELL_NUMBERS:
                        cell = empty_cells[cell_checked]
                        cell_checked += 1
                    cell_used += 1
                    print(f"create_plan cell: {cell}")
                    load_operation = History(cell=cell.id, tool=tool['id'], plan=plan_id)
                    # load_operation['toolId'] = tool['id']

                    operation[str(number)] = load_operation

                    number += 1
            mass_load = MassLoadCreate(operation = operation)

            print(f"create_plan mass_load: {mass_load}")
            save_mass_load(request, device_number, mass_load)

        return PlanAddResponse(status=200, message="Чертежи успешно добавлены")


                # links = tools_has_device_crud.get_tools_by_device_id(device.id)
                # for __tool in tools:
                #     if __tool.id in links:
                #         continue
                    # if not __tool.plan_id:
                    #     if quantity <= tool_quantity:
                    #         tools_crud.update_tool(
                    #             tool_id=__tool.id,
                    #             inventory_number=__tool.inventory_number,
                    #             plan_id=plan_id,
                    #             tool_type_id=__tool.tool_type_id,
                    #         )
                    #         tool_ids.append(__tool.id)
                    #         tools_has_device_crud.add_link(
                    #             tools_id=__tool.id,
                    #             device_id=device.id
                    #         )
                    #         quantity += 1
                    #         tool_types_crud.update_tool_type(
                    #             tool_type_id=tool_type.id,
                    #             name=tool_type.name,
                    #             description=tool_type.description,
                    #             count=tool_type.count - quantity,
                    #             img=tool_type.img,
                    #             groups_id=tool_type.groups_id,
                    #         )

        if not result:
            raise HTTPException(status_code=400, detail="Не удалось создать Чертёж")
        # created_plans.append(new_plan)

        return HTTPException(status_code=200, detail="Чертёж успешно создать")
    except Exception as err:
        print(f"err: {err}")
        __exception = True
        __e = err
        print(traceback.format_exc())
    finally:
        print(f"__exception: {__exception}")
        if __exception:

            plan_tool_types = plan_tool_types_crud.get_plan_tool_types_by_plan_id(plan.id)

            for plan_tool_type in plan_tool_types:
                plan_tool_types_crud.delete_plan_tool_types(plan_tool_type.id)

            plans_crud.delete_plan(plan.id)

            raise HTTPException(status_code=301, detail=__e)
        else:
            return PlanAddResponse(status=200, message="Чертежи успешно добавлены")


@all_plans_router.put("/update_plan/{device_number}/{plan_id}", response_model=Plan)
def update_plan(device_number: int, plan_id: int, plan_data: PlanUpdate, db: Session = Depends(get_db)):
    """
    Обновляет Чертёж, предварительно проверив, что хотя бы один из инструментов данного устройства
    связан с этим Чертёжом (то есть, у инструмента поле plan_id равно plan_id).
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    # tools_crud = EngineTools()
    plans_crud = EnginePlan()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    # if not tool_ids:
    #     raise HTTPException(status_code=404, detail="Нет инструментов, связанных с данным устройством")
    #
    # tools = tools_crud.get_tools_by_ids(tool_ids)
    # if not any(tool.plan_id == plan_id for tool in tools):
    #     raise HTTPException(status_code=403, detail="Чертёж не связан с данным устройством")

    updated_plan = plans_crud.update_plan_from_data(plan_id, plan_data)
    if not updated_plan:
        raise HTTPException(status_code=404, detail="Чертёж не найден")
    return updated_plan


@all_plans_router.delete("/delete_plan/{device_number}/{plan_id}")
def delete_plan(device_number: int, plan_id: int, db: Session = Depends(get_db)):
    """
    Удаляет Чертёж, предварительно проверив, что он связан с устройством (через наличие plan_id в инструментах устройства).
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    # tools_crud = EngineTools()
    plans_crud = EnginePlan()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    # if not tool_ids:
    #     raise HTTPException(status_code=404, detail="Нет инструментов, связанных с данным устройством")
    #
    # tools = tools_crud.get_tools_by_ids(tool_ids)
    # if not any(tool.plan_id == plan_id for tool in tools):
    #     raise HTTPException(status_code=403, detail="Чертёж не связан с данным устройством")

    deleted = plans_crud.delete_plan(plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Чертёж не найден")
    return {"message": "Чертёж успешно удален"}
