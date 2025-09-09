
import random
import pytest
import datetime
from faker import Faker
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser
from DB.Models.Cell import Cell
from DB.Models.Group import Group
from DB.Models.History import History
from DB.Models.LoadOperations import LoadOperations
from DB.Models.Load import Load
from DB.Models.MassLoad import MassLoad
from DB.Models.Plan import Plan
from DB.Models.Role import Role
from DB.Models.Status import Status
from DB.Models.Tools import Tools
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Models.User import User


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
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineLoadOperations
@pytest.fixture
def engine_load_operations(test_session):
    """
    Создает экземпляр EngineLoadOperations с тестовой сессией.
    """
    return EngineLoadOperations(session=test_session)


# Фикстура для экземпляра EngineLoad
@pytest.fixture
def engine_load(test_session):
    """
    Создает экземпляр EngineLoad с тестовой сессией.
    """
    return EngineLoad(session=test_session)


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
def engine_massload(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineMassLoad(session=test_session)

@pytest.fixture
def setup_data(test_session, engine_load, engine_history, engine_group, engine_role, engine_cells, engine_user,
               engine_plan, engine_tools, engine_status, fake_data, engine_massload):
    """
    Создает тестовые данные для тестирования операций load.
    """
    datetime_value = datetime.datetime.now()

    engine_group.delete_all()
    engine_role.delete_all()
    engine_cells.delete_all()
    engine_user.delete_all()
    engine_plan.delete_all()
    engine_tools.delete_all()
    engine_status.delete_all()

    # Создание роли и пользователя
    index = max(engine_group.get_all_ids(), default=0) + 1
    role = Role(
        id=index,
        Name="Admin",
        Description="Root user"
    )

    index = max(engine_user.get_all_ids(), default=0) + 1
    user = User(
        id=index,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )

    # План и группа

    index = max(engine_plan.get_all_ids(), default=0) + 1
    plan = Plan(
        id=index,
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111, 999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5,
    )
    index = max(engine_group.get_all_ids(), default=0) + 1
    group = Group(
        id=index,
        name="Old Group",
        description="Old Description",
        status=0,
    )

    # Инструменты и ячейки
    used_ids = engine_tools.get_all_ids()

    tools = [
        Tools(
            id=max(used_ids, default=0) + i + 1,
            barcode=str(random.randint(111111111111, 999999999999)),
            name=f"Tool {i}",
            description="Test Tool",
            img="tool.png",
            plan_id=plan.id,
            groups_id=group.id,
        )
        for i in range(2)
    ]
    # Статус и массовое удаление
    status = Status(
        id=max(engine_status.get_all_ids(), default=0) + 1,
        stype=f"Inactive {random.randint(1, 9999)}",
        description="The status is inactive.",
    )
    used_ids = engine_cells.get_all_ids()
    cells = [
        Cell(
            id=max(used_ids, default=0) + i + 1,
            number=random.randint(1, 999),
            groups_id=group.id,
            tools_id=tool.id,
            description=tool.name,
            status_id=status.id
        )
        for i, tool in enumerate(tools)
    ]


    mass_load = MassLoad(
        id=max(engine_massload.get_all_ids(), default=0) + 1,
        description="Mass load operation",
    )
    load = Load(
        id=max(engine_load.get_all_ids(), default=0) + 1,
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Выдача инструмента"
    )
    _id = max(engine_history.get_all_ids(), default=0) + 1
    # _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    # История
    history = History(
        id=_id,
        datetime=datetime_value,
        Status=1,
        Description="Test action",
        user_id=user.id,
        user_role_id=role.id,
        tools_id=tools[0].id,
    )

    # Сохранение данных в сессии
    test_session.add_all([role, user, plan, group, *tools, *cells, status, mass_load, history, load])

    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    return {
        "role": role,
        "user": user,
        "plan": plan,
        "group": group,
        "tools": tools,
        "cells": cells,
        "status": status,
        "mass_load": mass_load,
        "history": history,
        "load": load
    }


def test_add_operation_success(engine_load_operations, test_session, setup_data):
    """
    Тест успешного добавления операции.
    """
    # Данные для добавления операции
    data = setup_data
    role = data["role"]
    user = data["user"]
    plan = data["plan"]
    group = data["group"]
    tools = data["tools"]
    cells = data["cells"]
    status = data["status"]
    mass_load = data["mass_load"]
    history = data["history"]
    load = data["load"]

    load_id = load.id
    load_tools_id = tools[0].id
    status_id = status.id
    history_id = history.id
    description = "Test operation"

    result = engine_load_operations.add_operation(
        id=max(engine_load_operations.get_all_ids(), default=0)+1,
        date=datetime.datetime.now(),
        description=description,
        load_id=load_id,
        load_tools_id=load_tools_id,
        status_id=status_id,
        history_id=history_id)

    assert result is True, "Операция не была добавлена"

    # Проверяем, что операция добавлена в базу данных
    added_operation = test_session.query(LoadOperations).filter_by(load_id=load_id).first()
    assert added_operation is not None, "Добавленная операция не найдена в базе данных"
    assert added_operation.load_id == load_id
    assert added_operation.load_tools_id == load_tools_id
    assert added_operation.status_id == status_id
    assert added_operation.history_id == history_id
    assert added_operation.description == description
    # engine_load_operations.delete_operation()


# def test_add_operation_integrity_error(engine_load_operations, test_session):
#     """
#     Тест добавления операции с нарушением уникальности (например, дублирование данных).
#     """
#     # Попробуем добавить операцию с одинаковыми данными
#     load_id = 1
#     load_tools_id = 2
#     status_id = 3
#     history_id = 4
#     description = "Test operation"
#
#     engine_load_operations.add_operation(load_id, load_tools_id, status_id, history_id, description)
#
#     # Попытка добавить ту же операцию должна вызвать ошибку
#     result = engine_load_operations.add_operation(load_id, load_tools_id, status_id, history_id, description)
#     assert result is False, "Операция была добавлена с ошибкой уникальности"


def test_get_operation_by_id(engine_load_operations, test_session, setup_data):
    """
    Тест получения операции по ID.
    """
    # Добавляем операцию
    data = setup_data
    role = data["role"]
    user = data["user"]
    plan = data["plan"]
    group = data["group"]
    tools = data["tools"]
    cells = data["cells"]
    status = data["status"]
    mass_load = data["mass_load"]
    history = data["history"]
    load = data["load"]

    load_id = load.id
    load_tools_id = tools[0].id
    status_id = status.id
    history_id = history.id
    description = "Test operation"

    result = engine_load_operations.add_operation(
        id=max(engine_load_operations.get_all_ids(), default=0)+1,
        date=datetime.datetime.now(),
        description=description,
        load_id=load_id,
        load_tools_id=load_tools_id,
        status_id=status_id,
        history_id=history_id)

    assert result is True, "Операция не была добавлена"

    # Получаем операцию по ID
    added_operation = test_session.query(LoadOperations).filter_by(load_id=load_id).first()
    result = engine_load_operations.get(added_operation.id)
    assert result is not None, "Операция по ID не найдена"
    assert result.load_id == load_id
    assert result.load_tools_id == load_tools_id


# def test_get_all_operations(engine_load_operations, test_session):
#     """
#     Тест получения всех операций.
#     """
#     # Добавляем несколько операций
#     for i in range(5):
#         engine_load_operations.add_operation(load_id=i + 1, load_tools_id=i + 2, status_id=i + 3, history_id=i + 4,
#                                              description=f"Operation {i + 1}")
#
#     # Получаем все операции
#     result = engine_load_operations.get_all_operations()
#     assert len(result) == 5, "Количество операций не совпадает"
#     assert all(isinstance(op, LoadOperations) for op in result)


def test_update_operation_success(engine_load_operations, test_session, setup_data):
    """
    Тест успешного обновления операции.
    """
    # Добавляем операцию
    data = setup_data
    role = data["role"]
    user = data["user"]
    plan = data["plan"]
    group = data["group"]
    tools = data["tools"]
    cells = data["cells"]
    status = data["status"]
    mass_load = data["mass_load"]
    history = data["history"]
    load = data["load"]

    load_id = load.id
    load_tools_id = tools[0].id
    status_id = status.id
    history_id = history.id
    description = "Test operation"

    result = engine_load_operations.add_operation(
        id=max(engine_load_operations.get_all_ids(), default=0)+1,
        date=datetime.datetime.now(),
        description=description,
        load_id=load_id,
        load_tools_id=load_tools_id,
        status_id=status_id,
        history_id=history_id)

    assert result is True, "Операция не была добавлена"

    # Обновляем описание операции
    added_operation = test_session.query(LoadOperations).filter_by(load_id=load_id).first()
    result = engine_load_operations.update(added_operation.id, description="Updated description")

    assert result is True, "Операция не была обновлена"

    # Проверяем обновление
    updated_operation = test_session.query(LoadOperations).filter_by(id=added_operation.id).first()
    assert updated_operation.description == "Updated description"


def test_delete_operation_success(engine_load_operations, test_session, setup_data):
    """
    Тест успешного удаления операции.
    """
    # Добавляем операцию
    data = setup_data
    role = data["role"]
    user = data["user"]
    plan = data["plan"]
    group = data["group"]
    tools = data["tools"]
    cells = data["cells"]
    status = data["status"]
    mass_load = data["mass_load"]
    history = data["history"]
    load = data["load"]

    load_id = load.id
    load_tools_id = tools[0].id
    status_id = status.id
    history_id = history.id
    description = "Test operation"

    result = engine_load_operations.add_operation(
        id=max(engine_load_operations.get_all_ids(), default=0)+1,
        date=datetime.datetime.now(),
        description=description,
        load_id=load_id,
        load_tools_id=load_tools_id,
        status_id=status_id,
        history_id=history_id)

    assert result is True, "Операция не была добавлена"
    # Удаляем операцию
    added_operation = test_session.query(LoadOperations).filter_by(load_id=load_id).first()
    result = engine_load_operations.delete(added_operation.id)

    assert result is True, "Операция не была удалена"

    # Проверяем, что операция удалена
    deleted_operation = test_session.query(LoadOperations).filter_by(id=added_operation.id).first()
    assert deleted_operation is None, "Удалённая операция всё ещё присутствует в базе данных"


def test_count_operations(engine_load_operations, test_session):
    """
    Тест подсчета всех операций.
    """
    # Добавляем несколько операций
    # for i in range(1):
    #     engine_load_operations.add_operation(load_id=i + 1, load_tools_id=i + 2, status_id=i + 3, history_id=i + 4,
    #                                          description=f"Operation {i + 1}")

    # Проверяем количество операций
    result = engine_load_operations.count()
    assert result > 0, f"Количество операций не совпадает. Ожидалось 5, получено {result}"


def test_find_by_status(engine_load_operations, test_session, setup_data):
    """
    Тест поиска операций по статусу.
    """
    # Добавляем несколько операций
    data = setup_data
    role = data["role"]
    user = data["user"]
    plan = data["plan"]
    group = data["group"]
    tools = data["tools"]
    cells = data["cells"]
    status = data["status"]
    mass_load = data["mass_load"]
    history = data["history"]
    load = data["load"]

    load_id = load.id

    status_id = status.id
    history_id = history.id
    description = "Test operation"

    for tool in tools:
        result = engine_load_operations.add_operation(
            id=max(engine_load_operations.get_all_ids(), default=0)+1,
            date=datetime.datetime.now(),
            description=description,
            load_id=load_id,
            load_tools_id=tool.id,
            status_id=status_id,
            history_id=history_id)

        assert result is True, "Операция не была добавлена"

    # Ищем операции с указанным статусом
    result = engine_load_operations.find_by_status(status.id)
    assert len(result) >= 1, f"Ожидалось 5 операций с статусом 1, но найдено {len(result)}"
    assert all(op.status_id == status.id for op in result)

# def test_find_by_date_range(engine_load_operations, test_session):
#     """
#     Тест поиска операций по диапазону дат.
#     """
#     # Добавляем несколько операций
#     now = datetime.utcnow()
#     for i in range(5):
#         engine_load_operations.add_operation(load_id=i + 1, load_tools_id=i + 2, status_id=1, history_id=i + 4,
#                                              description=f"Operation {i + 1}")
#
#     # Ищем операции в диапазоне дат
#     start_date = now - timedelta(days=1)
#     end_date = now + timedelta(days=1)
#     result = engine_load_operations.find_by_date_range(start_date, end_date)
#     assert len(result) == 5, f"Ожидалось 5 операций в заданном диапазоне, но найдено {len(result)}"
