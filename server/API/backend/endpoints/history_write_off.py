from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from API.backend.request_models import (
    HistoryWriteOffResponse,  # Pydantic‑модель: { "operation": { "0": { ... }, "1": { ... }, ... } }
    HistoryWriteOff,  # Модель записи истории списаний (при чтении/обновлении)
    HistoryWriteOffCreate,  # Модель для создания записи списания
    HistoryWriteOffUpdate  # Модель для обновления записи списания
)
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
from DB.Engine.DropCRUD import EngineDrop  # CRUD‑класс для таблицы Drop
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.GroupCRUD import EngineGroup

history_write_off_router = APIRouter(tags=["History write off"])


def determine_tool_position(drop_record) -> str:
    """
    Определяет положение инструмента: если у записи заполнено поле cell_id, считаем, что инструмент находится на складе ("stock"),
    иначе — "in_use". При необходимости логику можно доработать.
    """
    return "stock" if drop_record.cell_id else "in_use"


@history_write_off_router.get("/history-write_off/{device_number}", response_model=HistoryWriteOffResponse)
def get_history_write_off(device_number: int, db: Session = Depends(get_db)):
    """
    Получает историю списаний для указанного устройства.

    1. Находим устройство по device_number (поле number в таблице Device).
    2. Через Tools_has_Device получаем все инструменты, принадлежащие устройству.
    3. Из таблицы Drop (через EngineDrop) выбираем записи, где tools_id входит в полученный список.
    4. Для каждой записи получаем:
         - ID_tool: берём, например, barcode инструмента;
         - group: название группы (через EngineGroup по tool.groups_id);
         - toolName: имя инструмента;
         - toolPosition: определяется функцией (если cell_id заполнено, "stock", иначе "in_use");
         - username: дефолтно "-" (так как информации о пользователе нет);
         - sum, reason, time: возвращаются как "None" (так как этих полей в таблице Drop нет).
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    drop_crud = EngineDrop()
    tools_crud = EngineTools()
    group_crud = EngineGroup()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    tool_ids = tools_has_device_crud.get_tools_by_device_id(device.id)
    if not tool_ids:
        raise HTTPException(status_code=404, detail="Инструменты для данного устройства не найдены")

    drops = drop_crud.get_drops_by_tool_ids(tool_ids)
    if not drops:
        raise HTTPException(status_code=404, detail="Записи списаний не найдены")

    operations: Dict[str, dict] = {}
    for idx, record in enumerate(drops):
        tool = tools_crud.get_tool_by_id(record.tools_id)
        if not tool:
            continue  # пропускаем запись, если инструмент не найден

        group = group_crud.get_group_by_id(tool.groups_id) if tool.groups_id else None
        operations[str(idx)] = {
            "ID_tool": tool.barcode,  # берём barcode как идентификатор инструмента
            "group": group.name if group else "Unknown",  # название группы
            "toolName": tool.name,  # имя инструмента
            "toolPosition": determine_tool_position(record),  # положение инструмента: "stock" или "in_use"
            "username": "-",  # информация о пользователе отсутствует
            "sum": "None",  # отсутствует в таблице Drop
            "reason": "None",  # отсутствует в таблице Drop
            "time": "None"  # можно вернуть "None" или форматировать created_at
        }

    return {"operation": operations}


@history_write_off_router.post("/history-write_off/{device_number}", response_model=HistoryWriteOff)
def create_history_write_off(device_number: int, write_off_data: HistoryWriteOffCreate, db: Session = Depends(get_db)):
    """
    Создает новую запись истории списаний для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что инструмент (write_off_data.tool_id) принадлежит данному устройству через Tools_has_Device.
    3. Создаем новую запись в таблице Drop через EngineDrop.
       Для полей, которых нет в модели Drop, можно задать значения по умолчанию.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    drop_crud = EngineDrop()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    if not tools_has_device_crud.check_tool_belongs_to_device(write_off_data.tool_id, device.id):
        raise HTTPException(status_code=403, detail="Инструмент не принадлежит данному устройству")

    new_record = drop_crud.create_drop(write_off_data)
    if not new_record:
        raise HTTPException(status_code=400, detail="Не удалось создать запись списания")

    return new_record


@history_write_off_router.put("/history-write_off/{device_number}/{drop_id}", response_model=HistoryWriteOff)
def update_history_write_off(device_number: int, drop_id: int, write_off_data: HistoryWriteOffUpdate,
                            db: Session = Depends(get_db)):
    """
    Обновляет запись истории списаний для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем запись из таблицы Drop по drop_id.
    3. Проверяем, что запись принадлежит инструменту, связанному с данным устройством.
    4. Обновляем запись через EngineDrop.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    drop_crud = EngineDrop()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_record = drop_crud.get_drop_by_id(drop_id)
    if not existing_record:
        raise HTTPException(status_code=404, detail="Запись списания не найдена")

    if not tools_has_device_crud.check_tool_belongs_to_device(existing_record.tools_id, device.id):
        raise HTTPException(status_code=403, detail="Запись списания не принадлежит данному устройству")

    updated_record = drop_crud.update_drop_from_data(drop_id, write_off_data)
    if not updated_record:
        raise HTTPException(status_code=400, detail="Не удалось обновить запись списания")

    return updated_record


@history_write_off_router.delete("/history-write_off/{device_number}/{drop_id}")
def delete_history_write_off(device_number: int, drop_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запись истории списаний для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем запись из таблицы Drop по drop_id.
    3. Проверяем, что запись принадлежит инструменту, связанному с данным устройством.
    4. Удаляем запись через EngineDrop.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    drop_crud = EngineDrop()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_record = drop_crud.get_drop_by_id(drop_id)
    if not existing_record:
        raise HTTPException(status_code=404, detail="Запись списания не найдена")

    if not tools_has_device_crud.check_tool_belongs_to_device(existing_record.tools_id, device.id):
        raise HTTPException(status_code=403, detail="Запись списания не принадлежит данному устройству")

    deleted = drop_crud.delete_drop(drop_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Не удалось удалить запись списания")

    return {"message": "Запись списания успешно удалена"}
