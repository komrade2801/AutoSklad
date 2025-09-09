# DB/session.py
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker, Session

from DB.Data.base import Base
from DB.Data.sqlite_db import SessionLocal, get_engine


# FastAPI-зависимость
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Возвращает экземпляр Session напрямую, без генератора.
    Используйте его в скриптах, на старте, вне FastAPI.
    """
    return SessionLocal()

def get_inspector():
    """
    Пример функции, если нужен инспектор для работы со схемой.
    """
    return inspect(get_engine())
