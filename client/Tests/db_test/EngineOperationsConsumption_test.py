import random
import pytest
import datetime

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser
from DB.Models.Cell import Cell
from DB.Models.Consumption import Consumption
from DB.Models.Group import Group
from DB.Models.History import History
from DB.Models.OperationsConsumption import OperationsConsumption
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption
from sqlalchemy.exc import IntegrityError

from DB.Models.Plan import Plan
from DB.Models.Role import Role
from DB.Models.Status import Status
from DB.Models.Tools import Tools
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
    # Session = sessionmaker(bind=test_engine)
    return SessionLocal()


# Фикстура для экземпляра EngineOperationsConsumption
@pytest.fixture
def engine_operations_consumption(test_session):
    """
    Создает экземпляр EngineOperationsConsumption с тестовой сессией.
    """
    return EngineOperationsConsumption(session=test_session)


# Фикстура для создания экземпляра EngineGroup
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


# Фикстура для экземпляра EngineCell
@pytest.fixture
def engine_cell(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


# Фикстура для создания экземпляра EngineHistory
@pytest.fixture
def engine_history(test_session):
    """
    Создает экземпляр EngineHistory с тестовой сессией.
    """
    return EngineHistory(session=test_session)


# Фикстура для экземпляра EnginePlan
@pytest.fixture
def engine_plan(test_session):
    """
    Создает экземпляр EnginePlan с тестовой сессией.
    """
    return EnginePlan(session=test_session)


# Фикстура для экземпляра EngineStatus
@pytest.fixture
def engine_status(test_session):
    """
    Создает экземпляр EngineStatus с тестовой сессией.
    """
    return EngineStatus(session=test_session)


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


@pytest.fixture
def engine_cells(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


@pytest.fixture
def setup_data(test_session: SessionLocal, engine_group, engine_tools, engine_cell, engine_history,
               engine_operations_consumption, engine_plan, engine_status, engine_role, engine_user, engine_cells,
               fake_data):
    """
    Создает тестовые данные для таблицы OperationsConsumption и связанных таблиц.
    """
    # Создание тестовых данных
    datetime_value = datetime.datetime.now()
    engine_group.delete_all()
    engine_plan.delete_all()
    engine_tools.delete_all()
    engine_role.delete_all()
    engine_cells.delete_all()
    engine_user.delete_all()
    engine_status.delete_all()

    # Создание роли и пользователя
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

    # План и группа
    plan = Plan(
        id=random.choice([num for num in range(1, 9999) if num not in engine_plan.get_all_ids()]),
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111, 999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5,
    )
    group = Group(
        id=random.choice([num for num in range(1, 9999) if num not in engine_group.get_all_ids()]),
        name="Old Group",
        description="Old Description",
        status=0,
    )

    # Инструменты и ячейки
    tools = [
        Tools(
            id=random.choice([num for num in range(1, 9999) if num not in engine_tools.get_all_ids()]),
            barcode=str(random.randint(111111111111, 999999999999)),
            name=f"Tool {i}",
            description="Test Tool",
            img="tool.png",
            plan_id=plan.id,
            groups_id=group.id,
        )
        for i in range(2)
    ]
    status = Status(
        id=random.choice([num for num in range(1, 9999) if num not in engine_status.get_all_ids()]),
        stype=f"consumption",
        description="Test status"
    )
    cells = [
        Cell(
            id=random.choice([num for num in range(1, 9999) if num not in engine_cell.get_all_ids()]),
            number=random.randint(1, 999),
            groups_id=group.id,
            tools_id=tool.id,
            description=tool.name,
            status_id = status.id
        )
        for tool in tools
    ]

    all_ids = engine_history.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    history = History(
        id=_id,
        datetime=datetime_value,
        Status=1,
        Description="Test action",
        user_id=random.randint(1, 9999),
        user_role_id=random.randint(1, 9999),
        tools_id=tools[0].id
    )

    # Создаем запись в OperationsConsumption
    operations_consumption = OperationsConsumption(
        id=random.choice([num for num in range(1, 9999) if num not in engine_operations_consumption.get_all_ids()]),
        consumption_id=random.randint(1, 9999),
        consumption_tools_id=tools[0].id,
        status_id=status.id,
        history_id=history.id,
        description="Test operation consumption"
    )

    consumption = Consumption(
        tools_id=tools[0].id,
        cell_id=cells[0].id
    )
    # Сохраняем данные в сессии
    test_session.add_all(
        [plan, user, role, consumption, *tools, *cells, status, history, group, operations_consumption])
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    return {
        "status": status,
        "history": history,
        "role": role,
        "user": user,
        "plan": plan,
        "group": group,
        "tools": tools,
        "cells": cells,
        "operations_consumption": operations_consumption,
        "consumption": consumption,
    }


def test_add_operation_success(engine_operations_consumption, test_session, setup_data):
    """
    Тест успешного добавления операции.
    """
    # Добавляем операцию
    data = setup_data
    status = data["status"]
    history = data["history"]
    tools = data["tools"]
    consumption = data["consumption"]

    result = engine_operations_consumption.add_operation(
        description="Test operation",
        consumption_id=consumption.id,
        history_id=history.id,
        consumption_tools_id=tools[0].id,
        status_id=status.id,
    )
    assert result is True, "Операция не была успешно добавлена"

    # Проверяем, что операция добавлена в базу данных
    added_operation = test_session.query(OperationsConsumption).filter_by(
        consumption_id=consumption.id,
        consumption_tools_id=tools[0].id,
        status_id=status.id,
        history_id=history.id,
    ).first()
    assert added_operation is not None, "Добавленная операция не найдена в базе данных"
    assert added_operation.description == "Test operation", "Описание операции не совпадает"
    engine_operations_consumption.delete_operation(added_operation.id)


def test_get_operation_success(engine_operations_consumption, test_session, setup_data):
    """
    Тест получения операции по идентификатору.
    """
    # Добавляем операцию
    data = setup_data
    status = data["status"]
    history = data["history"]
    tools = data["tools"]
    consumption = data["consumption"]

    result = engine_operations_consumption.add_operation(
        description="Test operation",
        consumption_id=consumption.id,
        history_id=history.id,
        consumption_tools_id=tools[0].id,
        status_id=status.id,
    )
    # Проверяем, что операция добавлена в базу данных
    operation = test_session.query(OperationsConsumption).filter_by(
        consumption_id=consumption.id,
        consumption_tools_id=tools[0].id,
        status_id=status.id,
        history_id=history.id,
    ).first()
    # Получаем операцию по ID
    result = engine_operations_consumption.get_operation(operation.id)
    assert result is not None, "Операция по ID не найдена"
    assert result.id == operation.id, "ID операции не совпадает"
    assert result.description == "Test operation", "Описание операции не совпадает"


def test_get_all_operations(engine_operations_consumption, test_session, setup_data):
    """
    Тест получения всех операций.
    """
    data = setup_data
    # Добавляем несколько операций
    for i in data["tools"]:
        operation = OperationsConsumption(
            id=random.randint(1, 9999),
            date=datetime.datetime.now(),
            description=f"Operation",
            consumption_id=data["consumption"].id,
            history_id=data["history"].id,
            consumption_tools_id=i.id,
            status_id=data["status"].id,
        )
        test_session.add(operation)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем все операции
    result = engine_operations_consumption.get_all_operations()
    assert len(result) >= len(data["tools"]), "Количество операций не совпадает"
    # assert all(op.description.startswith("Operation") for op in result), "Описание операции не совпадает"


def test_update_operation_success(engine_operations_consumption, test_session, setup_data):
    """
    Тест успешного обновления операции.
    """
    # Добавляем операцию
    engine_operations_consumption.delete_all()
    data = setup_data

    operation = OperationsConsumption(
        id=max(engine_operations_consumption.get_all_ids(),default=0)+1,
        date=datetime.datetime.now(),
        description=f"Operation",
        consumption_id=data["consumption"].id,
        history_id=data["history"].id,
        consumption_tools_id=data["tools"][0].id,
        status_id=data["status"].id,
    )
    test_session.add(operation)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Обновляем описание операции
    result = engine_operations_consumption.update_operation(operation.id, description="Updated operation")
    assert result is True, "Операция не была обновлена"

    # Проверяем, что операция обновлена
    updated_operation = test_session.query(OperationsConsumption).get(operation.id)
    assert updated_operation.description == "Updated operation", "Описание операции не обновлено"


def test_delete_operation_success(engine_operations_consumption, test_session, setup_data):
    """
    Тест успешного удаления операции.
    """
    # Добавляем операцию
    data = setup_data

    operation = OperationsConsumption(
        id=random.randint(1, 9999),
        date=datetime.datetime.now(),
        description=f"Operation",
        consumption_id=data["consumption"].id,
        history_id=data["history"].id,
        consumption_tools_id=data["tools"][0].id,
        status_id=data["status"].id,
    )
    test_session.add(operation)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаляем операцию
    result = engine_operations_consumption.delete_operation(operation.id)
    assert result is True, "Операция не была удалена"

    # Проверяем, что операция удалена
    deleted_operation = test_session.query(OperationsConsumption).get(operation.id)
    assert deleted_operation is None, "Удалённая операция всё ещё присутствует в базе данных"


def test_count_operations(engine_operations_consumption, test_session, setup_data):
    """
    Тест получения количества операций.
    """
    # Добавляем несколько операций
    data = setup_data
    # Добавляем несколько операций
    for i in data["tools"]:
        operation = OperationsConsumption(
            id=random.randint(1, 9999),
            date=datetime.datetime.now(),
            description=f"Operation",
            consumption_id=data["consumption"].id,
            history_id=data["history"].id,
            consumption_tools_id=i.id,
            status_id=data["status"].id,
        )
        test_session.add(operation)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем количество операций
    result = engine_operations_consumption.count_operations()
    assert result >= len(data["tools"]), f"Количество операций должно быть 5, но получено {result}"

# def test_drop_operations_table(engine_operations_consumption, test_session, setup_data):
#     """
#     Тест удаления таблицы операций.
#     """
#     data = setup_data
#     # Добавляем несколько операций
#     for i in data["tools"]:
#         operation = OperationsConsumption(
#             id=random.randint(1, 9999),
#             date=datetime.datetime.now(),
#             description=f"Operation",
#             consumption_id=data["consumption"].id,
#             history_id=data["history"].id,
#             consumption_tools_id=i.id,
#             status_id=data["status"].id,
#         )
#         test_session.add(operation)
#     try:
#         test_session.commit()
#     except Exception:
#         test_session.rollback()
#         raise
#
#     # Удаляем таблицу
#     result = engine_operations_consumption.drop_operations_table()
#     assert result is True, "Таблица не была удалена"
#
#     # Проверяем, что таблица пуста
#     all_operations = test_session.query(OperationsConsumption).all()
#     assert len(all_operations) == 0, "Таблица не была удалена"
