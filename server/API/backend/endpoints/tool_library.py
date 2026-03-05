from __future__ import annotations

import json
import threading
import uuid
from io import BytesIO
# from fastapi.responses import JSONResponse
from Core.app_logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File  # , Body, Form

logger = get_logger(__name__)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import pandas as pd
from starlette import status

from API.backend.request_models import (
    ToolLibraryResponse,  # Pydantic-модель для ответа: { "groups": { ... } }
    ToolLibrary,  # Модель инструмента (ответ при создании/обновлении)
    ToolLibraryCreate,  # Модель для создания записи
    ToolLibraryUpdate, ToolsImportResponse,
    UploadAcceptedResponse, ImportStatusResponse,
)
# , DEFAULT_FIELD_MAP
from API.backend.upload.config import update_field_map, load_field_map
from API.backend.upload.mappers import normalize_record, is_empty_row
from dbSync.Logic_v2.CommandQueue import INBOUND_QUEUES, PRIORITY_QUEUES

# from DB.Data.db_depends import get_db
from DB.session import get_db, get_db_session
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

# Импорт в потоке синхронизации: хранилище задач и лок
_import_jobs: Dict[str, Dict[str, Any]] = {}
_import_jobs_lock = threading.Lock()

IMPORT_BATCH_SIZE = 100  # батчинг: yield каждые N строк для обработки очереди "local" и _save_queue


def set_import_job_failed(job_id: str, error: str) -> None:
    """Устанавливает статус задачи импорта в failed (вызов из Runner при исключении)."""
    with _import_jobs_lock:
        if job_id in _import_jobs:
            _import_jobs[job_id]["status"] = "failed"
            _import_jobs[job_id]["error"] = error


def run_import_sync(
    job_id: str,
    data: bytes,
    use_count: bool,
    columns_map: Optional[str],
    total_sheets: int,
):
    """
    Генератор: выполняет импорт Excel в потоке Runner.
    Yield каждые IMPORT_BATCH_SIZE обработанных строк — Runner обрабатывает батч "local" и вызывает _save_queue.
    По завершении обновляет _import_jobs[job_id].
    """
    with _import_jobs_lock:
        if job_id not in _import_jobs:
            return
        _import_jobs[job_id]["status"] = "running"
    db = get_db_session()
    try:
        field_map = load_field_map()
        if columns_map:
            try:
                cm_dict = json.loads(columns_map)
                if isinstance(cm_dict, dict):
                    update_field_map(cm_dict)
                    field_map = load_field_map()
            except json.JSONDecodeError:
                pass

        xl = pd.ExcelFile(BytesIO(data))
        e_group = EngineGroup(session=db)
        e_tool_types = EngineToolTypes(session=db)

        processed = 0
        repeated = 0
        errors = []
        tool_type_counts = {}
        last_seen = {k: None for k in field_map.keys()}
        row_idx = 0
        batch_count = 0

        for sheet_name in xl.sheet_names:
            queue_in = INBOUND_QUEUES.get(1)
            if queue_in:
                try:
                    queue_in.put({"type": "sheet_batch_start"})
                except Exception as ex:
                    logger.warning("upload_xlsx sheet_batch_start: %s", ex)

            df = pd.read_excel(xl, sheet_name=sheet_name, keep_default_na=False)
            df = df.replace({pd.NA: ''})
            sheet_records = df.to_dict(orient="records")
            del df

            grp = e_group.find(name=sheet_name, description="")
            if grp is None:
                errors.append({"sheet": sheet_name, "error": "Группа по имени листа не найдена"})
                logger.warning("upload_xlsx sheet %s: group not found", sheet_name)
                if queue_in:
                    try:
                        queue_in.put({"type": "sheet_batch_end"})
                    except Exception as ex:
                        logger.warning("upload_xlsx sheet_batch_end: %s", ex)
                continue
            grp_id = grp.id

            for rec in sheet_records:
                rec["Название группы"] = sheet_name
                if is_empty_row(rec, field_map):
                    continue
                row_idx += 1
                idx = row_idx
                try:
                    norm, last_seen = normalize_record(rec, REQUIRED, field_map, last_seen)
                    tool_types_name = norm.get("tool_types_name")
                    if not tool_types_name or (isinstance(tool_types_name, str) and not tool_types_name.strip()):
                        errors.append({"row": idx, "error": "Отсутствует название инструмента (номенклатура)"})
                        continue
                    tt = e_tool_types.find_by_name(name=tool_types_name)
                    tool_type = None
                    if not tt:
                        tool_type_id = max(e_tool_types.get_all_ids(), default=0) + 1
                        ok = e_tool_types.add_tool_type(
                            tool_type_id=tool_type_id,
                            name=tool_types_name,
                            description=norm.get("tool_types_description") or "",
                            count=0,
                            img=norm.get("tool_types_img") or "",
                            groups_id=grp_id
                        )
                        tool_type = e_tool_types.get_tool_type_by_id(tool_type_id) if ok else None
                    else:
                        tool_type = tt[0]
                        repeated += 1
                    if tool_type is None:
                        errors.append({"row": idx, "error": "Не удалось создать или найти тип инструмента (номенклатуру)"})
                        continue
                    count = 0
                    if use_count:
                        count = norm.get("tool_types_count") or 1
                    if tool_type.id in tool_type_counts:
                        tool_type_counts[tool_type.id] = tool_type_counts[tool_type.id] + count
                    else:
                        tool_type_counts[tool_type.id] = count
                    processed += 1
                    batch_count += 1
                    if batch_count >= IMPORT_BATCH_SIZE:
                        batch_count = 0
                        yield
                except (ValueError, SQLAlchemyError, AttributeError) as e:
                    db.rollback()
                    errors.append({"row": idx, "error": str(e)})

            if queue_in:
                try:
                    queue_in.put({"type": "sheet_batch_end"})
                except Exception as ex:
                    logger.warning("upload_xlsx sheet_batch_end: %s", ex)

        errors_total = len(errors)
        if tool_type_counts:
            for id, count in tool_type_counts.items():
                tool_type = e_tool_types.get_tool_type_by_id(id)
                if tool_type:
                    e_tool_types.update_tool_type(
                        id=tool_type.id,
                        name=tool_type.name,
                        description=tool_type.description,
                        count=tool_type.count + count,
                        img=tool_type.img,
                        groups_id=tool_type.groups_id,
                    )

        result = {
            "processed": processed,
            "repeated": repeated,
            "errors": errors[:10],
            "errors_total": errors_total,
            "field_map": field_map,
            "total_sheets": total_sheets,
            "total_records": row_idx,
        }
        with _import_jobs_lock:
            if job_id in _import_jobs:
                _import_jobs[job_id]["status"] = "completed"
                _import_jobs[job_id]["result"] = result
        logger.info("upload_xlsx (sync thread): записей: %s, обработано: %s, повторов: %s, ошибок: %s",
                    row_idx, processed, repeated, errors_total)
    except Exception as e:
        logger.exception("upload_xlsx (sync thread) failed: %s", e)
        with _import_jobs_lock:
            if job_id in _import_jobs:
                _import_jobs[job_id]["status"] = "failed"
                _import_jobs[job_id]["error"] = str(e)
    finally:
        db.close()


@tool_library_router.post(
    "/upload",
    response_model=None,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Импорт запущен в фоне"},
        422: {"description": "Ошибка валидации файла"},
    })
async def upload_xlsx(
        file: UploadFile = File(...),
        use_count: bool = False,
        columns_map: Optional[str] = Form(
            None, description="JSON‑строка с дополнительным маппингом"),
):
    """Принимает файл, ставит импорт в приоритетную очередь потока синхронизации, возвращает job_id для опроса статуса."""
    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(422, f"Cannot read file: {e}")
    try:
        xl = pd.ExcelFile(BytesIO(data))
    except Exception as e:
        raise HTTPException(422, f"Cannot parse Excel: {e}")
    total_sheets = len(xl.sheet_names)
    logger.info("upload_xlsx: файл принят, листов: %s, постановка в приоритетную очередь", total_sheets)

    job_id = str(uuid.uuid4())
    with _import_jobs_lock:
        _import_jobs[job_id] = {"status": "pending", "result": None, "error": None}

    queue_in = PRIORITY_QUEUES.get(1) or INBOUND_QUEUES.get(1)
    if queue_in:
        try:
            queue_in.put({
                "type": "import_start",
                "job_id": job_id,
                "data": data,
                "use_count": use_count,
                "columns_map": columns_map,
                "total_sheets": total_sheets,
            })
        except Exception as ex:
            logger.warning("upload_xlsx: не удалось поставить import_start: %s", ex)
            with _import_jobs_lock:
                if job_id in _import_jobs:
                    _import_jobs[job_id]["status"] = "failed"
                    _import_jobs[job_id]["error"] = str(ex)
            raise HTTPException(503, "Очередь синхронизации недоступна")
    else:
        with _import_jobs_lock:
            if job_id in _import_jobs:
                _import_jobs[job_id]["status"] = "failed"
                _import_jobs[job_id]["error"] = "Очередь синхронизации не создана"
        raise HTTPException(503, "Синхронизация не запущена")

    return UploadAcceptedResponse(job_id=job_id, message="Импорт поставлен в очередь (приоритет)")


@tool_library_router.get(
    "/upload/status/{job_id}",
    response_model=ImportStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Задача не найдена"}},
)
def upload_status(job_id: str):
    """Возвращает статус фонового импорта по job_id."""
    with _import_jobs_lock:
        job = _import_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Задача импорта не найдена")
    return ImportStatusResponse(
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
    )


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
