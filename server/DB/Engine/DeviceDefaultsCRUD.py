from DB.Engine.CRUD import BaseCRUD
from DB.Models.DeviceDefaults import DeviceDefaults
import json
from typing import Optional, Dict, Any


class EngineDeviceDefaults(BaseCRUD):
    """CRUD для управления шаблонами конфигураций устройств"""

    def __init__(self, session=None):
        super().__init__(session=session, model=DeviceDefaults)

    def find_by_template(self, template_name: str):
        """Найти шаблон по имени"""
        return self.find_first(template_name=template_name)

    def get_active_templates(self):
        """Получить все активные шаблоны"""
        return self.filter_by(is_active=True)

    def get_template_config(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Получить конфигурацию как dict"""
        template = self.find_by_template(template_name)
        if template:
            return json.loads(template.config_json)
        return None

    def add_template_from_dict(self, template_name: str, config_dict: Dict[str, Any],
                             description: str = None, is_active: bool = True) -> bool:
        """Добавить новый шаблон из словаря конфигурации"""
        config_json = json.dumps(config_dict, ensure_ascii=False, indent=2)

        index = max(self.get_all_ids(), default=0) + 1
        return self.add(
            index=index,
            template_name=template_name,
            config_json=config_json,
            description=description,
            is_active=is_active
        )

    def get_count(self) -> int:
        """Возвращает количество шаблонов"""
        return len(self.all())
