# mappers.py
import math
from typing import Any, Dict, List
# from fastapi import HTTPException
from pydantic import RootModel

from API.backend.upload.config import DEFAULT_FIELD_MAP


# load_field_map,  BaseModel, Field,

class ColumnsMapModel(RootModel[Dict[str, List[str]]]):
    """
    Корневая модель, хранящая произвольный маппинг:
      ключ -> список заголовков из Excel
    Пример в Swagger берётся из DEFAULT_FIELD_MAP.
    """
    # root: Dict[str, List[str]]
    class Config:
        json_schema_extra = {
            "example": DEFAULT_FIELD_MAP
        }


def _is_valid(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and math.isnan(val):
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def get_field(rec: Dict[str, Any],
              logical: str,
              field_map: Dict[str, List[str]]) -> Any:
    """
    Пробегает по всем вариантам заголовков для логического поля и возвращает первое валидное значение.
    """
    for hdr in field_map.get(logical, []):
        if hdr in rec and _is_valid(rec[hdr]):
            return rec[hdr]
    return None


def ___normalize_record(
        rec: Dict[str, Any],
        required: List[str],
        field_map: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Собирает нормализованный словарь по ключам из field_map и проверяет обязательные поля.
    """
    norm = {key: get_field(rec, key, field_map) for key in field_map.keys()}

    missing = [f for f in required if not norm.get(f)]
    if missing:
        raise ValueError(f"Missing mandatory fields: {', '.join(missing)}")

    return norm


def normalize_record(rec: Dict[str, Any],
                     required: List[str],
                     field_map: Dict[str, List[str]],
                     last_seen: Dict[str, Any]) -> Dict[str, Any]:
    """
    Собирает нормализованный словарь по ключам из field_map и проверяет обязательные поля.
    При этом, если значение поля равно строке '--', оно заменяется на last_seen[target].
    Возвращает обновлённый last_seen внутри norm для последующего использования.
    """
    norm = {}
    for key, headers in field_map.items():
        val = None
        # ищем первое валидное
        for hdr in headers:
            if hdr in rec:
                raw = rec[hdr]
                if isinstance(raw, str) and raw.strip() == "--":
                    # особый маркер: наследуем
                    val = last_seen.get(key)
                    break
                if raw not in (None, ""):
                    val = raw
                    break
        # обновляем norm и last_seen, если появилось новое
        norm[key] = val
        if val not in (None, "", "--"):
            last_seen[key] = val

    # проверяем обязательные
    missing = [f for f in required if not norm.get(f)]
    if missing:
        raise ValueError(f"Missing mandatory fields: {', '.join(missing)}")

    return norm, last_seen