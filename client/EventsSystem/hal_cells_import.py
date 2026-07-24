"""Импорт HAL-координат ячеек из CSV (client/docs/cells_hal.csv)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

DEFAULT_CSV_NAME = "cells_hal.csv"
REQUIRED_COLUMNS = ("number", "hal_x", "hal_z")

# Путь: client/docs/cells_hal.csv относительно EventsSystem/
_CLIENT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = _CLIENT_ROOT / "docs" / DEFAULT_CSV_NAME

HalImportRow = Tuple[int, int, int]  # number, hal_x, hal_z


@dataclass(frozen=True)
class HalImportParseResult:
    ok: bool
    rows: Tuple[HalImportRow, ...] = ()
    error: Optional[str] = None
    path: Optional[Path] = None


def default_hal_cells_csv_path() -> Path:
    return DEFAULT_CSV_PATH


def _norm_header(name: str) -> str:
    return (name or "").strip().lstrip("\ufeff").lower()


def _parse_int_field(raw: str, *, field: str, line_no: int) -> Tuple[Optional[int], Optional[str]]:
    text = (raw or "").strip()
    if text == "":
        return None, f"Строка {line_no}: пустое значение «{field}»"
    body = text[1:] if text.startswith("-") else text
    if not body.isdigit():
        return None, (
            f"Строка {line_no}: «{field}» должно быть целым числом "
            f"(получено «{text}»)"
        )
    return int(text, 10), None


def parse_hal_cells_csv(
    path: Optional[Path] = None,
    *,
    known_numbers: Optional[Set[int]] = None,
) -> HalImportParseResult:
    """
    Читает CSV (utf-8-sig), валидирует все строки.
    При любой ошибке — ok=False и текст ошибки; rows пустой (БД не трогаем).
    known_numbers — множество номеров ячеек в БД; если задано, неизвестный number = ошибка.
    """
    csv_path = Path(path) if path is not None else DEFAULT_CSV_PATH
    if not csv_path.is_file():
        return HalImportParseResult(
            ok=False,
            error=f"Файл не найден:\n{csv_path}",
            path=csv_path,
        )

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
            sample = fh.read(4096)
            fh.seek(0)
            if not sample.strip():
                return HalImportParseResult(
                    ok=False,
                    error="Файл пуст",
                    path=csv_path,
                )
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(fh, dialect=dialect)
            if reader.fieldnames is None:
                return HalImportParseResult(
                    ok=False,
                    error="Нет заголовка CSV",
                    path=csv_path,
                )
            header_map: Dict[str, str] = {}
            for raw_name in reader.fieldnames:
                key = _norm_header(raw_name)
                if key:
                    header_map[key] = raw_name
            missing = [c for c in REQUIRED_COLUMNS if c not in header_map]
            if missing:
                return HalImportParseResult(
                    ok=False,
                    error="Нет колонок: " + ", ".join(missing),
                    path=csv_path,
                )

            rows: List[HalImportRow] = []
            seen_numbers: Set[int] = set()
            for line_no, raw_row in enumerate(reader, start=2):
                if raw_row is None:
                    continue
                # Пропуск полностью пустых строк
                if all(not (v or "").strip() for v in raw_row.values()):
                    continue
                number, err = _parse_int_field(
                    raw_row.get(header_map["number"], ""),
                    field="number",
                    line_no=line_no,
                )
                if err:
                    return HalImportParseResult(ok=False, error=err, path=csv_path)
                assert number is not None
                if number <= 0:
                    return HalImportParseResult(
                        ok=False,
                        error=f"Строка {line_no}: number должен быть > 0",
                        path=csv_path,
                    )
                if number in seen_numbers:
                    return HalImportParseResult(
                        ok=False,
                        error=f"Строка {line_no}: дубликат number={number}",
                        path=csv_path,
                    )
                seen_numbers.add(number)

                hx, err = _parse_int_field(
                    raw_row.get(header_map["hal_x"], ""),
                    field="hal_x",
                    line_no=line_no,
                )
                if err:
                    return HalImportParseResult(ok=False, error=err, path=csv_path)
                hz, err = _parse_int_field(
                    raw_row.get(header_map["hal_z"], ""),
                    field="hal_z",
                    line_no=line_no,
                )
                if err:
                    return HalImportParseResult(ok=False, error=err, path=csv_path)
                assert hx is not None and hz is not None

                if known_numbers is not None and number not in known_numbers:
                    return HalImportParseResult(
                        ok=False,
                        error=f"Строка {line_no}: ячейка number={number} не найдена в БД",
                        path=csv_path,
                    )

                rows.append((number, hx, hz))

            if not rows:
                return HalImportParseResult(
                    ok=False,
                    error="В файле нет строк данных",
                    path=csv_path,
                )

            return HalImportParseResult(
                ok=True,
                rows=tuple(rows),
                path=csv_path,
            )
    except UnicodeDecodeError:
        return HalImportParseResult(
            ok=False,
            error="Ошибка кодировки файла (нужен UTF-8)",
            path=csv_path,
        )
    except OSError as e:
        return HalImportParseResult(
            ok=False,
            error=f"Не удалось открыть файл:\n{e}",
            path=csv_path,
        )
    except csv.Error as e:
        return HalImportParseResult(
            ok=False,
            error=f"Ошибка разбора CSV:\n{e}",
            path=csv_path,
        )


def confirm_message(rows: Sequence[HalImportRow], path: Optional[Path] = None) -> str:
    name = (path or DEFAULT_CSV_PATH).name
    return (
        f"Импортировать координаты из «{name}»?\n\n"
        f"Будет обновлено ячеек: {len(rows)}"
    )


def success_message(count: int) -> str:
    return f"Координаты обновлены.\n\nЯчеек: {count}"
