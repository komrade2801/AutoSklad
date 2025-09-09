from options import *

import os

# относительный путь от этого файла к sqlite-файлу
db_filename = "data/sync.db"

def get_db_path() -> str:
    # src/DB/ → поднимаемся наверх, чтобы хранить БД рядом с run.py
    here = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(here, os.pardir))
    # поддиректория data/ в корне проекта
    return os.path.join(project_root, db_filename)
