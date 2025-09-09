import traceback

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Models.Error import Error
from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Engine.ErrorsCRUD import EngineError


# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineError
@pytest.fixture
def engine_error(test_session):
    """
    Создает экземпляр EngineError с тестовой сессией.
    """
    return EngineError(session=test_session)


def test_add_error_success(engine_error, test_session):
    """
    Тест успешного добавления ошибки.
    """
    engine_error.delete_all()
    error_type = "Timeout"
    message = "The operation timed out."

    result = engine_error.add_error(error_type, message)

    assert result is True, "Ошибка не была добавлена"

    # Проверяем, что ошибка добавлена в базу данных
    added_error = test_session.query(Error).filter_by(error_type=error_type, message=message).first()
    assert added_error is not None, "Добавленная ошибка не найдена в базе данных"
    assert added_error.error_type == error_type
    assert added_error.message == message


def test_get_error_by_id(engine_error, test_session):
    """
    Тест получения ошибки по ID.
    """
    error_type = "Timeout"
    message = "The operation timed out."

    # Добавляем ошибку
    new_error = Error(error_type=error_type, message=message, timestamp=datetime.utcnow())
    test_session.add(new_error)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Проверяем получение ошибки по ID
    result = engine_error.get_error_by_id(new_error.id)
    assert result is not None, "Ошибка по ID не найдена"
    assert result.error_type == error_type
    assert result.message == message


def test_get_errors_by_type(engine_error, test_session):
    """
    Тест получения ошибок по типу.
    """
    error_type = "TestErrorType"
    message = "Test message"

    # Добавляем несколько ошибок
    for _ in range(3):
        new_error = Error(error_type=error_type, message=message, timestamp=datetime.utcnow())
        test_session.add(new_error)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Получаем ошибки по типу
    result = engine_error.get_errors_by_type(error_type)
    assert len(result) == 3, "Количество ошибок по типу не совпадает"
    assert all(error.error_type == error_type for error in result)


def test_get_recent_errors(engine_error, test_session):
    """
    Тест получения последних ошибок.
    """
    # Добавляем несколько ошибок
    error_type = "RecentError"
    for i in range(10):
        new_error = Error(error_type=error_type, message=f"Message {i}", timestamp=datetime.utcnow())
        test_session.add(new_error)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Получаем последние 5 ошибок
    result = engine_error.get_recent_errors(limit=5)
    assert len(result) == 5, "Количество последних ошибок неверно"
    assert all(error.error_type == error_type for error in result)


def test_delete_error_success(engine_error, test_session):
    """
    Тест успешного удаления ошибки.
    """
    # Добавляем ошибку
    error_to_delete = Error(error_type="DeleteTest", message="To be deleted", timestamp=datetime.utcnow())
    test_session.add(error_to_delete)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Удаляем ошибку
    result = engine_error.delete_error(error_to_delete.id)
    assert result is True, "Ошибка не была успешно удалена"

    # Проверяем, что ошибка удалена
    deleted_error = test_session.query(Error).filter_by(id=error_to_delete.id).first()
    assert deleted_error is None, "Удалённая ошибка всё ещё присутствует в базе данных"


def test_get_all_errors(engine_error, test_session):
    """
    Тест получения всех ошибок.
    """
    # Удаляем все существующие ошибки
    test_session.query(Error).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Добавляем новые ошибки
    for i in range(5):
        new_error = Error(error_type="AllErrorsTest", message=f"Error {i}", timestamp=datetime.utcnow())
        test_session.add(new_error)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем все ошибки
    result = engine_error.get_all_errors()
    assert len(result) == 5, "Количество всех ошибок неверно"
