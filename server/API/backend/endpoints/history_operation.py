# API/backend/endpoints/history_operation.py
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from API.backend.request_models import (
    # Pydantic-модель: {"operation": { "0": HistoryOperation, ... } }
    HistoryOperationResponse,
    HistoryOperation,  # Модель записи истории (при чтении/обновлении)
    HistoryOperationCreate,  # Модель для создания записи
    HistoryOperationUpdate  # Модель для обновления записи
)
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from Logic.HistoryOperationCRUD import EngineHistoryOperation
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice

history_operation_router = APIRouter(tags=["History operation"])


@history_operation_router.get("/history-operation/{device_number}", response_model=HistoryOperationResponse)
def get_history_operation(device_number: int):
    """
    Получает операции истории для указанного устройства.

    Алгоритм:
      1. Находим устройство по device_number (по полю number таблицы Device).
      2. Через EngineHistoryOperation выбираем записи, связанные с этим устройством (например, по device_id).
      3. Для каждой записи формируем объект с полями:
         - date: дата операции (или "None", если не задана)
         - name_operation: название операции (или "None")
         - user: имя пользователя (или "None")
         - device: имя устройства (например, "Аппарат 1")
      4. Возвращаем итоговый объект, где ключ "operation" содержит словарь с пронумерованными записями.
    """
    print(f"get_history_operation")
    devices_crud = EngineDevice()
    history_op_crud = EngineHistoryOperation()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # Получаем все операции, связанные с устройством (предполагается, что в таблице HistoryOperation есть поле device_id)
    operations_list = None
    try:
        operations_list = history_op_crud.get_operations_by_device_id(
            device.id)
    except:
        print(traceback.format_exc())
        operations_list = []

    print(f"operations_list: {operations_list}")

    # operations: Dict[str, dict] = {}
    # if operations_list:
    #     for idx, op in enumerate(operations_list):
    #         operations[str(idx)] = {
    #             "date": op.get("date", "None"),
    #             "name_operation": op.get("name_operation", "None"),
    #             "tool": op.get("tool", "None"),
    #             "plan": op.get("plan", "None"),
    #             "user": op.get("user", "None"),
    #             "device": device.name or "Unknown"
    #         }

    operations = []
    if operations_list:
        for idx, op in enumerate(operations_list):
            # print(f"op: {op}")
            operations.append({
                "id": op.get("id", "None"),
                "date": op.get("date", "None"),
                "operation_status": op.get("status", "None"),
                "description": op.get("name_operation", "None"),
                "tool": op.get("tool", "None"),
                "plan": op.get("plan", "None"),
                "user": op.get("user", "None"),
                "device": device.name or "Unknown"
            })

    return {"operation": operations}


@history_operation_router.post("/history-operation/{device_number}", response_model=HistoryOperation)
def create_history_operation(device_number: int, op_data: HistoryOperationCreate, db: Session = Depends(get_db)):
    """
    Создает новую запись истории для указанного устройства.

    1. Находим устройство по device_number.
    2. Проверяем, что, если в данных указан инструмент, он принадлежит устройству (через ToolsHasDevice).
    3. Создаем новую запись через EngineHistoryOperation, присваивая ей device_id.
    """
    devices_crud = EngineDevice()
    tools_has_device_crud = EngineToolsHasDevice()
    history_op_crud = EngineHistoryOperation()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # Если в op_data передан tools_id, проверяем принадлежность
    if hasattr(op_data, "tools_id"):
        if not tools_has_device_crud.check_tool_belongs_to_device(op_data.tools_id, device.id):
            raise HTTPException(
                status_code=403, detail="Инструмент не принадлежит данному устройству")

    # Присваиваем созданной записи идентификатор устройства
    op_data.device_id = device.id

    new_op = history_op_crud.create_operation(op_data)
    if not new_op:
        raise HTTPException(
            status_code=400, detail="Не удалось создать операцию истории")
    return new_op


@history_operation_router.put("/history-operation/{device_number}/{op_id}", response_model=HistoryOperation)
def update_history_operation(device_number: int, op_id: int, op_data: HistoryOperationUpdate,
                             db: Session = Depends(get_db)):
    """
    Обновляет запись истории для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем запись операции по op_id.
    3. Проверяем, что операция принадлежит данному устройству (например, по device_id).
    4. Обновляем запись.
    """
    devices_crud = EngineDevice()
    # tools_has_device_crud = EngineToolsHasDevice()
    history_op_crud = EngineHistoryOperation()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_op = history_op_crud.get_operation_by_id(op_id)
    if not existing_op:
        raise HTTPException(
            status_code=404, detail="Запись истории не найдена")

    if existing_op.device_id != device.id:
        raise HTTPException(
            status_code=403, detail="Запись истории не принадлежит данному устройству")

    updated_op = history_op_crud.update_operation(op_id, op_data)
    if not updated_op:
        raise HTTPException(
            status_code=400, detail="Не удалось обновить запись истории")
    return updated_op


@history_operation_router.delete("/history-operation/{device_number}/{op_id}")
def delete_history_operation(device_number: int, op_id: int, db: Session = Depends(get_db)):
    """
    Удаляет запись истории для указанного устройства.

    1. Находим устройство по device_number.
    2. Получаем запись операции по op_id.
    3. Проверяем, что запись принадлежит данному устройству.
    4. Удаляем запись.
    """
    devices_crud = EngineDevice()
    history_op_crud = EngineHistoryOperation()

    device = devices_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    existing_op = history_op_crud.get_operation_by_id(op_id)
    if not existing_op:
        raise HTTPException(
            status_code=404, detail="Запись истории не найдена")

    if existing_op.device_id != device.id:
        raise HTTPException(
            status_code=403, detail="Запись истории не принадлежит данному устройству")

    deleted = history_op_crud.delete_operation(op_id)
    if not deleted:
        raise HTTPException(
            status_code=400, detail="Не удалось удалить запись истории")

    return {"message": "Запись истории успешно удалена"}
