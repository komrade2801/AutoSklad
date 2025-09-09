# config.py

from pathlib import Path
# import json

# 1. Загружаем конфиг рядом с этим файлом
config_path = Path(__file__).parent / "config.json"
# cfg = json.loads(config_path.read_text(encoding="utf-8"))

FullScreen = False
db_path = 'vending.db'
db_path_work = 'vending.db'
db_path_test = ':memory:'

