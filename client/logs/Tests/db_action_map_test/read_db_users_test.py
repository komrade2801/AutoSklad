import pytest
from unittest.mock import MagicMock

from faker import Faker

from DB.Models.Role import Role
from DB.Models.User import User
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


@pytest.fixture
def mapper():
    # Создание объекта ActionMapper и мокирование методов
    mapper = ActionMapper()
    mapper.e_user.get_all_users = MagicMock()
    return mapper


@pytest.fixture
def fake_user_data(fake_data):
    # Создание фейкового пользователя для тестирования
    role_name = fake_data.job()
    role_description = fake_data.sentence()
    role = Role(
        id=1,
        Name=role_name,
        Description=role_description,
        ParentRole_id=None,
        parent_role=None,
    )

    return User(
        id=1,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )


def test_read_db_users_success(mapper, fake_user_data):
    """
    Тест успешного получения списка пользователей.
    """
    # Подготавливаем замок для метода get_all_users
    mapper.e_user.get_all_users.return_value = [fake_user_data]

    # Выполняем тестируемую функцию
    result = mapper.read_db_users()

    # Проверяем, что результат совпадает с ожидаемым
    assert len(result) == 1
    assert result[0].first_name == fake_user_data.first_name
    assert result[0].SecondName == fake_user_data.SecondName
    assert result[0].Family == fake_user_data.Family


def test_read_db_users_empty(mapper):
    """
    Тест получения пустого списка пользователей, если их нет в базе.
    """
    # Подготавливаем замок для метода get_all_users
    mapper.e_user.get_all_users.return_value = []

    # Выполняем тестируемую функцию
    result = mapper.read_db_users()

    # Проверяем, что результат - пустой список
    assert result == []


def test_read_db_users_exception(mapper):
    """
    Тест обработки ошибки при получении пользователей из базы.
    """
    # Подготавливаем замок, который вызывает исключение
    mapper.e_user.get_all_users.side_effect = Exception("Database error")

    # Выполняем тестируемую функцию
    result = mapper.read_db_users()

    # Проверяем, что результат - пустой список при ошибке
    assert result == []
