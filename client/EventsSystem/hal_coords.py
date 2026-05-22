"""Проверка HAL-координат ячейки и ввода на screen_38."""

from typing import List, Optional, Tuple

REASON_MISSING_HAL_COORDS = "missing_hal_coords"
REASON_ZERO_HAL_COORDS = "zero_hal_coords"
REASON_EMPTY = "empty"
REASON_INVALID_CHARS = "invalid_chars"
REASON_OUT_OF_RANGE = "out_of_range"
REASON_EXCEEDS_AXIS_MAX = "exceeds_axis_max"
REASON_CELL_NOT_FOUND = "cell_not_found"

MOT_STEP_MIN = 0
MOT_STEP_MAX = 999999
# Максимальные шаги по осям MOT1..MOT5 (индекс 0..4)
MOT_AXIS_MAX = (420, 420, 632, 590, 60)
MOT_EXCEEDS_MAX_MESSAGE = "Превышено максимальное значение"
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


def mot_axis_max(motor_index: int) -> int:
    """Верхняя граница шагов для MOT1..MOT5 (motor_index 0..4)."""
    idx = max(0, min(4, int(motor_index)))
    return int(MOT_AXIS_MAX[idx])


def motor_label(motor_index: int) -> str:
    if motor_index in HAL_MOT_Z_INDICES:
        return "M1–M2"
    return f"M{int(motor_index) + 1}"


def _clamp_step(value: int, motor_index: Optional[int] = None) -> int:
    v = int(value)
    if motor_index is not None:
        return max(MOT_STEP_MIN, min(mot_axis_max(motor_index), v))
    return max(MOT_STEP_MIN, min(MOT_STEP_MAX, v))


def clamp_motor_value(value: int, motor_index: int) -> int:
    return _clamp_step(value, motor_index)


def apply_jog_delta(value: int, delta: int, motor_index: int) -> Tuple[int, bool]:
    """Сдвиг по оси с усечением; True, если цель выходила за [0, max]."""
    raw = int(value) + int(delta)
    clamped = clamp_motor_value(raw, motor_index)
    return clamped, clamped != raw


def parse_hal_jog_trigger(trigger: str) -> Tuple[Optional[str], int]:
    """
    hal_jog_z_plus / hal_jog_m3_minus -> ('z'|'m3'|..., sign).
    sign: +1 или -1; axis None, если триггер не распознан.
    """
    name = (trigger or "").strip().lower()
    if not name.startswith("hal_jog_"):
        return None, 0
    body = name[len("hal_jog_") :]
    if body.endswith("_plus"):
        axis = body[: -len("_plus")]
        sign = 1
    elif body.endswith("_minus"):
        axis = body[: -len("_minus")]
        sign = -1
    else:
        return None, 0
    if axis in ("z", "m1", "m2", "m3", "m4", "m5"):
        return axis, sign
    return None, 0


def jog_motor_indices_for_axis(axis: str) -> List[int]:
    if axis == "z":
        return list(HAL_MOT_Z_INDICES)
    if axis in ("m1", "m2", "m3", "m4", "m5"):
        return [int(axis[1]) - 1]
    return []


def apply_jog_to_motor_positions(
    positions,
    *,
    axis: str,
    sign: int,
    step: int,
) -> Tuple[List[int], bool]:
    """Рассчитать кадр MOT после JOG; True, если хотя бы одна ось усечена."""
    delta = int(sign) * int(step)
    indices = jog_motor_indices_for_axis(axis)
    pos = list(positions)[:5]
    while len(pos) < 5:
        pos.append(0)
    any_clamped = False
    for idx in indices:
        new_v, clamped = apply_jog_delta(pos[idx], delta, idx)
        if clamped:
            any_clamped = True
        pos[idx] = new_v
    return pos, any_clamped


def hal_mot4_from_hal_x(hal_x: int) -> int:
    """MOT4 при выдаче: hal_x − 25 (задняя ось X)."""
    return clamp_motor_value(int(hal_x) - HAL_MOT_X_OFFSET_M4, HAL_MOT_X_DERIVED_INDEX)


def clamp_mot_vector(pos) -> List[int]:
    """Привести вектор MOT к 5 осям и диапазону без пересчёта M4 от M3."""
    raw = list(pos)[:5]
    while len(raw) < 5:
        raw.append(0)
    return [clamp_motor_value(int(v), i) for i, v in enumerate(raw)]


def normalize_mot_vector(pos) -> List[int]:
    """Устаревший алиас: только clamp. Связка M4=M3−25 — в hal_dispense_target_mot5."""
    return clamp_mot_vector(pos)


def hal_dispense_target_mot5(hal_x: int, hal_z: int) -> Tuple[int, int, int, int, int]:
    """
    Подъезд к ячейке: M1=M2=hal_z, M3=hal_x, M4=hal_x−25, M5=0.
    """
    hx = clamp_motor_value(int(hal_x), HAL_MOT_X_INDEX)
    hz = clamp_motor_value(int(hal_z), HAL_MOT_Z_INDICES[0])
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
    REASON_EXCEEDS_AXIS_MAX: MOT_EXCEEDS_MAX_MESSAGE,
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


def parse_motor_uint(
    text: str,
    motor_index: int,
    *,
    min_value: int = MOT_STEP_MIN,
) -> Tuple[Optional[int], Optional[str]]:
    """Разбор координаты MOT с верхней границей по оси."""
    return parse_uint(
        text,
        min_value=min_value,
        max_value=mot_axis_max(motor_index),
    )


def clamp_motor_text(
    text: str,
    motor_index: int,
) -> Tuple[str, bool]:
    """
    Подставить ближайшее допустимое значение для поля ввода.
    Возвращает (текст для QLineEdit, было_ли_усечение).
    """
    raw = (text or "").strip()
    if not raw:
        return "0", False
    if not raw.isdigit():
        return raw, False
    value = int(raw)
    max_v = mot_axis_max(motor_index)
    if value > max_v:
        return str(max_v), True
    return str(value), False


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
        value, reason = parse_motor_uint(t, i)
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
