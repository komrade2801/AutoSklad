import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import db_path


def check_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем текущую директорию
    __db_path = os.path.join(current_dir, db_path)  # Формируем относительный путь

    # if os.path.exists(__db_path):
    #     print(f"Файл базы данных '{__db_path}' существует.")
    # else:
    #     print(f"Файл базы данных '{__db_path}' не найден.")
    return __db_path


def engine(db_path=check_file()):
    _engine = create_engine(f"sqlite:///{db_path}", echo=False,
                            connect_args={"check_same_thread": False, "timeout": 10}, )
    return _engine


def SessionLocal(_engine=engine(db_path=check_file())):
    import time
    time.sleep(0.1)  # 100 мс
    _SessionLocal = sessionmaker(bind=_engine)
    return _SessionLocal()
