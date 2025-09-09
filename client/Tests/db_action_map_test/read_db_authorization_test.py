import pytest
from unittest.mock import MagicMock
from DB.Models.User import User
from DB.Models.Role import Role
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    return {
        'login': 1234,  # Пример логина
        'password': 'password123',  # Пример пароля
    }


@pytest.fixture
def mapper():
    # Создаём объект `ActionMapper` и замокаем методы движков
    mapper = ActionMapper()
    mapper.e_user.get_user_by_code = MagicMock()
    mapper.e_role.get_role_by_id = MagicMock()
    return mapper


@pytest.fixture
def user_data():
    # Создаём фейковые данные пользователя и роли
    role = Role(id=1, Name='Admin', Description='Administrator role', ParentRole_id=None)
    user = User(
        id=1,
        barcode='12345678',
        Code=1234,
        FirstName='John',
        password='password123',  # Пароль должен совпасть с test_data['password']
        SecondName='Doe',
        Family="Single",
        Role_id=role.id
    )
    return user, role


def test_read_db_authorization_success(mapper, fake_data, user_data):
    """
    Тест успешной авторизации.
    """
    user, role = user_data

    # Настроим моки для получения пользователя и роли
    mapper.e_user.get_user_by_code.return_value = user
    mapper.e_role.get_role_by_id.return_value = role

    # Выполнение действия
    result_user, result_role = mapper.read_db_authorization(fake_data['login'], fake_data['password'])

    # Проверка результата
    assert result_user == user
    assert result_role == role
    mapper.e_user.get_user_by_code.assert_called_once_with(fake_data['login'])
    mapper.e_role.get_role_by_id.assert_called_once_with(user.role_id)


def test_read_db_authorization_invalid_password(mapper, fake_data, user_data):
    """
    Тест ошибки из-за неверного пароля.
    """
    user, role = user_data

    # Настроим моки для получения пользователя и роли
    mapper.e_user.get_user_by_code.return_value = user
    mapper.e_role.get_role_by_id.return_value = role

    # Выполнение действия с неверным паролем
    result_user, result_role = mapper.read_db_authorization(fake_data['login'], 'wrongpassword')

    # Проверка результата
    assert result_user is None
    assert result_role is None
    mapper.e_user.get_user_by_code.assert_called_once_with(fake_data['login'])


def test_read_db_authorization_user_not_found(mapper, fake_data):
    """
    Тест ошибки из-за отсутствия пользователя с таким логином.
    """
    # Настроим мок для отсутствия пользователя
    mapper.e_user.get_user_by_code.return_value = None

    # Выполнение действия
    result_user, result_role = mapper.read_db_authorization(fake_data['login'], fake_data['password'])

    # Проверка результата
    assert result_user is None
    assert result_role is None
    mapper.e_user.get_user_by_code.assert_called_once_with(fake_data['login'])


def test_read_db_authorization_exception_handling(mapper, fake_data):
    """
    Тест обработки исключения при выполнении запроса.
    """
    # Настроим мок, чтобы при вызове метода возникло исключение
    mapper.e_user.get_user_by_code.side_effect = Exception("Database error")

    # Выполнение действия
    result_user, result_role = mapper.read_db_authorization(fake_data['login'], fake_data['password'])

    # Проверка результата
    assert result_user is None
    assert result_role is None
    mapper.e_user.get_user_by_code.assert_called_once_with(fake_data['login'])
