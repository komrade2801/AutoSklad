import random

import pytest
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import datetime

from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.LoadCRUD import EngineLoad  # Импортируем класс EngineLoad
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser

from DB.Engine.MassLoadCRUD import EngineMassLoad

from DB.Models.Cell import Cell
from DB.Models.Group import Group
from DB.Models.History import History
from DB.Models.Load import Load
from DB.Data.base import Base

from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Models.MassLoad import MassLoad
from DB.Models.Plan import Plan
from DB.Models.Role import Role
from DB.Models.Status import Status
from DB.Models.Tools import Tools
from DB.Models.User import User


# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    # engine = create_engine('sqlite:///:memory:')  # Используем SQLite в памяти для тестов
    # Base.metadata.create_all(engine)  # Создаем все таблицы
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
    return SessionLocal()


# Фикстура для экземпляра EngineLoad
@pytest.fixture
def engine_massload(test_session):
    """
    Создает экземпляр EngineLoad с тестовой сессией.
    """
    return EngineMassLoad(session=test_session)


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
def setup_data(test_session, engine_load, engine_status, engine_tools, engine_plan, engine_user, engine_cells,
               engine_role, engine_group, fake_data, engine_massload, engine_history):
    """
    Создает тестовые данные для тестирования операций load.
    """

    engine_group.delete_all()
    engine_role.delete_all()
    engine_cells.delete_all()
    engine_user.delete_all()
    engine_plan.delete_all()
    engine_tools.delete_all()
    engine_status.delete_all()

    datetime_value = datetime.datetime.now()
    role_indx = engine_role.get_all_ids()
    role_indx = max(role_indx, default=0) + 1

    # Создание роли и пользователя
    role = Role(
        id=role_indx,
        Name="Admin",
        Description="Root user"
    )
    user_indx = engine_user.get_all_ids()
    user_indx = max(user_indx, default=0) + 1

    user = User(
        id=user_indx,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )
    plan_indx = engine_plan.get_all_ids()
    plan_indx = max(plan_indx, default=0) + 1

    # План и группа
    plan = Plan(
        id=plan_indx,
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111, 999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5,
    )
    group_indx = engine_group.get_all_ids()
    group_indx = max(group_indx, default=0) + 1

    group = Group(
        id=group_indx,
        name="Old Group",
        description="Old Description",
        status=0,
    )
    tools_indx = engine_tools.get_all_ids()
    tools_indx = max(tools_indx, default=0) + 1

    # Инструменты и ячейки
    tools = [
        Tools(
            id=tools_indx + i,
            barcode=str(random.randint(111111111111, 999999999999)),
            name=f"Tool {i}",
            description="Test Tool",
            img="tool.png",
            plan_id=plan.id,
            groups_id=group.id,
        )
        for i in range(2)
    ]
    cells_indx = engine_cells.get_all_ids()
    cells_indx = max(cells_indx, default=0) + 1

    cells = [
        Cell(
            id=cells_indx + tool.id,
            number=random.randint(1, 999),
            groups_id=group.id,
            tools_id=tool.id,
            description=tool.name,
            status_id = 1

        )
        for tool in tools
    ]
    status_indx = engine_status.get_all_ids()
    status_indx = max(status_indx, default=0) + 1

    # Статус и массовое удаление
    status = Status(
        id=status_indx,
        stype=f"Inactive {random.randint(1, 9999)}",
        description="The status is inactive.",
    )
    mass_load_indx = engine_massload.get_all_ids()
    mass_load_indx = max(mass_load_indx, default=0) + 1

    mass_load = MassLoad(
        id=mass_load_indx,
        description="Mass load operation",
    )
    load_indx = engine_load.get_all_ids()
    load_indx = max(load_indx, default=0) + 1

    load = Load(
        id=load_indx,
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )

    history_indx = engine_history.get_all_ids()
    history_indx = max(history_indx, default=0) + 1

    # История
    history = History(
        id=history_indx,
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


def test_add_load(engine_load, test_session, setup_data):
    """
    Тест добавления записи Load.
    """
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

    load = Load(
        id=random.randint(1, 9999),
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    test_session.add(load)
    test_session.commit()

    # Проверка, что запись добавлена в базу данных
    added_load = test_session.query(Load).filter_by(tools_id=tools[0].id, mass_load_id=mass_load.id).first()
    assert added_load is not None, "Загруженная запись не найдена в базе данных"
    assert added_load.description == "Загрузка инструмента"


# def test_find_by_tools_id(engine_load, test_session, setup_data):
#     """
#     Тест поиска записей по tools_id.
#     """
#     data = setup_data
#     tools = data["tools"]
#     cells = data["cells"]
#     mass_load = data["mass_load"]
#
#     load_1 = Load(
#         id=random.randint(1, 9999),
#         tools_id=tools[0].id,
#         mass_load_id=mass_load.id,
#         cell_id=cells[0].id,
#         description="Загрузка инструмента"
#     )
#     load_2 = Load(
#         id=random.randint(1, 9999),
#         tools_id=tools[0].id,
#         mass_load_id=mass_load.id,
#         cell_id=cells[0].id,
#         description="Загрузка инструмента"
#     )
#     test_session.add(load_1)
#     test_session.add(load_2)
#     try:
#         test_session.commit()
#     except Exception:
#         test_session.rollback()
#         raise
#
#     # Поиск по tools_id
#     loads = engine_load.find_by_tools_id(tools[0].id)
#     assert len(loads) >= 2, "Неверное количество записей по tools_id"
#     assert all(load.tools_id == tools[0].id for load in loads), "Некорректные данные в возвращенных записях"


def test_find_by_mass_load_id(engine_load, test_session, setup_data):
    """
    Тест поиска записей по mass_load_id.
    """
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

    all_ids = engine_load.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    load_indx = engine_load.get_all_ids()
    load_indx = max(load_indx, default=0) + 1

    load_1 = Load(
        id=load_indx,
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )

    load_2 = Load(
        id=load_indx + 1,
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    test_session.add(load_1)
    test_session.add(load_2)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Поиск по mass_load_id
    loads = engine_load.find_by_mass_load_id(mass_load.id)
    assert len(loads) >= 2, "Неверное количество записей по mass_load_id"
    assert all(load.mass_load_id == mass_load.id for load in loads), "Некорректные записи по mass_load_id"


def test_update_description(engine_load, test_session, setup_data):
    """
    Тест обновления описания записи Load.
    """

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

    load = Load(
        id=random.randint(1, 9999),
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    test_session.add(load)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Обновление описания
    result = engine_load.update_description(load_id=load.id, description="Updated description")
    assert result is True, "Описание не обновлено"

    # Проверяем обновленное описание
    updated_load = test_session.query(Load).filter_by(id=load.id).first()
    assert updated_load.description == "Updated description", "Описание не совпадает"


def test_delete_by_tools_id(engine_load, test_session, setup_data):
    """
    Тест удаления записей по tools_id.
    """

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
    all_ids = engine_load.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    load_1 = Load(
        id=_id,
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    all_ids = engine_load.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])
    load_2 = Load(
        id=_id,
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )

    test_session.add(load_1)
    test_session.add(load_2)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаляем записи по tools_id
    deleted_count = engine_load.delete_by_tools_id(tools[0].id)
    assert deleted_count >= 2, "Количество удаленных записей неверно"

    # Проверяем, что записи удалены
    remaining_loads = test_session.query(Load).filter_by(tools_id=tools[0].id).all()
    assert len(remaining_loads) == 0, "Записи не были удалены"


def test_count_by_cell_id(engine_load, test_session, setup_data):
    """
    Тест подсчета записей по cell_id.
    """

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

    load_1 = Load(
        id=random.randint(1, 9999),
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    load_2 = Load(
        id=random.randint(1, 9999),
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    load_3 = Load(
        id=random.randint(1, 9999),
        tools_id=tools[0].id,
        mass_load_id=mass_load.id,
        cell_id=cells[0].id,
        description="Загрузка инструмента"
    )
    test_session.add(load_1)
    test_session.add(load_2)
    test_session.add(load_3)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Подсчитаем количество записей по cell_id
    count = engine_load.count_by_cell_id(cells[0].id)
    assert count >= 2, "Количество записей по cell_id неверно"


def test_delete_non_existent(engine_load, test_session):
    """
    Тест удаления записей, которых нет в базе.
    """
    # Попытка удалить записи с несуществующим tools_id
    deleted_count = engine_load.delete_by_tools_id(999)
    assert deleted_count == 0, "Не должно быть удалено ни одной записи"


def test_update_non_existent(engine_load, test_session):
    """
    Тест обновления записи, которой нет в базе.
    """
    # Попытка обновить описание несуществующей записи
    result = engine_load.update_description(load_id=999, description="New description")
    assert result is False, "Обновление несуществующей записи должно вернуть False"
