import random

import pytest
from datetime import datetime

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Models.User import User
from DB.Models.Role import Role
from DB.Models.History import History
from DB.Models.Identification import Identification
from DB.Engine.UserCRUD import EngineUser
from DB.Data.db import SessionLocal, engine


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


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


# Фикстура для экземпляра EngineUser
@pytest.fixture
def engine_user(test_session):
    """
    Создает экземпляр EngineUser с тестовой сессией.
    """
    return EngineUser(session=test_session)


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


def test_add_user_success(engine_user, test_session, sample_role, fake_data):
    """
    Тест успешного добавления пользователя.
    """
    engine_user.delete_all()

    user_id = engine_user.get_all_ids()
    user_id = max(user_id) + 1 if user_id else 1

    _index = user_id
    _barcode = int(fake_data.ean())
    _code = fake_data.random_number(digits=4)
    _first_name = fake_data.first_name()
    _second_name = fake_data.last_name()
    _family = "Single"
    _password = str(fake_data.random_number(digits=4))
    _role_id = sample_role.id

    result = engine_user.add_user(
        index=_index,  # user_id,
        barcode=_barcode,  # int(fake_data.ean()),
        code=_code,  # fake_data.random_number(digits=4),
        first_name=_first_name,  # fake_data.first_name(),
        second_name=_second_name,  # fake_data.last_name(),
        family=_family,  # "Single",
        password=_password,  # str(fake_data.random_number(digits=4)),
        role_id=_role_id,  # sample_role.id
    )

    assert result is True, "Пользователь не был добавлен"
    user = engine_user.get_user_by_id(user_id)
    # Проверяем, что пользователь добавлен в базу данных
    added_user = test_session.query(User).filter_by(barcode=user.barcode).first()
    assert added_user is not None, "Добавленный пользователь не найден в базе данных"
    assert added_user.first_name == _first_name
    assert added_user.second_name == _second_name
    assert added_user.family == _family
    assert added_user.barcode == _barcode
    assert added_user.role_id == _role_id
    # test_session.query(User).delete()


def test_get_user_by_id(engine_user, test_session, sample_role, fake_data):
    """
    Тест получения пользователя по ID.
    """
    user_id = engine_user.get_all_ids()
    user_id = max(user_id) + 1 if user_id else 1

    user = User(
        id=user_id,
        barcode=fake_data.ean(),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=sample_role.id
    )

    test_session.add(user)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_user.get_user_by_id(user.id)
    assert result is not None, "Пользователь не найден по ID"
    assert result.id == user.id
    assert result.first_name == user.first_name
    assert result.SecondName == user.second_name
    # test_session.query(User).delete()


def test_get_all_users(engine_user, test_session, sample_role, fake_data):
    """
    Тест получения всех пользователей.
    """
    for i in range(5):
        user_id = engine_user.get_all_ids()
        user_id = max(user_id) + 1 if user_id else 1

        user = User(
            id=user_id,
            barcode=fake_data.ean(),
            Code=fake_data.random_number(digits=4),
            FirstName=fake_data.first_name(),
            password=str(fake_data.random_number(digits=4)),
            SecondName=fake_data.last_name(),
            Family="Single",
            Role_id=sample_role.id
        )
        test_session.add(user)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_user.get_all_users(limit=10)
    assert len(result) > 2, "Количество пользователей не совпадает"
    assert all(isinstance(user, User) for user in result)
    # test_session.query(User).delete()


def test_update_user_success(engine_user, test_session, sample_role, fake_data):
    """
    Тест успешного обновления пользователя.
    """
    user_id = engine_user.get_all_ids()
    user_id = max(user_id) + 1 if user_id else 1

    user = User(
        id=user_id,
        barcode=fake_data.ean(),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=sample_role.id
    )
    test_session.add(user)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    updated_data = {"FirstName": "Jane", "SecondName": "Smith"}
    result = engine_user.update_user(user.id, **updated_data)

    assert result is True, "Пользователь не был обновлен"

    updated_user = test_session.query(User).filter_by(id=user.id).first()
    assert updated_user.first_name == "Jane"
    assert updated_user.second_name == "Smith"
    # test_session.query(User).delete()


def test_delete_user_success(engine_user, test_session, sample_role, fake_data):
    """
    Тест успешного удаления пользователя.
    """
    user_id = engine_user.get_all_ids()
    user_id = max(user_id) + 1 if user_id else 1

    user = User(
        id=user_id,
        barcode=fake_data.ean(),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=sample_role.id
    )
    test_session.add(user)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_user.delete_user(user.id)
    assert result is True, "Пользователь не был успешно удален"

    deleted_user = test_session.query(User).filter_by(id=user.id).first()
    assert deleted_user is None, "Удаленный пользователь все еще присутствует в базе данных"


def test_get_users_with_role(engine_user, test_session, sample_role, fake_data):
    """
    Тест получения пользователей по роли.
    """
    users = []
    for i in range(3):
        user_id = engine_user.get_all_ids()
        user_id = max(user_id) + 1 if user_id else 1

        user = User(
            id=user_id,
            barcode=fake_data.ean(),
            Code=fake_data.random_number(digits=4),
            FirstName=fake_data.first_name(),
            password=str(fake_data.random_number(digits=4)),
            SecondName=fake_data.last_name(),
            Family="Single",
            Role_id=sample_role.id
        )
        test_session.add(user)
        users.append(user)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_user.get_users_with_role(sample_role.id)
    assert len(result) == 3, "Количество пользователей с указанной ролью не совпадает"
    assert all(user.role_id == sample_role.id for user in result)
    # test_session.query(User).delete()


# def test_get_user_history(engine_user, test_session, sample_role):
#     """
#     Тест получения истории пользователя.
#     """
#     user = User(FirstName="John", SecondName="Doe", Family="Single", barcode="12345", Role_id=sample_role.id)
#     test_session.add(user)
#     test_session.commit()
#
#     history = History(user_id=user.id, action="Login", timestamp=datetime.utcnow())
#     test_session.add(history)
#     test_session.commit()
#
#     result = engine_user.get_user_history(user.id)
#     assert len(result) == 1, "История пользователя не возвращается"
#     assert result[0].action == "Login"
#     # engine_user.d


def test_search_users_by_name(engine_user, test_session, sample_role, fake_data):
    """
    Тест поиска пользователей по имени.
    """
    for i in range(3):
        user_id = engine_user.get_all_ids()
        user_id = max(user_id) + 1 if user_id else 1

        user = User(
            id=user_id,
            barcode=fake_data.ean(),
            Code=fake_data.random_number(digits=4),
            FirstName=fake_data.first_name(),
            password=str(fake_data.random_number(digits=4)),
            SecondName=fake_data.last_name(),
            Family="Single",
            Role_id=sample_role.id
        )
        test_session.add(user)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    user_id = engine_user.get_all_ids()[0]
    users = engine_user.get_user_by_id(user_id)
    result = engine_user.search_users_by_name(users.first_name)
    assert len(result) >= 1, "Поиск по имени не дал ожидаемого результата"
    assert result[0].first_name == users.first_name
    # test_session.query(User).delete()

# def test_get_user_with_full_relationships(engine_user, test_session, sample_role):
#     """
#     Тест получения пользователя с полными связями (роли, истории, идентификации).
#     """
#     user = User(FirstName="John", SecondName="Doe", Family="Single", barcode="12345", Role_id=sample_role.id)
#     test_session.add(user)
#     test_session.commit()
#
#     history = History(user_id=user.id, action="Login", timestamp=datetime.utcnow())
#     test_session.add(history)
#
#     identification = Identification(user_id=user.id, identification_type="Fingerprint", value="12345")
#     test_session.add(identification)
#
#     test_session.commit()
#
#     result = engine_user.get_user_with_full_relationships(user.id)
#     assert result is not None, "Пользователь с полными связями не найден"
#     assert len(result.stories) == 1, "История не загружена"
#     assert len(result.identifications) == 1, "Идентификация не загружена"

# Дополнительные тесты можно добавить для других методов в классе.
