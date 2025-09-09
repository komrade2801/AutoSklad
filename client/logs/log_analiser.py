# log_analiser.py

import re
import os
from pathlib import Path

# === НАСТРОЙКИ ===

# 1) где лежит ваш лог:
LOG_FILENAME = "sync.log"  # файл рядом со скриптом

# 2) список фильтров — строки или regex
FILTERS = [
    "Cell"
    # "id",
    # r"map_incoming",     # пример regex
    # r"DataTransformer",  # ...
]

# 3) включить поддержку регулярных выражений?
USE_REGEX = False

# ====================

def compile_filters(patterns, use_regex):
    compiled = []
    for p in patterns:
        if use_regex:
            compiled.append(re.compile(p))
        else:
            compiled.append(re.compile(re.escape(p)))
    return compiled

def line_matches(line, filters):
    return any(f.search(line) for f in filters)

def main():
    script_dir = Path(__file__).parent
    log_path = script_dir / LOG_FILENAME

    if not log_path.exists():
        print(f"Не найден файл лога: {log_path}")
        return

    filters = compile_filters(FILTERS, USE_REGEX)

    with open(log_path, encoding="utf-8") as f:
        for num, line in enumerate(f, 1):
            if line_matches(line, filters):
                print(f"{num:4d}: {line.rstrip()}")

if __name__ == "__main__":
    main()
