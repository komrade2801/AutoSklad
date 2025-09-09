import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from DB.Models.Role import Role
from DB.Models.User import User
from DB.Models.History import History
from DB.Engine.RoleCRUD import EngineRole
from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Models.Rights import Rights


# Создаём движок базы данных в памяти для тестирования
@pytest.fixture(scope="module")
def test_engine():
    """
    Создаёт тестовый движок базы данных (в памяти).
    """
    return engine()


# Создаём тестовую сессию
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создаёт тестовую сессию SQLAlchemy.
    """
    return SessionLocal()


# Экземпляр класса EngineRole для тестирования
@pytest.fixture
def engine_role(test_session):
    """
    Создаёт экземпляр EngineRole с тестовой сессией.
    """
    return EngineRole(test_session)


def test_add_role_success(engine_role, test_session):
    """
    Тест успешного добавления роли.
    """

    # engine_role.delete_all()
    # engine_role.delete_all()

    name = "Admin"
    description = "Administrator role"

    result = engine_role.add_role(name=name, description=description)
    assert result is True, "Роль не была добавлена"

    added_role = test_session.query(Role).filter_by(name=name).first()
    assert added_role is not None, "Добавленная роль не найдена в базе данных"
    assert added_role.name == name
    assert added_role.description == description


def test_get_role_by_id(engine_role, test_session):
    """
    Тест получения роли по ID.
    """
    name = "Viewer"
    description = "View-only role"

    new_role = Role(name=name, description=description)
    test_session.add(new_role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_role.get_role_by_id(new_role.id)
    assert result is not None, "Роль по ID не найдена"
    assert result.Name == name
    assert result.Description == description


def test_update_role_success(engine_role, test_session):
    """
    Тест успешного обновления роли.
    """
    role = Role(name="OldRole", description="Old description")
    test_session.add(role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    updated_name = "UpdatedRole"
    updated_description = "Updated description"
    result = engine_role.update_role(role.id, name=updated_name, description=updated_description)

    assert result is True, "Роль не была обновлена"

    updated_role = test_session.query(Role).filter_by(id=role.id).first()
    assert updated_role.name == updated_name
    assert updated_role.description == updated_description


def test_delete_role_success(engine_role, test_session):
    """
    Тест успешного удаления роли.
    """
    role = Role(name="ToDelete", description="Temporary role")
    test_session.add(role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_role.delete_role(role.id)
    assert result is True, "Роль не была удалена"

    deleted_role = test_session.query(Role).filter_by(id=role.id).first()
    assert deleted_role is None, "Удалённая роль всё ещё присутствует в базе данных"


# def test_get_roles_with_rights(engine_role, test_session):
#     """
#     Тест получения всех ролей с правами доступа.
#     """
#     role = Role(Name="RoleWithRights", Description="Role with rights")
#     test_session.add(role)
#     test_session.commit()
#
#     result = engine_role.get_roles_with_rights()
#     assert len(result) > 0, "Роли с правами доступа не найдены"
#     assert role in result, "Ожидаемая роль отсутствует в результатах"

# TODO: test_get_users_with_role
# def test_get_users_with_role(engine_role, test_session):
#     """
#
#     Тест получения пользователей, связанных с ролью.
#     """
#     role = Role(Name="UserRole", Description="Role with users")
#     test_session.add(role)
#     test_session.commit()
#
#     user = User(FirstName="Test User", Role_id=role.id, SecondName="Test User SecondName", Family="Test User Family", barcode="1111111")
#     test_session.add(user)
#     test_session.commit()
#
#     result = engine_role.get_users_with_role(role.id)
#     assert len(result) == 1, "Количество связанных пользователей неверно"
#     assert result[0].first_name == "Test User", "Имя пользователя не совпадает"

# TODO: test_get_history_by_role
# def test_get_history_by_role(engine_role, test_session):
#     """
#     Тест получения истории, связанной с ролью.
#     """
#     role = Role(Name="HistoryRole", Description="Role with history")
#     test_session.add(role)
#     test_session.commit()
#
#     history = History(User_Role_id=role.id, Status="Created", datetime=datetime.utcnow())
#     test_session.add(history)
#     test_session.commit()
#
#     result = engine_role.get_history_by_role(role.id)
#     assert len(result) == 1, "Количество записей истории неверно"
#     assert result[0].Action == "Created", "Действие в истории не совпадает"


def test_get_child_roles(engine_role, test_session):
    """
    Тест получения дочерних ролей.
    """
    parent_role = Role(name="ParentRole", description="Parent role")
    test_session.add(parent_role)
    test_session.commit()

    child_role = Role(name="ChildRole", description="Child role", parent_role_id=parent_role.id)
    test_session.add(child_role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_role.get_child_roles(parent_role.id)
    assert len(result) == 1, "Количество дочерних ролей неверно"
    assert result[0].Name == "ChildRole", "Имя дочерней роли не совпадает"


def test_get_parent_role(engine_role, test_session):
    """
    Тест получения родительской роли.
    """
    parent_role = Role(name="ParentRole", description="Parent role")
    test_session.add(parent_role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    child_role = Role(name="ChildRole", description="Child role", parent_role_id=parent_role.id)
    test_session.add(child_role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_role.get_parent_role(child_role.id)
    assert result is not None, "Родительская роль не найдена"
    assert result.Name == "ParentRole", "Имя родительской роли не совпадает"


def test_get_all_roles(engine_role, test_session):
    """
    Тест получения всех ролей.
    """
    test_session.query(Role).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    for i in range(5):
        role = Role(name=f"Role {i}", description=f"Description {i}")
        test_session.add(role)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_role.get_all_roles()
    assert len(result) == 5, "Количество ролей неверно"
