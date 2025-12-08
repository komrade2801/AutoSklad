from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional, Tuple
import json
import ipaddress
from DB.session import get_db
from DB.Engine.SettingsCRUD import EngineSettings
from DB.Engine.DeviceDefaultsCRUD import EngineDeviceDefaults
from Core.authorization import AuthService, TokenData
from DB.Data.init_db import restart_program

settings_router = APIRouter(tags=["Settings"])
auth_service = AuthService()

@settings_router.get("/settings", response_model=Dict[str, List[Dict]])
def get_all_settings(db: Session = Depends(get_db)):
    """Get all settings grouped by category for UI display"""
    # Check authorization
    # auth_service.validation_user(request) - would need request object, implement later

    settings_crud = EngineSettings()
    all_settings = settings_crud.all()

    # Group by category for UI tabs
    grouped = {
        "network": [],
        "security": [],
        "database": [],
        "sync": [],
        "frontend": []
    }

    for setting in all_settings:
        category = setting.category
        if category not in grouped:
            grouped[category] = []

        grouped[category].append({
            'key': setting.key,
            'value': settings_crud._cast_value(setting.value, setting.value_type),
            'type': setting.value_type,
            'category': setting.category,
            'description': setting.description,
            'sensitive': setting.is_sensitive,
            'requires_restart': setting.requires_restart
        })

    return grouped

def validate_setting_value(setting_key: str, value: Any) -> Tuple[bool, Optional[str]]:
    """
    Валидация значения настройки.
    Возвращает (is_valid, error_message).
    """
    # Валидация порта
    if setting_key == 'port':
        try:
            port = int(value)
            if not (1 <= port <= 65535):
                return False, f"Порт должен быть в диапазоне от 1 до 65535, получено: {port}"
        except (ValueError, TypeError):
            return False, f"Порт должен быть числом, получено: {value}"
    
    # Валидация IP-адреса
    elif setting_key == 'Host':
        try:
            ipaddress.ip_address(str(value))
        except ValueError:
            return False, f"Некорректный IP-адрес: {value}"
    
    # Валидация таймаутов
    elif setting_key in ['SENDER_TIMEOUT', 'RECEIVER_TIMEOUT']:
        try:
            timeout = int(value)
            if not (1 <= timeout <= 3600):
                return False, f"Таймаут должен быть в диапазоне от 1 до 3600 секунд, получено: {timeout}"
        except (ValueError, TypeError):
            return False, f"Таймаут должен быть числом, получено: {value}"
    
    # Валидация для целых чисел
    # Проверка будет выполнена на основе value_type из БД
    
    return True, None

def get_user_id_from_request(request: Request) -> Optional[int]:
    """Получает user_id из JWT токена в запросе"""
    try:
        token = auth_service.extract_token(request)
        if not token:
            return None
        
        token_data = auth_service.verify_token(token)
        if isinstance(token_data, dict) and token_data.get("status") == "error":
            return None
        
        if isinstance(token_data, TokenData):
            return token_data.user_id
        
        return None
    except Exception:
        return None

@settings_router.put("/settings/{setting_key}")
def update_setting(
    setting_key: str, 
    value: Any, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Update single setting value with validation"""
    settings_crud = EngineSettings()

    # Получаем информацию о настройке до обновления
    existing = settings_crud.find_first(key=setting_key)
    if not existing:
        raise HTTPException(status_code=404, detail="Setting not found")

    # Валидация значения
    is_valid, error_message = validate_setting_value(setting_key, value)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Дополнительная валидация типа
    if existing.value_type == 'int':
        try:
            int(value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, 
                detail=f"Настройка {setting_key} должна быть числом, получено: {value}"
            )
    elif existing.value_type == 'bool':
        if value not in [True, False, 0, 1, '0', '1', 'true', 'false']:
            raise HTTPException(
                status_code=400,
                detail=f"Настройка {setting_key} должна быть булевым значением, получено: {value}"
            )

    # Получаем user_id из токена
    user_id = get_user_id_from_request(request)
    if user_id is None:
        user_id = 1  # Fallback для совместимости

    result = settings_crud.set_setting(setting_key, value, user_id=user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Setting not found")

    # Используем requires_restart из БД, а не хардкод
    return {"status": "updated", "requires_restart": existing.requires_restart}


@settings_router.post("/settings/restart")
def restart_application(background_tasks: BackgroundTasks):
    """
    Инициирует перезапуск приложения после изменения критичных настроек.
    Новый процесс запускается в фоне, текущий завершается.
    """
    background_tasks.add_task(restart_program)
    return {"status": "restarting"}

def _get_requires_restart(setting_key: str) -> bool:
    """
    Проверяет, требует ли настройка перезапуска.
    Используется как fallback, если настройка не найдена в БД.
    """
    settings_crud = EngineSettings()
    existing = settings_crud.find_first(key=setting_key)
    if existing:
        return existing.requires_restart
    
    # Fallback для критичных настроек (на случай, если настройка еще не в БД)
    restart_required = {"Host", "port", "SECRET_KEY", "AES_KEY"}
    return setting_key in restart_required

@settings_router.get("/device-templates", response_model=List[Dict])
def get_device_templates(db: Session = Depends(get_db)):
    """Get available device configuration templates"""
    templates_crud = EngineDeviceDefaults()
    templates = templates_crud.filter_by(is_active=True)

    return [{
        'template_name': t.template_name,
        'description': t.description,
        'config': json.loads(t.config_json)
    } for t in templates]

@settings_router.get("/current-device-config/{device_number}")
def get_current_device_config(device_number: int, db: Session = Depends(get_db)):
    """Get current configuration for a specific device"""
    from DB.Engine.DeviceCRUD import EngineDevice
    device_crud = EngineDevice()
    device = device_crud.get_device_by_number(device_number)

    if not device:
        raise HTTPException(404, "Device not found")

    return json.loads(device.details)
