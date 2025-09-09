import datetime
import random
import traceback

import pytest
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.MassDropCRUD import EngineMassDrop
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.UserCRUD import EngineUser
from DB.Models.Group import Group
from DB.Models.History import History
from DB.Models.MassDrop import MassDrop
from DB.Models.Plan import Plan
from DB.Models.Role import Role
from DB.Models.Status import Status
from DB.Models.Tools import Tools
from DB.Models.Cell import Cell
from DB.Models.DropOperations import DropOperations
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.DropOperationsCRUD import EngineDropOperations
from DB.Data.db import SessionLocal, engine
from DB.Models.User import User
from DB.Models.Drop import Drop


# Фикстура для создания тестового движка базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    # engine = create_engine('sqlite:///:memory:')  # Используем базу данных в памяти
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
    session = SessionLocal()
    return session


# Фикстура для экземпляра EngineDropOperations
@pytest.fixture
def engine_drop_operations(test_session):
    """
    Создает экземпляр EngineDropOperations с тестовой сессией.
    """
    return EngineDropOperations(session=test_session)


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


# Фикстура для создания экземпляра EngineHistory
@pytest.fixture
def engine_history(test_session):
    """
    Создает экземпляр EngineHistory с тестовой сессией.
    """
    return EngineHistory(session=test_session)


@pytest.fixture
def engine_cell(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


# Фикстура для экземпляра EngineDrop
@pytest.fixture
def engine_drop(test_session):
    """
    Создает экземпляр EngineDrop с тестовой сессией.
    """
    return EngineDrop(session=test_session)


# Фикстура для экземпляра EngineMassDrop
@pytest.fixture
def engine_mass_drop(test_session):
    """
    Создает экземпляр EngineMassDrop с тестовой сессией.
    """
    return EngineMassDrop(test_session)


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
def setup_data(test_session, engine_drop, engine_history, engine_group, engine_tools, engine_status, engine_mass_drop, engine_role, engine_user, engine_plan, engine_cells, fake_data):
    """
    Создает тестовые данные для тестирования операций Drop.
    """
    datetime_value = datetime.datetime.now()
    engine_role.delete_all()
    engine_user.delete_all()
    engine_plan.delete_all()
    engine_cells.delete_all()
    engine_status.delete_all()
    engine_mass_drop.delete_all()
    engine_history.delete_all()
    engine_drop.delete_all()
    engine_group.delete_all()
    engine_tools.delete_all()

    # Создание роли и пользователя
    role = Role(
        id=random.randint(1, 9999),
        Name="Admin",
        Description="Root user"
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
        id=random.randint(1, 9999),
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111, 999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5,
    )
    group = Group(
        id=random.randint(1, 9999),
        name="Old Group",
        description="Old Description",
        status=0,
    )

    # Инструменты и ячейки
    tools = [
        Tools(
            id=random.randint(1, 9999),
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
        id = random.randint(1, 9999),
        stype = "mass_drop_init",
        description = "The status is inactive.",
        created_at = datetime.datetime.now()
    )

    cells = [
        Cell(
            id=random.randint(1, 9999),
            number=random.randint(1, 999),
            groups_id=group.id,
            tools_id=tool.id,
            description=tool.name,
            status_id = status.id
        )
        for tool in tools
    ]

    mass_drop = MassDrop(
        id=random.randint(1, 9999),
        description="Mass drop operation",
    )
    drop = Drop(
        id=random.randint(1, 9999),
        tools_id=tools[0].id,
        mass_drop_id=mass_drop.id,
        cell_id=cells[0].id,
        description="Выдача инструмента"
    )
    # История
    all_ids = engine_history.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

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
    test_session.add_all([role, user, plan, group, *tools, *cells, status, mass_drop, history, drop])

    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    return {
        "role": role,
        "user": user,
        "plan": plan,
        "group": group,
        "tools": tools,
        "cells": cells,
        "status": status,
        "mass_drop": mass_drop,
        "history": history,
        "drop": drop
    }


def test_add_operation_success(engine_drop_operations, test_session, setup_data):
    """
    Тест успешного добавления операции Drop.
    """
    # Данные из фикстуры
    data = setup_data
    tools = data["tools"]
    cells = data["cells"]
    status = data["status"]
    history = data["history"]
    mass_drop = data["mass_drop"]

    # Подготовка данных для операции
    tool = tools[0]
    cell = cells[0]
    description = "Test operation"
    drop_id = random.randint(1, 9999)  # Идентификатор Drop

    # Добавление операции через EngineDropOperations
    result = engine_drop_operations.add_operation(
        index=random.randint(1, 9999),
        drop_id=drop_id,
        tools_id=tool.id,
        status_id=status.id,
        history_id=history.id,
        description=description,
    )

    # Проверка результата
    assert result is True, "Операция не была успешно добавлена"

    # Проверяем, что операция добавлена в базу данных
    added_operation = test_session.query(DropOperations).filter_by(drop_id=drop_id).first()
    assert added_operation is not None, "Добавленная операция не найдена в базе данных"
    assert added_operation.tools_id == tool.id
    assert added_operation.status_id == status.id
    assert added_operation.history_id == history.id
    assert added_operation.description == description


def test_get_operation_by_id_success(engine_drop_operations, test_session, setup_data):
    """
    Тест успешного получения операции Drop по ID.
    """
    # Подготовка данных из фикстуры
    tools = setup_data["tools"]
    history = setup_data["history"]
    status = setup_data["status"]

    # Добавление новой операции Drop
    drop_id = random.randint(1, 9999)
    tools_id = tools[0].id
    status_id = status.id
    history_id = history.id
    description = "Test Operation"

    added_successfully = engine_drop_operations.add_operation(
        index=random.randint(1, 9999),
        drop_id=drop_id,
        tools_id=tools_id,
        status_id=status_id,
        history_id=history_id,
        description=description,
    )
    assert added_successfully, "Не удалось добавить операцию Drop."

    # Проверяем, что операция добавлена в базу данных
    operation = test_session.query(DropOperations).filter_by(drop_id=drop_id).first()
    assert operation is not None, "Добавленная операция не найдена в базе данных"

    # Получение операции по ID через метод
    result = engine_drop_operations.get_operation_by_id(operation.id)

    # Проверка данных полученной операции
    assert result is not None, "Операция по ID не найдена"
    assert result.id == operation.id, "ID полученной операции не совпадает с ожидаемым"
    assert result.drop_id == drop_id, "Неверный drop_id в полученной операции"
    assert result.tools_id == tools_id, "Неверный tools_id в полученной операции"
    assert result.status_id == status_id, "Неверный status_id в полученной операции"
    assert result.history_id == history_id, "Неверный history_id в полученной операции"
    assert result.description == description, "Неверное описание операции"


# def test_get_all_operations(engine_drop_operations, test_session, setup_data):
#     """
#     Тест получения всех операций Drop.
#     """
#     # Извлекаем данные из setup_data
#     tools = setup_data["tools"]
#     status = setup_data["status"]
#     history = setup_data["history"]
#     mass_drop = setup_data["mass_drop"]
#     drop = setup_data["drop"]
#     # Добавляем несколько операций Drop
#     for i, tool in enumerate(tools, start=1):
#         engine_drop_operations.add_operation(
#             index=random.randint(1, 9999),
#             drop_id=drop.id,
#             tools_id=tool.id,
#             status_id=status.id,
#             history_id=history.id,
#             description=f"Operation {i}"
#         )
#
#     # Получаем все операции
#     operations = engine_drop_operations.get_all_operations()
#
#     # Проверяем количество операций и их тип
#     assert len(operations) == len(tools), "Количество операций не совпадает"
#     assert all(
#         isinstance(op, DropOperations) for op in operations
#     ), "Некоторые элементы не являются объектами DropOperations"
#
#     # Проверяем соответствие данных
#     for i, operation in enumerate(operations, start=1):
#         assert operation.description == f"Operation {i}", f"Описание операции {i} не совпадает"
#         assert operation.tools_id == tools[i - 1].id, f"ID инструмента операции {i} не совпадает"
#         assert operation.status_id == status.id, f"ID статуса операции {i} не совпадает"
#         assert operation.history_id == history.id, f"ID истории операции {i} не совпадает"


# def test_count_operations(engine_drop_operations, test_session):
#     """
#     Тест получения количества операций.
#     """
#     # Добавляем несколько операций
#     for i in range(3):
#         engine_drop_operations.add_operation(drop_id=i + 1, tools_id=i + 1, status_id=i + 1, history_id=i + 1,
#                                              description=f"Operation {i + 1}")
#
#     # Получаем количество операций
#     count = engine_drop_operations.count_operations()
#
#     assert count == 3, f"Ожидалось 3 операции, но получено {count}"


def test_update_operation_success(engine_drop_operations, test_session):
    """
    Тест успешного обновления операции.
    """
    drop_id = 1
    tools_id = 1
    status_id = 1
    history_id = 1
    description = "Test Operation"
    index = max(engine_drop_operations.get_all_ids(), default=0) + 1
    engine_drop_operations.add_operation(index, drop_id, tools_id, status_id, history_id, description)

    # Обновляем описание операции
    new_description = "Updated Test Operation"
    operation = test_session.query(DropOperations).first()
    result = engine_drop_operations.update_operation(operation.id, description=new_description)

    assert result is True, "Операция не была обновлена"

    # Проверяем, что описание изменилось
    updated_operation = test_session.query(DropOperations).filter_by(id=operation.id).first()
    assert updated_operation.description == new_description, "Описание операции не обновилось"


def test_delete_operation_success(engine_drop_operations, test_session):
    """
    Тест успешного удаления операции.
    """
    drop_id = 1
    tools_id = 1
    status_id = 1
    history_id = 1
    description = "Test Operation"
    index = max(engine_drop_operations.get_all_ids(), default=0) + 1
    engine_drop_operations.add_operation(index, drop_id, tools_id, status_id, history_id, description)

    # Удаляем операцию
    operation = test_session.query(DropOperations).first()
    result = engine_drop_operations.delete_operation(operation.id)

    assert result is True, "Операция не была успешно удалена"

    # Проверяем, что операция удалена
    deleted_operation = test_session.query(DropOperations).filter_by(id=operation.id).first()
    assert deleted_operation is None, "Удалённая операция всё ещё присутствует в базе данных"

# def test_drop_operations_table_success(engine_drop_operations, test_session):
#     """
#     Тест успешного удаления таблицы DropOperations.
#     """
#     # Удаляем таблицу
#     result = engine_drop_operations.drop_operations_table()
#
#     assert result is True, "Таблица не была успешно удалена"
#
#     # Проверяем, что таблица удалена
#     with pytest.raises(Exception):
#         test_session.query(DropOperations).first()
