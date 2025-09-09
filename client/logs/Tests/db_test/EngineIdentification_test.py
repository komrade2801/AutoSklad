import random

import pytest
from datetime import datetime

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Engine.IdentificationCRUD import EngineIdentification
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.UserCRUD import EngineUser
from DB.Models.Identification import Identification
from DB.Data.db import SessionLocal, engine
from DB.Models.User import User


# Фикстура для создания тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    return engine()


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineIdentification
@pytest.fixture
def engine_identification(test_session):
    """
    Создает экземпляр EngineIdentification с тестовой сессией.
    """
    return EngineIdentification(session=test_session)


@pytest.fixture
def engine_role(test_session):
    """
    Создаёт экземпляр EngineRole с тестовой сессией.
    """
    return EngineRole(test_session)


@pytest.fixture
def engine_user(test_session):
    """
    Создаёт экземпляр EngineRole с тестовой сессией.
    """
    return EngineUser(test_session)


@pytest.fixture
def sample_user(test_session, engine_role, engine_user, engine_identification, fake_data):
    """
    Создает тестовую роль для пользователя.
    """
    engine_role.delete_all()
    engine_user.delete_all()
    engine_identification.delete_all()

    engine_role.add_role(
            name="TestRole",
            description=""
        )
    role = engine_role.get_all_roles()[0]
    user = User(
        id=1,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )

    test_session.add(user)
    test_session.commit()
    return user


def test_add_identification_success(engine_identification, test_session, sample_user, engine_role, engine_user):
    """
    Тест успешного добавления записи идентификации.
    """

    datetime_value = datetime.utcnow()
    status = 1
    user_id = sample_user.id
    description = "Test identification"

    # Добавление записи
    result = engine_identification.add_identification(datetime_value, status, user_id, description)

    assert result is True, "Идентификация не была добавлена"

    # Проверка, что запись добавлена в базу данных
    added_identification = test_session.query(Identification).filter_by(User_id=user_id,
                                                                        Description=description).first()
    assert added_identification is not None, "Добавленная идентификация не найдена в базе данных"
    assert added_identification.Status == status
    assert added_identification.User_id == user_id
    assert added_identification.Description == description


def test_add_identification_without_description_success(engine_identification, test_session, sample_user):
    """
    Тест успешного добавления записи идентификации без описания.
    """
    datetime_value = datetime.utcnow()
    status = 1
    user_id = sample_user.id

    # Добавление записи без описания
    result = engine_identification.add_identification(datetime_value, status, user_id)

    assert result is True, "Идентификация без описания не была добавлена"

    # Проверка, что запись добавлена в базу данных
    added_identification = test_session.query(Identification).filter_by(User_id=user_id, Description=None).first()
    assert added_identification is not None, "Добавленная идентификация без описания не найдена в базе данных"


def test_get_identification_by_id(engine_identification, test_session, sample_user):
    """
    Тест получения идентификации по ID.
    """
    datetime_value = datetime.utcnow()
    status = 1
    user_id = sample_user.id
    description = "Test identification"

    # Добавление записи
    new_identification = Identification(datetime=datetime_value, Status=status, User_id=user_id,
                                        Description=description)
    test_session.add(new_identification)
    test_session.commit()

    # Получение идентификации по ID
    result = engine_identification.get_identification_by_id(new_identification.id)
    assert result is not None, "Идентификация по ID не найдена"
    assert result.Status == status
    assert result.User_id == user_id
    assert result.Description == description


def test_get_identifications_by_user_id(engine_identification, test_session, sample_user):
    """
    Тест получения идентификаций по ID пользователя.
    """
    user_id = sample_user.id
    datetime_value = datetime.utcnow()
    status = 1
    description = "Test identification"

    # Добавление нескольких записей
    for _ in range(3):
        new_identification = Identification(datetime=datetime_value, Status=status, User_id=user_id,
                                            Description=description)
        test_session.add(new_identification)
    test_session.commit()

    # Получение идентификаций по ID пользователя
    result = engine_identification.get_identifications_by_user_id(user_id)
    assert len(result) == 3, "Количество идентификаций по пользователю неверное"
    assert all(identification.User_id == user_id for identification in result)


# def test_get_identifications_by_status(engine_identification, test_session, sample_user):
#     """
#     Тест получения идентификаций по статусу.
#     """
#     status = 1
#     datetime_value = datetime.utcnow()
#     user_id = sample_user.id
#     description = "Test identification"
#
#     # Добавление нескольких записей с одинаковым статусом
#     for _ in range(3):
#         new_identification = Identification(datetime=datetime_value, Status=status, User_id=user_id,
#                                             Description=description)
#         test_session.add(new_identification)
#     test_session.commit()
#
#     # Получение идентификаций по статусу
#     result = engine_identification.get_identifications_by_status(status)
#     assert len(result) == 3, "Количество идентификаций с этим статусом неверное"
#     assert all(identification.Status == status for identification in result)


def test_update_identification_status_success(engine_identification, test_session, sample_user):
    """
    Тест успешного обновления статуса идентификации.
    """
    datetime_value = datetime.utcnow()
    status = 1
    user_id = sample_user.id
    description = "Test identification"

    # Добавление записи
    new_identification = Identification(datetime=datetime_value, Status=status, User_id=user_id,
                                        Description=description)
    test_session.add(new_identification)
    test_session.commit()

    # Обновление статуса идентификации
    new_status = 2
    result = engine_identification.update_identification_status(new_identification.id, new_status)

    assert result is True, "Статус идентификации не был обновлён"

    # Проверка обновленного статуса
    updated_identification = test_session.query(Identification).filter_by(id=new_identification.id).first()
    assert updated_identification.Status == new_status, "Статус идентификации не обновился"


def test_update_identification_description_success(engine_identification, test_session, sample_user):
    """
    Тест успешного обновления описания идентификации.
    """
    datetime_value = datetime.utcnow()
    status = 1
    user_id = sample_user.id
    description = "Test identification"

    # Добавление записи
    new_identification = Identification(datetime=datetime_value, Status=status, User_id=user_id,
                                        Description=description)
    test_session.add(new_identification)
    test_session.commit()

    # Обновление описания идентификации
    new_description = "Updated description"
    result = engine_identification.update_identification_description(new_identification.id, new_description)

    assert result is True, "Описание идентификации не было обновлено"

    # Проверка обновленного описания
    updated_identification = test_session.query(Identification).filter_by(id=new_identification.id).first()
    assert updated_identification.Description == new_description, "Описание идентификации не обновилось"


def test_delete_identification_success(engine_identification, test_session, sample_user):
    """
    Тест успешного удаления идентификации.
    """
    datetime_value = datetime.utcnow()
    status = 1
    user_id = sample_user.id
    description = "Test identification"

    # Добавление записи
    new_identification = Identification(datetime=datetime_value, Status=status, User_id=user_id,
                                        Description=description)
    test_session.add(new_identification)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаление записи
    result = engine_identification.delete_identification(new_identification.id)

    assert result is True, "Идентификация не была удалена"

    # Проверка, что запись удалена
    deleted_identification = test_session.query(Identification).filter_by(id=new_identification.id).first()
    assert deleted_identification is None, "Удалённая идентификация всё ещё присутствует в базе данных"


def test_get_all_identifications(engine_identification, test_session, sample_user):
    """
    Тест получения всех идентификаций.
    """
    # Удаляем все существующие записи
    test_session.query(Identification).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Добавление нескольких записей
    for i in range(5):
        new_identification = Identification(datetime=datetime.utcnow(), Status=1, User_id=i,
                                            Description=f"Description {i}")
        test_session.add(new_identification)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем все записи
    result = engine_identification.get_all_identifications()
    assert len(result) > 1, "Количество всех идентификаций неверное"
