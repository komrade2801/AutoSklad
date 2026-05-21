"""Проверка HAL-координат ячейки и ввода на screen_38."""

from typing import List, Optional, Tuple

REASON_MISSING_HAL_COORDS = "missing_hal_coords"
REASON_ZERO_HAL_COORDS = "zero_hal_coords"
REASON_EMPTY = "empty"
REASON_INVALID_CHARS = "invalid_chars"
REASON_OUT_OF_RANGE = "out_of_range"
REASON_CELL_NOT_FOUND = "cell_not_found"

MOT_STEP_MIN = 0
MOT_STEP_MAX = 999999
CELL_NUMBER_MIN = 1
CELL_NUMBER_MAX = 9999

# Индексы MOT (0-based): M1,M2 — hal_z; M3 — hal_x на экране координат; M5 — штырь
HAL_MOT_Z_INDICES = (0, 1)
HAL_MOT_X_INDEX = 2
HAL_MOT_X_DERIVED_INDEX = 3
HAL_MOT_PUSH_INDEX = 4
# Смещение M4 только в сценарии выдачи: M4 = hal_x − HAL_MOT_X_OFFSET_M4
HAL_MOT_X_OFFSET_M4 = 25
HAL_DISPENSE_PUSH_DOWN = 60
HAL_DISPENSE_PUSH_UP = 0

# Запись hal_x/hal_z с экрана координат: M3 → hal_x, M1 → hal_z
HAL_SAVE_MOT_X_INDEX = HAL_MOT_X_INDEX
HAL_SAVE_MOT_Z_INDEX = HAL_MOT_Z_INDICES[0]

HAL_JOG_X_INDICES = (HAL_MOT_X_INDEX,)
HAL_JOG_Z_INDICES = HAL_MOT_Z_INDICES


def _clamp_step(value: int) -> int:
    return max(MOT_STEP_MIN, min(MOT_STEP_MAX, int(value)))


def hal_mot4_from_hal_x(hal_x: int) -> int:
    """MOT4 при выдаче: hal_x − 25 (задняя ось X)."""
    return _clamp_step(int(hal_x) - HAL_MOT_X_OFFSET_M4)


def clamp_mot_vector(pos) -> List[int]:
    """Привести вектор MOT к 5 осям и диапазону без пересчёта M4 от M3."""
    p = [_clamp_step(int(v)) for v in list(pos)[:5]]
    while len(p) < 5:
        p.append(0)
    return p


def normalize_mot_vector(pos) -> List[int]:
    """Устаревший алиас: только clamp. Связка M4=M3−25 — в hal_dispense_target_mot5."""
    return clamp_mot_vector(pos)


def hal_dispense_target_mot5(hal_x: int, hal_z: int) -> Tuple[int, int, int, int, int]:
    """
    Подъезд к ячейке: M1=M2=hal_z, M3=hal_x, M4=hal_x−25, M5=0.
    """
    hx = _clamp_step(int(hal_x))
    hz = _clamp_step(int(hal_z))
    return (hz, hz, hx, hal_mot4_from_hal_x(hx), 0)


def hal_project_hal_xz_from_motors(pos) -> Tuple[int, int]:
    """Проекция вектора MOT в hal_x (M3) и hal_z (M1)."""
    p = clamp_mot_vector(pos)
    return int(p[HAL_MOT_X_INDEX]), int(p[HAL_MOT_Z_INDICES[0]])

_MESSAGES = {
    REASON_MISSING_HAL_COORDS: "Координаты ячейки не заданы",
    REASON_ZERO_HAL_COORDS: "Нельзя сохранить (0, 0) — подведите каретку к ячейке",
    REASON_EMPTY: "Поле не заполнено",
    REASON_INVALID_CHARS: "Только цифры",
    REASON_OUT_OF_RANGE: "Число вне допустимого диапазона",
    REASON_CELL_NOT_FOUND: "Ячейка с таким номером не найдена",
}


def message_for_reason(reason: str, *, motor_label: str = "", min_v=None, max_v=None) -> str:
    base = _MESSAGES.get(reason, "Ошибка ввода")
    if reason == REASON_OUT_OF_RANGE and min_v is not None and max_v is not None:
        if motor_label:
            return f"{motor_label}: допустимо {min_v}…{max_v}"
        return f"Допустимо {min_v}…{max_v}"
    if motor_label:
        return f"{motor_label}: {base}"
    return base


def parse_uint(
    text: str,
    *,
    min_value: int = 0,
    max_value: int = MOT_STEP_MAX,
) -> Tuple[Optional[int], Optional[str]]:
    raw = (text or "").strip()
    if not raw:
        return None, REASON_EMPTY
    if not raw.isdigit():
        return None, REASON_INVALID_CHARS
    value = int(raw)
    if value < min_value or value > max_value:
        return None, REASON_OUT_OF_RANGE
    return value, None


def validate_cell_number_text(text: str) -> Tuple[Optional[int], Optional[str]]:
    return parse_uint(
        text,
        min_value=CELL_NUMBER_MIN,
        max_value=CELL_NUMBER_MAX,
    )


def validate_motor_position_texts(
    texts: List[str],
) -> Tuple[Optional[List[int]], Optional[int], Optional[str]]:
    """
    texts: 5 строк координат M1..M5.
    Возвращает (positions, bad_index, reason). bad_index 0..4 при ошибке.
    """
    out: List[int] = []
    for i, t in enumerate(texts[:5]):
        value, reason = parse_uint(
            t,
            min_value=MOT_STEP_MIN,
            max_value=MOT_STEP_MAX,
        )
        if reason:
            return None, i, reason
        out.append(value)
    while len(out) < 5:
        out.append(0)
    return out, None, None


def validate_hal_cell_coords(
    hal_x: Optional[int], hal_z: Optional[int]
) -> Tuple[bool, Optional[str]]:
    """
    Координаты валидны, если оба заданы (NOT NULL) и пара не (0, 0).
    """
    if hal_x is None or hal_z is None:
        return False, REASON_MISSING_HAL_COORDS
    if int(hal_x) == 0 and int(hal_z) == 0:
        return False, REASON_ZERO_HAL_COORDS
    return True, None


def format_hal_coords_error(
    reason: str,
    *,
    cell_id: Optional[int] = None,
    number: Optional[int] = None,
) -> str:
    parts = [reason]
    if cell_id is not None:
        parts.append(f"cell_id={cell_id}")
    if number is not None:
        parts.append(f"number={number}")
    return " ".join(parts)
