from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict
# , List, Optional
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.ErrorsCRUD import EngineError
from DB.Engine.ErrorHasDeviceCRUD import EngineErrorHasDevice
from DB.Engine.UserCRUD import EngineUser
# from DB.Models import Error, ErrorHasDevice, Device, User

history_error_router = APIRouter(tags=["History error"])

# --- GET /history/error/{device_number} ---
@history_error_router.get("/history/error/{device_number}", response_model=Dict)
def get_error_history(
    device_number: int,
    db: Session = Depends(get_db)
):
    """Получение истории ошибок для устройства по серийному номеру"""
    device_crud = EngineDevice()
    error_has_device_crud = EngineErrorHasDevice()
    user_crud = EngineUser()

    # 1. Получение устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # 2. Получение всех связанных ошибок
    error_ids = error_has_device_crud.get_error_ids_by_device(device.id)
    if not error_ids:
        return {"error": {}}

    # 3. Получение данных ошибок и связанных пользователей
    errors = []
    for error_id in error_ids:
        error = EngineError().get_error(error_id)
        if error:
            user = user_crud.get_user_by_id(error.user_id) if error.user_id else None
            errors.append({
                "date": error.timestamp.isoformat() if error.timestamp else "None",
                "name_error": error.error_type,
                "user": f"{user.first_name or ''} {user.second_name or ''}".strip() if user else "None",
                "device": device.name
            })

    # 4. Формирование ответа в требуемом формате
    return {"error": {str(i): err for i, err in enumerate(errors)}}

# --- POST /history/error/{device_number} ---
@history_error_router.post("/history/error/{device_number}", status_code=status.HTTP_201_CREATED)
def create_error(
    device_number: int,
    error_data: dict,  # Заменить на Pydantic-модель
    db: Session = Depends(get_db)
):
    """Создание новой ошибки для устройства"""
    device_crud = EngineDevice()
    error_crud = EngineError()
    error_has_device_crud = EngineErrorHasDevice()

    # 1. Валидация устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(404, "Устройство не найдено")

    # 2. Создание ошибки
    new_error = error_crud.create_error(
        error_id=error_data.get("user_id"),
        error_type=error_data.get("error_type"),
        message=error_data.get("message"),
    )

    # 3. Связь с устройством
    error_has_device_crud.link_error_to_device(new_error.id, device.id)

    return {"status": "success", "error_id": new_error.id}

# --- PUT /history/error/{device_number}/{error_id} ---
@history_error_router.put("/history/error/{device_number}/{error_id}")
def update_error(
    device_number: int,
    error_id: int,
    update_data: dict,  # Заменить на Pydantic-модель
    db: Session = Depends(get_db)
):
    """Обновление данных ошибки"""
    device_crud = EngineDevice()
    error_crud = EngineError()
    error_has_device_crud = EngineErrorHasDevice()

    # 1. Проверка устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(404, "Устройство не найдено")

    # 2. Проверка связи ошибки с устройством
    if not error_has_device_crud.check_link(error_id, device.id):
        raise HTTPException(403, "Ошибка не связана с устройством")

    # 3. Обновление данных
    updated_error = error_crud.update_error(
        error_id=error_id,
        error_type=update_data.get("error_type"),
        message=update_data.get("message")
    )

    return {"status": "success", "data": updated_error}

# --- DELETE /history/error/{device_number}/{error_id} ---
@history_error_router.delete("/history/error/{device_number}/{error_id}")
def delete_error(
    device_number: int,
    error_id: int,
    db: Session = Depends(get_db)
):
    """Удаление ошибки"""
    device_crud = EngineDevice()
    error_crud = EngineError()
    error_has_device_crud = EngineErrorHasDevice()

    # 1. Проверка устройства
    device = device_crud.get_device_by_number(device_number)
    if not device:
        raise HTTPException(404, "Устройство не найдено")

    # 2. Проверка связи
    if not error_has_device_crud.check_link(error_id, device.id):
        raise HTTPException(403, "Ошибка не связана с устройством")

    # 3. Удаление связи и ошибки
    error_has_device_crud.unlink_error_from_device(error_id, device.id)
    error_crud.delete_error(error_id)

    return {"status": "success"}
