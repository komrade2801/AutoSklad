import random

import pytest
from datetime import datetime

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser
from DB.Models.Group import Group
from DB.Models.History import History
from DB.Models.User import User
from DB.Models.Role import Role
from DB.Models.Tools import Tools
from DB.Models.Plan import Plan
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Data.db import SessionLocal
from DB.Data.db import engine


# Фикстура для настройки тестовой базы данных
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
    # SessionLocal.configure(bind=test_engine)
    return SessionLocal()


# Фикстура для создания экземпляра EngineHistory
@pytest.fixture
def engine_history(test_session):
    """
    Создает экземпляр EngineHistory с тестовой сессией.
    """
    return EngineHistory(session=test_session)


# Фикстура для экземпляра EngineStatus
@pytest.fixture
def engine_status(test_session):
    """
    Создает экземпляр EngineStatus с тестовой сессией.
    """
    return EngineStatus(session=test_session)


@pytest.fixture
def engine_group(test_session):
    """
    Создает экземпляр EngineGroup с тестовой сессией.
    """
    return EngineGroup(session=test_session)


# Фикстура для создания экземпляра EngineTools
@pytest.fixture
def engine_tools(test_session):
    """
    Создает экземпляр EngineTools с тестовой сессией.
    """
    return EngineTools(test_session)


@pytest.fixture
def engine_cell(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


# Экземпляр класса EngineRole для тестирования
@pytest.fixture
def engine_role(test_session):
    """
    Создаёт экземпляр EngineRole с тестовой сессией.
    """
    return EngineRole(test_session)


# Фикстура для экземпляра EngineUser
@pytest.fixture
def engine_user(test_session):
    """
    Создает экземпляр EngineUser с тестовой сессией.
    """
    return EngineUser(session=test_session)


# Фикстура для экземпляра EnginePlan
@pytest.fixture
def engine_plan(test_session):
    """
    Создает экземпляр EnginePlan с тестовой сессией.
    """
    return EnginePlan(session=test_session)


@pytest.fixture
def engine_cells(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


@pytest.fixture
def setup_data(test_session, engine_group, engine_role, engine_cells, engine_user, engine_plan, engine_tools,
               engine_status, fake_data):
    """
    Создает необходимые тестовые данные: пользователя, роль, инструмент, план.
    """
    engine_group.delete_all()
    engine_role.delete_all()
    engine_cells.delete_all()
    engine_user.delete_all()
    engine_plan.delete_all()
    engine_tools.delete_all()
    engine_status.delete_all()

    group = Group(id=random.randint(1, 9999), name="Old Group", description="Old Description", status=0)
    role = Role(id=random.randint(1, 9999), Name="Admin", Description="root user")
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

    plan = Plan(
        id=random.randint(1, 9999),
        enterprise="TestEnterprise",
        barcode="1234567890123",
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    tool = Tools(
        id=random.randint(1, 9999),
        barcode="67890",
        name="Молоток",
        description="Плоский",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(tool)
    test_session.add(user)
    test_session.add(role)
    test_session.add(plan)
    test_session.commit()

    return user, role, tool, plan


def test_add_history_success(engine_history, test_session, setup_data):
    """
    Тест успешного добавления записи в историю.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем запись истории
    result = engine_history.add_history(
        id=random.randint(1, 999),
        user_id=user.id,
        role_id=role.id,
        tools_id=tool.id,
        datetime_value=datetime_value,
        status=1,
        description="Test action",
        # plan_id=plan.id
    )
    assert result is True, "История не была добавлена"

    # Проверяем, что запись добавлена в базу данных
    history_entry = test_session.query(History).filter_by(user_id=user.id, tools_id=tool.id).first()
    assert history_entry is not None, "Запись истории не найдена в базе данных"
    assert history_entry.user_id == user.id
    assert history_entry.user_role_id == role.id
    assert history_entry.tools_id == tool.id


def test_get_history_by_id(engine_history, test_session, setup_data):
    """
    Тест получения записи истории по ID.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем запись истории
    engine_history.add_history(
        id=random.randint(1, 999),
        user_id=user.id,
        role_id=role.id,
        tools_id=tool.id,
        datetime_value=datetime_value,
        status=1,
        description="Test action",
        # plan_id=plan.id
    )

    # Получаем запись по ID
    history_entry = test_session.query(History).first()
    result = engine_history.get_history_by_id(history_entry.id)
    assert result is not None, "Запись истории по ID не найдена"
    assert result.id == history_entry.id


def test_get_history_by_user(engine_history, test_session, setup_data):
    """
    Тест получения записей истории по пользователю.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем несколько записей истории
    for _ in range(3):
        engine_history.add_history(
            id=random.randint(1, 999),
            user_id=user.id,
            role_id=role.id,
            tools_id=tool.id,
            datetime_value=datetime_value,
            status=1,
            description="Test action",
            # plan_id=plan.id
        )

    # Получаем все записи по пользователю
    history_entries = engine_history.get_history_by_user(user.id)
    assert len(history_entries) >= 3, "Количество записей истории по пользователю неверно"
    assert all(entry.user_id == user.id for entry in history_entries)


def test_get_history_by_role(engine_history, test_session, setup_data):
    """
    Тест получения записей истории по роли.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем несколько записей истории
    for _ in range(3):
        engine_history.add_history(
            id=random.randint(1, 999),
            user_id=user.id,
            role_id=role.id,
            tools_id=tool.id,
            datetime_value=datetime_value,
            status=1,
            description="Test action",
            # plan_id=plan.id
        )

    # Получаем все записи по роли
    history_entries = engine_history.get_history_by_role(role.id)
    assert len(history_entries) >= 2, "Количество записей истории по роли неверно"
    assert all(entry.user_role_id == role.id for entry in history_entries)


def test_get_history_by_tool(engine_history, test_session, setup_data):
    """
    Тест получения записей истории по инструменту.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем несколько записей истории
    for _ in range(3):
        engine_history.add_history(
            id=random.randint(1, 999),
            user_id=user.id,
            role_id=role.id,
            tools_id=tool.id,
            datetime_value=datetime_value,
            status=1,
            description="Test action",
            # plan_id=plan.id
        )

    # Получаем все записи по инструменту
    history_entries = engine_history.get_history_by_tool(tool.id)
    assert len(history_entries) >= 1, "Количество записей истории по инструменту неверно"
    assert all(entry.tools_id == tool.id for entry in history_entries)


# def test_get_history_by_plan(engine_history, test_session, setup_data):
#     """
#     Тест получения записей истории по чертежу.
#     """
#     user, role, tool, plan = setup_data
#     datetime_value = datetime.now()
#
#     # Добавляем несколько записей истории
#     for _ in range(3):
#         engine_history.add_history(
#             user_id=user.id, role_id=role.id, tools_id=tool.id,
#             datetime_value=datetime_value, status=1, description="Test action", plan_id=plan.id
#         )
#
#     # Получаем все записи по чертежу
#     history_entries = engine_history.get_history_by_plan(plan.id)
#     assert len(history_entries) == 3, "Количество записей истории по чертежу неверно"
#     assert all(entry.Plan_id == plan.id for entry in history_entries)


def test_update_history_success(engine_history, test_session, setup_data):
    """
    Тест успешного обновления записи истории.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем запись истории
    engine_history.add_history(
        id=random.randint(1, 999),
        user_id=user.id,
        role_id=role.id,
        tools_id=tool.id,
        datetime_value=datetime_value,
        status=1,
        description="Test action",
        # plan_id=plan.id
    )

    # Получаем первую запись
    history_entry = test_session.query(History).first()

    # Обновляем запись
    updated = engine_history.update_history(history_entry.id, status=2, description="Updated action")
    assert updated is True, "История не была обновлена"

    # Проверяем обновленные данные
    updated_entry = test_session.query(History).get(history_entry.id)
    assert updated_entry.status >= 2
    assert updated_entry.description == "Updated action"


def test_delete_history_success(engine_history, test_session, setup_data):
    """
    Тест успешного удаления записи истории.
    """
    user, role, tool, plan = setup_data
    datetime_value = datetime.now()

    # Добавляем запись истории
    engine_history.add_history(
        id=random.randint(1, 999),
        user_id=user.id,
        role_id=role.id,
        tools_id=tool.id,
        datetime_value=datetime_value,
        status=1,
        description="Test action",
        # plan_id=plan.id
    )

    # Получаем первую запись
    history_entry = test_session.query(History).first()

    # Удаляем запись
    deleted = engine_history.delete_history(history_entry.id)
    assert deleted is True, "История не была удалена"

    # Проверяем, что запись удалена
    deleted_entry = test_session.query(History).get(history_entry.id)
    assert deleted_entry is None, "Удалённая запись всё ещё присутствует в базе данных"

# def test_get_history_with_relations(engine_history, test_session, setup_data):
#     """
#     Тест получения истории с подгрузкой связанных данных.
#     """
#     user, role, tool, plan = setup_data
#     datetime_value = datetime.now()
#
#     # Добавляем запись истории
#     engine_history.add_history(
#         id=random.randint(1, 999),
#         user_id=user.id,
#         role_id=role.id,
#         tools_id=tool.id,
#         datetime_value=datetime_value,
#         status=1,
#         description="Test action",
#         # plan_id=plan.id
#     )
#
#     # Получаем запись с подгрузкой всех связанных данных
#     history_entries = engine_history.get_history_with_relations()
#     assert len(history_entries) > 0, "История не была получена"
#     assert all(entry.users is not None for entry in history_entries), "Связанные данные пользователя не подгружены"
#     assert all(entry.tools is not None for entry in history_entries), "Связанные данные инструмента не подгружены"
#     assert all(entry.role is not None for entry in history_entries), "Связанные данные роли не подгружены"
