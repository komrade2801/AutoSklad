import pytest
from unittest.mock import MagicMock
from DB.Models.User import User
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    return {
        "FirstName": "John",
        "SecondName": "Doe",
        "Family": "Single",
        "Code": 1234
    }


@pytest.fixture
def mapper():
    # Создаем объект ActionMapper и замокаем методы
    mapper = ActionMapper()
    mapper.e_user.get_user_by_code = MagicMock()
    return mapper


@pytest.fixture
def fake_user(fake_data):
    # Создаем фиктивного пользователя
    user = User(
        id=1,
        barcode="12345678",
        Code=fake_data["Code"],
        FirstName=fake_data["FirstName"],
        SecondName=fake_data["SecondName"],
        Family=fake_data["Family"],
        password="password",
        Role_id=1
    )
    return user


def test_read_db_username_success(mapper, fake_user):
    """
    Тест успешного получения имени пользователя по коду.
    """
    # Подготавливаем замок для метода
    mapper.e_user.get_user_by_code.return_value = fake_user

    # Выполняем тестируемую функцию
    result = mapper.read_db_username(fake_user.code)

    # Проверяем, что результат совпадает с ожидаемым
    expected_username = f"{fake_user.first_name} {fake_user.second_name} {fake_user.family}".strip()
    assert result == expected_username

    # Проверяем, что метод был вызван с правильным аргументом
    mapper.e_user.get_user_by_code.assert_called_once_with(fake_user.code)


def test_read_db_username_user_not_found(mapper):
    """
    Тест, когда пользователь не найден по коду.
    """
    # Настроим замок, чтобы он возвращал None
    mapper.e_user.get_user_by_code.return_value = None

    # Выполняем тестируемую функцию
    result = mapper.read_db_username(9999)  # Некорректный код

    # Проверяем, что возвращается None, так как пользователь не найден
    assert result is None

    # Проверяем, что метод был вызван с правильным аргументом
    mapper.e_user.get_user_by_code.assert_called_once_with(9999)


def test_read_db_username_empty_name(mapper, fake_data):
    """
    Тест, когда имя пользователя пустое.
    """
    # Создадим пользователя с пустым именем
    user_with_empty_name = User(
        id=2,
        barcode="87654321",
        Code=fake_data["Code"],
        FirstName="",
        SecondName="",
        Family="",
        password="password",
        Role_id=1
    )

    # Настроим замок для возврата этого пользователя
    mapper.e_user.get_user_by_code.return_value = user_with_empty_name

    # Выполняем тестируемую функцию
    result = mapper.read_db_username(fake_data["Code"])

    # Проверяем, что результат будет None, так как имя пустое
    assert result is None

    # Проверяем, что метод был вызван с правильным аргументом
    mapper.e_user.get_user_by_code.assert_called_once_with(fake_data["Code"])


def test_read_db_username_exception(mapper):
    """
    Тест, когда происходит ошибка при получении пользователя.
    """
    # Настроим замок, чтобы он вызывал исключение
    mapper.e_user.get_user_by_code.side_effect = Exception("Some error")

    # Выполняем тестируемую функцию
    result = mapper.read_db_username(1234)

    # Проверяем, что возвращается None в случае ошибки
    assert result is None

    # Проверяем, что метод был вызван с правильным аргументом
    mapper.e_user.get_user_by_code.assert_called_once_with(1234)
