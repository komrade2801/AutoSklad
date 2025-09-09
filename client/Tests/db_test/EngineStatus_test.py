import random

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Engine.StatusCRUD import EngineStatus
from DB.Models.Status import Status


# Фикстура для создания тестовой сессии
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


# Фикстура для экземпляра EngineStatus
@pytest.fixture
def engine_status(test_session):
    """
    Создает экземпляр EngineStatus с тестовой сессией.
    """
    return EngineStatus(session=test_session)


def test_add_status_success(engine_status, test_session):
    """
    Тест успешного добавления статуса.
    """
    stype = f"Active {random.randint(1, 999)}"
    description = "The status is active."
    engine_status.delete_all()
    result = engine_status.add(index=random.randint(1, 999), stype=stype, description=description)

    assert result is True, "Статус не был добавлен"

    # Проверяем, что статус добавлен в базу данных
    added_status = test_session.query(Status).filter_by(stype=stype, description=description).first()
    assert added_status is not None, "Добавленный статус не найден в базе данных"
    assert added_status.stype == stype
    assert added_status.description == description


def test_get_status_by_id(engine_status, test_session):
    """
    Тест получения статуса по ID.
    """
    stype = f"Inactive {random.randint(1, 999)}"
    description = "The status is inactive."

    # Добавляем статус
    new_status = Status(stype=stype, description=description)
    test_session.add(new_status)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Проверяем получение статуса по ID
    result = engine_status.get(new_status.id)
    assert result is not None, "Статус по ID не найден"
    assert result.stype == stype
    assert result.description == description


def test_get_all_statuses(engine_status, test_session):
    """
    Тест получения всех статусов.
    """
    # Добавляем несколько статусов
    stypes = [f"Active {random.randint(1, 999)}", f"Inactive {random.randint(1, 999)}",
              f"Pending {random.randint(1, 999)}"]
    descriptions = ["The status is active.", "The status is inactive.", "The status is pending."]

    for stype, description in zip(stypes, descriptions):
        new_status = Status(stype=stype, description=description)
        test_session.add(new_status)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем все статусы
    result = engine_status.all()
    assert len(result) > 1, "Количество статусов не совпадает"
    assert all(isinstance(status, Status) for status in result)


def test_update_status_success(engine_status, test_session):
    """
    Тест успешного обновления статуса.
    """
    # Добавляем статус
    stype = f"Active {random.randint(1, 999)}"
    description = "The status is active."
    new_status = Status(stype=stype, description=description)
    test_session.add(new_status)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Обновляем статус
    updated_stype = f"UpdatedActive {random.randint(1, 999)}"
    updated_description = "The status has been updated."
    result = engine_status.update(new_status.id, stype=updated_stype, description=updated_description)
    assert result is True, "Статус не был успешно обновлен"

    # Проверяем, что статус обновлен в базе данных
    updated_status = test_session.query(Status).filter_by(id=new_status.id).first()
    assert updated_status is not None, "Обновленный статус не найден"
    assert updated_status.stype == updated_stype
    assert updated_status.description == updated_description


def test_delete_status_success(engine_status, test_session):
    """
    Тест успешного удаления статуса.
    """
    # Добавляем статус
    stype = f"Active {random.randint(1, 999)}"
    description = "The status is active."
    status_to_delete = Status(stype=stype, description=description)
    test_session.add(status_to_delete)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаляем статус
    result = engine_status.delete(status_to_delete.id)
    assert result is True, "Статус не был успешно удален"

    # Проверяем, что статус удален
    deleted_status = test_session.query(Status).filter_by(id=status_to_delete.id).first()
    assert deleted_status is None, "Удалённый статус всё ещё присутствует в базе данных"


# def test_drop_table_status(engine_status, test_session):
#     """
#     Тест удаления таблицы Status.
#     """
#     # Проверяем, что таблица существует
#     assert test_session.query(Status).count() >= 0, "Таблица Status не существует"
#
#     # Удаляем таблицу
#     result = engine_status.drop()
#     assert result is True, "Таблица не была удалена"
#
#     # Проверяем, что таблица удалена
#     with pytest.raises(Exception):
#         test_session.query(Status).all()


def test_add_status_integrity_error(engine_status):
    """
    Тест на обработку IntegrityError при добавлении статуса с уже существующим значением.
    """
    stype = f"Active {random.randint(1, 999)}"
    description = "The status is active."

    # Добавляем первый статус
    result1 = engine_status.add(index=random.randint(1, 999), stype=stype, description=description)
    assert result1 is True, "Первый статус должен добавляться успешно."

    # Пробуем добавить статус с таким же stype
    result2 = engine_status.add(index=random.randint(1, 999), stype=stype, description="Another description")
    assert result2 is False, "Добавление статуса с уже существующим stype должно вернуть False."
    # engine_status.delete_all()
