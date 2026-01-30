# DB/Data/init_db.py

import os
import sys
import subprocess

from Core.app_logging import get_logger
from Core.default import rebuild_db, execute
from options import db_path

logger = get_logger(__name__)

def get_db_filepath() -> str:
    """
    Возвращает полный путь к файлу sqlite, например ".../DB/Data/web_vending.db".
    """
    here = os.path.dirname(os.path.abspath(__file__))  # .../src/WEB/DB/Data
    return os.path.join(here, db_path)

def restart_program():
    """
    Перезапускает текущее приложение: запускает новый процесс с теми же argv и завершает старый.
    """
    logger.info("Перезапуск приложения...")
    python = sys.executable
    # sys.argv содержит ['python', 'main.py', ...]
    subprocess.Popen([python] + sys.argv)
    # Завершаем старый процесс
    sys.exit()

def initialize_database_if_needed():
    """
    Проверяет, существует ли файл БД. Если нет:
      1) вызывает rebuild_db() и execute() (из Core.default),
      2) перезапускает программу, чтобы все модули заново импортировались с уже готовой БД.
    """
    db_file = get_db_filepath()

    if not os.path.exists(db_file):
        logger.warning("SQLite file not found at %s", db_file)
        try:
            # 1) пересоздаём схему (удаляем старый файл и создаём таблицы)
            rebuild_db()
            # 2) заполняем начальные данные
            execute()
        except Exception as e:
            logger.exception("Failed to rebuild or execute initial load: %s", e)
            raise

        # 3) перезапускаем приложение (новый процесс)
        restart_program()
    else:
        logger.info("Using SQLite file at %s", db_file)
