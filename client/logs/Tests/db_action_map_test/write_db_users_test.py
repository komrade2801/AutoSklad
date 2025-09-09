import pytest
from unittest.mock import MagicMock
from faker import Faker
from DB.Models.Role import Role
from DB.Models.User import User
from DB.Models.Rights import Rights
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


@pytest.fixture
def mapper():
    # Создаём объект `ActionMapper` и замокаем методы движков
    mapper = ActionMapper()
    mapper.e_role.add_role = MagicMock(return_value=1)
    mapper.e_rights.add_right = MagicMock(return_value=True)
    mapper.e_user.add_user = MagicMock(return_value=1)
    return mapper


@pytest.fixture
def fake_data_user(fake_data, mapper):
    user_data = {}
    role_name = fake_data.job()
    role_description = fake_data.sentence()

    roles_indx = mapper.e_role.get_all_ids()
    roles_indx = max(roles_indx) + 1 if roles_indx else 1
    role = Role(
        id=roles_indx,
        Name=role_name,
        Description=role_description,
        ParentRole_id=None,
        parent_role=None,
    )
    users_indx = mapper.e_user.get_all_ids()
    users_indx = max(users_indx) + 1 if users_indx else 1
    user = User(
        id=users_indx,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )
    rights_indx = mapper.e_rights.get_all_ids()
    rights_indx = max(rights_indx) + 1 if rights_indx else 1

    rights = Rights(
        id=rights_indx,
        Name=fake_data.job(),
        Description=fake_data.job_male(),
        Role_id=role.id,
    )
    user_data['user'] = user
    user_data["role"] = role
    user_data["rights"] = rights
    return user_data


def test_execute_write_db_users_success(mapper, fake_data_user):
    """
    Тест успешного добавления пользователя через execute.
    """
    # Выполнение действия
    result = mapper.execute('write_db_users', fake_data_user)

    # Проверка результата
    assert result is True
    role = fake_data_user["role"]
    rights = fake_data_user["rights"]
    user = fake_data_user["user"]

    # Проверка вызовов методов
    mapper.e_role.add_role.assert_called_once_with(
        name=role.name,
        description=role.description,
        parent_role_id=None
    )
    mapper.e_rights.add_right.assert_any_call(
        index=rights.id,
        name=rights.Name,
        description=rights.Description,
        role_id=role.id
    )
    mapper.e_user.add_user.assert_called_once_with(
        index=user.id,
        barcode=user.barcode,
        code=user.code,
        first_name=user.first_name,
        second_name=user.second_name,
        family=user.family,
        password=user.password,
        role_id=user.role_id
    )


def test_execute_write_db_users_missing_role(mapper, fake_data):
    """
    Тест ошибки из-за отсутствия данных о роли через execute.
    """
    user_data = {
        "first_name": fake_data.first_name(),
        "second_name": fake_data.last_name(),
        "family": "Single",
        "barcode": fake_data.ean(length=8),
        "rights": [{"name": "Delete", "description": "Access to delete"}],
    }

    # Выполнение действия
    result = mapper.execute('write_db_users', user_data)

    # Проверка результата
    assert result is False


def test_execute_write_db_users_missing_rights(mapper, fake_data_user):
    """
    Тест ошибки из-за отсутствия прав пользователя через execute.
    """
    # Убираем права из fake_data_user
    fake_data_user['rights'] = None

    # Выполнение действия
    result = mapper.execute('write_db_users', fake_data_user)

    # Проверка результата
    assert result is False
