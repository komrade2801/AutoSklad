# config.py
from pathlib import Path
import json, threading
from typing import Dict, List

JSON_PATH = Path("field_map.json")
_LOCK = threading.RLock()

# Поля из карт соответствия:
DEFAULT_FIELD_MAP: Dict[str, List[str]] = {
    # === Group ===
    "group_id":            ["Уникальный идентификатор группы инструмента"],
    "group_name":          ["Название группы", "Тип инструмента"],
    "group_description":   ["Описание группы", "Поставщик"],
    "group_paren_group_id":["Код родительской группы"],

    # === ToolTypes ===
    "tool_types_id":           ["Уникальный идентификатор инструмента"],
    "tool_types_name":         ["Название инструмента",
                                "Шифр инструмента",
                                "Код\nноменклатуры",
                                "Наименование краткое\n(не более 25 символов)"],
    "tool_types_description":  ["Описание инструмента",
                                "Ø / R",
                                "Описание (не более 250 символов)",
                                "Наименование полное\n (не более 100 символов)"],
    "tool_types_count":        ["Количество инструмента"],
    "tool_types_img":          ["Изображение инструмента",
                                "Изображение\nноменклатуры"],
    "tool_types_groups_id":    ["Ключ на группу инструмента",
                                "Код группы номенклатуры"],

    # === Tools ===
    "tool_id":                 ["Уникальный идентификатор инструмента"],
    "tool_inventory_number":   ["Инвентарный номер"],
    "tool_plan_id":            ["Идентификатор чертежа"],
    "tool_tool_type_id":       ["Ключ на тип инструмента"],
}

def load_field_map() -> Dict[str, List[str]]:
    """Загрузить маппинг из JSON или вернуть дефолт."""
    if JSON_PATH.exists():
        try:
            return json.loads(JSON_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return DEFAULT_FIELD_MAP.copy()

def save_field_map(mapping: Dict[str, List[str]]):
    """Сохранить маппинг в JSON (потокобезопасно)."""
    with _LOCK:
        JSON_PATH.write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

def update_field_map(new: Dict[str, List[str]]):
    """
    Добавить новые заголовки из фронтенда в маппинг и сохранить.
    """
    fm = load_field_map()
    for key, hdrs in new.items():
        fm.setdefault(key, [])
        for h in hdrs:
            if h and h not in fm[key]:
                fm[key].append(h)
    save_field_map(fm)
