from DB.Engine.CRUD import BaseCRUD
from DB.Models.Settings import Settings
from threading import Lock
import json
from datetime import datetime
from typing import Dict, Any, Optional


class EngineSettings(BaseCRUD):
    """CRUD для управления настройками сервера с кэшированием"""

    _type_casts = {
        'str': str,
        'int': int,
        'float': float,
        'bool': lambda x: bool(int(x)),  # Store as 0/1 in DB
        'json': json.loads
    }
    
    # Общий кэш для всех экземпляров класса
    _cache: Dict[str, Any] = {}
    _cache_lock = Lock()

    def __init__(self, session=None):
        super().__init__(session=session, model=Settings)

    def load_all_to_cache(self) -> Dict[str, Any]:
        """Загружает все настройки в кэш"""
        with self._cache_lock:
            settings = self.all()
            self._cache.clear()
            for setting in settings:
                value = self._cast_value(setting.value, setting.value_type)
                self._cache[setting.key] = value
            return self._cache.copy()

    def _ensure_cache_loaded(self):
        """Проверяет и загружает кэш, если он пустой"""
        with self._cache_lock:
            if not self._cache:
                try:
                    settings = self.all()
                    for setting in settings:
                        value = self._cast_value(setting.value, setting.value_type)
                        self._cache[setting.key] = value
                except Exception:
                    # Если таблица Settings еще не создана, игнорируем ошибку
                    pass

    def get_cached(self, key: str) -> Optional[Any]:
        """Получить значение настройки из кэша"""
        self._ensure_cache_loaded()
        with self._cache_lock:
            return self._cache.get(key)

    def set_setting(self, key: str, value: Any, user_id: int = None) -> bool:
        """Установка значения настройки с обновлением кэша"""
        with self._cache_lock:
            # Находим существующую настройку
            existing = self.find_first(key=key)
            if not existing:
                return False

            # Конвертируем значение в строку для хранения в БД
            string_value = self._stringify_value(value, existing.value_type)

            # Обновляем в БД
            success = self.update(
                existing.id,
                value=string_value,
                updated_by=user_id,
                updated_at=datetime.utcnow()
            )
            if success:
                self._cache[key] = value
            return success

    def get_count(self) -> int:
        """Возвращает количество настроек"""
        return len(self.all())

    @staticmethod
    def _cast_value(value: str, value_type: str) -> Any:
        """Преобразует строковое значение в правильный тип данных"""
        cast_func = EngineSettings._type_casts.get(value_type, str)
        try:
            return cast_func(value)
        except (ValueError, json.JSONDecodeError):
            # Возвращаем значение как есть при ошибке преобразования
            return value

    @staticmethod
    def _stringify_value(value: Any, value_type: str) -> str:
        """Преобразует значение в строку для хранения в БД"""
        if value_type == 'json':
            return json.dumps(value, ensure_ascii=False)
        elif value_type == 'bool':
            return '1' if value else '0'
        else:
            return str(value)
