# color_map.py

from typing import Union, Dict

# Тип значения: либо строка (один цвет), либо словарь has_plan→цвет
ColorMapValue = Union[str, Dict[bool, str]]

STATUS_COLORS: dict[str, ColorMapValue] = {
    # === start_system ===
    # цвет по умолчанию, если статус - пустая ячейка
    "start_system": "#979797",

    # === mass_drop_ready ===
    # массовая загрузка готова
    "mass_drop_ready": "#535353",   # DarkGray

    # === mass_load_ready ===
    # массовая выгрузка готова - инструменты размещены в аппарате
    "mass_load_ready": {
        False: "#001fff",  # Синий для свободных инструментов
        True:  "#007e0f",  # Зеленый для чертежей
    }, # DimGray с 10% прозрачности

    # === mass_drop_init ===
    # массовая загрузка начата
    "mass_drop_init": "#9d1212",    # DodgerBlue

    # === mass_load_init ===
    # массовая выгрузка начата - загрузка инициирована, но инструменты ещё не размещены
    "mass_load_init": {
        False: "#008dff",  # Светло синий для свободной загрузки
        True:  "#00ed0f",  # Светло зеленый для загрузки по чертежу
    },    # Gold

    # === drop_ready ===
    # загрузка (одиночная) готова
    "drop_ready": "#00CED1",        # DarkTurquoise

    # === load_ready ===
    # выгрузка (одиночная) готова
    "load_ready": "#FF1493",        # DeepPink

    # === fallback ===
    # цвет по умолчанию, если вдруг стype не найден
    "__default__": "#979797",     # Серый
}
