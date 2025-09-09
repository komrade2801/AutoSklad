import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Engine.RightsCRUD import EngineRights
from DB.Models.Rights import Rights
from DB.Data.db import SessionLocal, engine
from DB.Models.Role import Role


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
    return SessionLocal()


# Фикстура для экземпляра EngineRights
@pytest.fixture
def engine_rights(test_session):
    """
    Создает экземпляр EngineRights с тестовой сессией.
    """
    return EngineRights(session=test_session)


@pytest.fixture
def sample_role(test_session):
    """
    Создает тестовую роль для пользователя.
    """
    role = Role(Name="TestRole", Description="")
    test_session.add(role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise
    return role


def test_add_right_success(engine_rights, test_session, sample_role):
    """
    Тест успешного добавления права доступа.
    """
    engine_rights.delete_all()
    name = "TestRight"
    description = "Test description"
    role_id = sample_role.id

    right_indx = engine_rights.get_all_ids()
    right_indx = max(right_indx) + 1 if right_indx else 1

    result = engine_rights.add_right(
        right_indx,
        name,
        description,
        role_id
    )

    assert result is True, "Право доступа не было добавлено"

    # Проверяем, что право добавлено в базу данных
    added_right = test_session.query(Rights).filter_by(Name=name, Description=description, Role_id=role_id).first()
    assert added_right is not None, "Добавленное право не найдено в базе данных"
    assert added_right.Name == name
    assert added_right.Description == description
    assert added_right.role_id == role_id


def test_get_right_by_id(engine_rights, test_session, sample_role):
    """
    Тест получения права доступа по ID.
    """
    name = "TestRight"
    description = "Test description"
    role_id = sample_role.id
    new_right = Rights(Name=name, Description=description, Role_id=role_id)
    test_session.add(new_right)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Проверяем получение права по ID
    result = engine_rights.get_right_by_id(new_right.id)
    assert result is not None, "Право по ID не найдено"
    assert result.Name == name
    assert result.Description == description
    assert result.role_id == role_id


def test_get_rights_by_role_id(engine_rights, test_session, sample_role):
    """
    Тест получения прав доступа по role_id.
    """
    role_id = sample_role.id
    rights_data = [
        Rights(Name="Right1", Description="Description1", Role_id=role_id),
        Rights(Name="Right2", Description="Description2", Role_id=role_id)
    ]
    test_session.add_all(rights_data)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем права по role_id
    result = engine_rights.get_rights_by_role_id(role_id)
    assert len(result) >= 2, "Количество прав по роли не совпадает"
    assert all(right.role_id == role_id for right in result)


def test_update_right_success(engine_rights, test_session, sample_role):
    """
    Тест успешного обновления права доступа.
    """
    name = "TestRight"
    description = "Test description"
    role_id = sample_role.id
    new_right = Rights(Name=name, Description=description, Role_id=role_id)
    test_session.add(new_right)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Обновляем данные права
    updated_name = "UpdatedTestRight"
    updated_description = "Updated description"
    result = engine_rights.update_right(new_right.id, name=updated_name, description=updated_description)

    assert result is True, "Право доступа не было обновлено"

    # Проверяем, что данные обновились в базе
    updated_right = test_session.query(Rights).filter_by(id=new_right.id).first()
    assert updated_right.Name == updated_name
    assert updated_right.Description == updated_description


def test_delete_right_success(engine_rights, test_session, sample_role):
    """
    Тест успешного удаления права доступа.
    """
    name = "DeleteRight"
    description = "To be deleted"
    role_id = sample_role.id
    right_to_delete = Rights(Name=name, Description=description, Role_id=role_id)
    test_session.add(right_to_delete)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаляем право
    result = engine_rights.delete_right(right_to_delete.id)
    assert result is True, "Право доступа не было успешно удалено"

    # Проверяем, что право удалено
    deleted_right = test_session.query(Rights).filter_by(id=right_to_delete.id).first()
    assert deleted_right is None, "Удалённое право всё ещё присутствует в базе данных"


def test_get_all_rights(engine_rights, test_session):
    """
    Тест получения всех прав доступа.
    """
    # Удаляем все существующие права
    test_session.query(Rights).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Добавляем новые права
    for i in range(5):
        new_right = Rights(Name=f"Right{i}", Description=f"Description {i}", Role_id=1)
        test_session.add(new_right)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем все права
    result = engine_rights.get_all_rights()
    assert len(result) >= 5, "Количество всех прав неверно"


def test_get_rights_with_role(engine_rights, test_session, sample_role):
    """
    Тест получения прав с предзагруженными данными о роли.
    """
    alls = engine_rights.get_all_rights()
    for role in alls:
        engine_rights.delete(role.id)
    role_id = sample_role.id
    right_data = [
        Rights(Name="RightWithRole1", Description="Description1", Role_id=role_id),
        Rights(Name="RightWithRole2", Description="Description2", Role_id=role_id)
    ]
    test_session.add_all(right_data)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем права с предзагруженными данными о роли
    result = engine_rights.get_rights_with_role()
    assert len(result) >= 2, "Количество прав с ролью неверное"
    # for right in result:
    #     if right.role_id != role_id:
    #         raise AssertionError(
    #             f"Неверное значение Role_id для права {right.Name}. Ожидалось {role_id}, получено {right.role_id}.")
    assert all(right.role_id == role_id for right in result)



def test_search_rights_success(engine_rights, test_session):
    """
    Тест поиска прав доступа по подстроке в названии.
    """
    right_data = [
        Rights(Name="ReadAccess", Description="Read access description", Role_id=1),
        Rights(Name="WriteAccess", Description="Write access description", Role_id=2)
    ]
    test_session.add_all(right_data)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Поиск прав по подстроке в названии
    search_substring = "Read"
    result = engine_rights.search_rights(search_substring)
    assert len(result) >= 1, "Поиск по правам не дал ожидаемого результата"
    assert result[0].Name == "ReadAccess"
