import pytest
from unittest.mock import MagicMock
from faker import Faker
from DB.Models.User import User
from DB.Models.Role import Role
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


@pytest.fixture
def mapper():
    # Создаём объект `ActionMapper` и замокаем методы движков
    mapper = ActionMapper()
    mapper.e_user.get_user_by_barcode = MagicMock()
    mapper.e_role.get_role_by_id = MagicMock()
    return mapper


@pytest.fixture
def fake_data_user(fake_data, mapper):
    role_name = fake_data.job()
    role_description = fake_data.sentence()
    role = Role(
        id=1,
        Name=role_name,
        Description=role_description,
        ParentRole_id=None,
        parent_role=None,
    )
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
    return user, role


def test_read_db_user_from_barcode_success(mapper, fake_data_user):
    """
    Тест успешного извлечения пользователя по штрихкоду.
    """
    user, role = fake_data_user
    # Подготовка моков
    mapper.e_user.get_user_by_barcode.return_value = user
    mapper.e_role.get_role_by_id.return_value = role

    # Выполнение действия
    result_user, result_role = mapper.read_db_user_from_barcode(user.barcode)

    # Проверка результата
    assert result_user == user
    assert result_role == role

    # Проверка вызовов методов
    mapper.e_user.get_user_by_barcode.assert_called_once_with(user.barcode)
    mapper.e_role.get_role_by_id.assert_called_once_with(user.role_id)


def test_read_db_user_from_barcode_user_not_found(mapper, fake_data):
    """
    Тест, когда пользователь не найден по штрихкоду.
    """
    barcode = fake_data.ean(length=8)
    # Подготовка моков
    mapper.e_user.get_user_by_barcode.return_value = None

    # Выполнение действия
    result_user, result_role = mapper.read_db_user_from_barcode(barcode)

    # Проверка результата
    assert result_user is None
    assert result_role is None

    # Проверка вызова метода
    mapper.e_user.get_user_by_barcode.assert_called_once_with(barcode)


def test_read_db_user_from_barcode_role_not_found(mapper, fake_data_user):
    """
    Тест, когда роль пользователя не найдена.
    """
    user, _ = fake_data_user
    # Подготовка моков
    mapper.e_user.get_user_by_barcode.return_value = user
    mapper.e_role.get_role_by_id.return_value = None

    # Выполнение действия
    result_user, result_role = mapper.read_db_user_from_barcode(user.barcode)

    # Проверка результата
    assert result_user == user
    assert result_role is None

    # Проверка вызова методов
    mapper.e_user.get_user_by_barcode.assert_called_once_with(user.barcode)
    mapper.e_role.get_role_by_id.assert_called_once_with(user.role_id)


def test_read_db_user_from_barcode_exception(mapper):
    """
    Тест, когда возникает исключение при попытке извлечь пользователя.
    """
    # Подготовка моков для исключения
    mapper.e_user.get_user_by_barcode.side_effect = Exception("Database error")

    # Выполнение действия
    result_user, result_role = mapper.read_db_user_from_barcode(1234)

    # Проверка результата
    assert result_user is None
    assert result_role is None

    # Проверка вызова метода
    mapper.e_user.get_user_by_barcode.assert_called_once_with(1234)
