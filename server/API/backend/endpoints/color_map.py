# color_map.py

from typing import Union, Dict

# Тип значения: либо строка (один цвет), либо словарь has_plan→цвет
ColorMapValue = Union[str, Dict[bool, str]]

STATUS_COLORS: dict[str, ColorMapValue] = {
    # === start_system ===
    # если нет плана — оранжевый, если есть — тёмно‑зелёный
    "start_system": {
        False: "#ff4f00",  # Orange для свободного
        True:  "#2C8822",  # ForestGreen для занятых
    },

    # === mass_drop_ready ===
    # массовая загрузка готова
    "mass_drop_ready": "#535353",   # DarkGray

    # === mass_load_ready ===
    # массовая выгрузка готова
    "mass_load_ready": "#69696910", # DimGray с 10% прозрачности

    # === mass_drop_init ===
    # массовая загрузка начата
    "mass_drop_init": "#1E90FF",    # DodgerBlue

    # === mass_load_init ===
    # массовая выгрузка начата
    "mass_load_init": "#535353",    # Gold

    # === drop_ready ===
    # загрузка (одиночная) готова
    "drop_ready": "#00CED1",        # DarkTurquoise

    # === load_ready ===
    # выгрузка (одиночная) готова
    "load_ready": "#FF1493",        # DeepPink

    # === fallback ===
    # цвет по умолчанию, если вдруг стype не найден
    "__default__": "#00000000",     # полностью прозрачный
}
