# # DB/Data/db_depends.py
# from sqlalchemy.orm import Session
#
# # from DB.Data.sqlite_db import SessionLocal
# # from DB.Data.mysql_db import SessionLocal
# import os
#
# from sqlalchemy import create_engine
# # from sqlalchemy.orm import sessionmaker
#
# from DB.config import db_path
# from DB.session import SessionLocal
#
#
# def get_db() -> Session:
#     db = SessionLocal()
#     try:
#         #  print("Открыли\n")
#         return db
#     finally:
#         #  print("Закрыли\n")
#         db.close()
#
#
# def check_file():
#     current_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем текущую директорию
#     __db_path = os.path.join(current_dir, db_path)  # Формируем относительный путь
#     return __db_path
#
# def engine(dbpath=check_file()):
#     _engine = create_engine(f"sqlite:///{dbpath}", echo=False,
#                             connect_args={"check_same_thread": False, "timeout": 10}, )
#     return _engine