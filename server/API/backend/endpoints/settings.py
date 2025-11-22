from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import json
from DB.session import get_db
from DB.Engine.SettingsCRUD import EngineSettings
from DB.Engine.DeviceDefaultsCRUD import EngineDeviceDefaults
from Core.authorization import AuthService

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

@settings_router.put("/settings/{setting_key}")
def update_setting(setting_key: str, value: Any, db: Session = Depends(get_db)):
    """Update single setting value"""
    settings_crud = EngineSettings()

    result = settings_crud.set_setting(setting_key, value, user_id=1)  # hardcoded user_id for now

    if not result:
        raise HTTPException(404, "Setting not found")

    return {"status": "updated", "requires_restart": _get_requires_restart(setting_key)}

def _get_requires_restart(setting_key: str) -> bool:
    """Check if setting requires restart (hardcoded for common ones)"""
    restart_required = ["Host", "port", "secret", "AES_KEY"]
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
