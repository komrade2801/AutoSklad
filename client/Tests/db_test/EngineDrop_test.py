import random
import traceback

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.MassDropCRUD import EngineMassDrop
from DB.Engine.ToolsCRUD import EngineTools
from DB.Models.Cell import Cell
from DB.Models.Drop import Drop
from DB.Engine.DropCRUD import EngineDrop
from DB.Data.base import Base
from DB.Data.db import SessionLocal, engine
from DB.Models.Group import Group
from DB.Models.Plan import Plan
from DB.Models.Tools import Tools
from DB.Models.MassLoad import MassLoad  # Импорт модели MassDrop


# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    return SessionLocal()


# Фикстура для экземпляра EngineDrop
@pytest.fixture
def engine_drop(test_session):
    """
    Создает экземпляр EngineDrop с тестовой сессией.
    """
    return EngineDrop(session=test_session)


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


# Фикстура для экземпляра EngineMassDrop
@pytest.fixture
def engine_mass_drop(test_session):
    """
    Создает экземпляр EngineMassDrop с тестовой сессией.
    """
    return EngineMassDrop(test_session)


@pytest.fixture
def setup_data(test_session, engine_mass_drop, engine_drop, engine_group, engine_tools, engine_cell):
    """
    Создает тестовые данные для инструментов, планов и групп.
    """
    engine_drop.delete_all()
    engine_group.delete_all()
    engine_tools.delete_all()
    engine_cell.delete_all()
    engine_mass_drop.delete_all()

    plan = Plan(
        id=random.randint(1, 9999),
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111, 999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    test_session.add(plan)

    group = Group(id=random.randint(1, 9999), name="Old Group", description="Old Description", status=0)
    test_session.add(group)
    tools = []
    for i in range(3):
        tool = Tools(
            id=random.randint(1, 9999),
            barcode=str(random.randint(111111111111, 999999999999)),
            name="Отвертка",
            description="Плоская отвертка",
            img="screwdriver.png",
            plan_id=plan.id,
            groups_id=group.id
        )
        test_session.add(tool)
        tools.append(tool)

    description = "Удаление устаревших данных"
    mass_drop = engine_mass_drop.add_task(description)

    cells = []
    for tool in tools:
        cell = Cell(
            number=random.randint(1, 999),
            groups_id=group.id,
            tools_id=tool.id,
            description=tool.name,
            status_id = 1
        )
        test_session.add(cell)
        cells.append(cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    return tools, plan, group, cells, mass_drop


def test_add_drop_success(engine_drop, test_session, engine_group, engine_tools, setup_data, engine_cell,
                          engine_mass_drop):
    """
    Тест успешного добавления записи Drop.
    """

    tools, plan, group, cell, mass_drop = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tools_id = tools_by_group[0].id
    cells = engine_cell.get_all_cells()
    cell_id = cells[0].id
    mass_drop_id = engine_mass_drop.get_all_tasks()[0].id
    description = "Выдача инструмента"
    result = engine_drop.add_drop(tools_id=tools_id, mass_drop_id=mass_drop_id, cell_id=cell_id,
                                  description=description)
    assert result is True, "Запись не была добавлена"

    # Проверяем, что запись добавлена в базу данных
    added_drop = test_session.query(Drop).filter_by(tools_id=tools_id, mass_drop_id=mass_drop_id,
                                                    cell_id=cell_id).first()
    assert added_drop is not None, "Добавленная запись не найдена в базе данных"
    assert added_drop.tools_id == tools_id
    assert added_drop.mass_drop_id == mass_drop_id
    assert added_drop.cell_id == cell_id
    assert added_drop.description == description


def test_get_by_tools_id(engine_drop, test_session, engine_mass_drop, engine_cell, engine_tools, engine_group,
                         setup_data):
    """
    Тест получения записей Drop по tools_id.
    """
    tools, plan, groups, cells, mass_drop = setup_data
    # Добавляем несколько записей
    # groups = engine_group.get_all_groups()
    group_id = groups.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)

    for tool in tools_by_group:
        cells = engine_cell.get_cells_by_tool(tool.id)
        mass_drop_id = engine_mass_drop.get_all_tasks()[0].id
        description = "Выдача инструмента"
        result = engine_drop.add_drop(tools_id=tool.id, mass_drop_id=mass_drop_id, cell_id=cells[0].id,
                                      description=description)
        assert result is True, "Запись не была добавлена"

    # engine_drop.add_drop(1, 2, 3, "Описание 1")
    # engine_drop.add_drop(1, 3, 4, "Описание 2")
    # engine_drop.add_drop(2, 2, 3, "Описание 3")

    # Получаем записи по tools_id = 1
    result = engine_drop.get_by_tools_id(tools_by_group[0].id)
    assert len(result) == 1, "Количество записей по tools_id не совпадает"
    # assert all(drop.tools_id == 1 for drop in result), "Не все записи имеют правильный tools_id"


def test_get_by_mass_drop_id(engine_drop, test_session, setup_data, engine_tools, engine_cell, engine_mass_drop):
    """
    Тест получения записей Drop по mass_drop_id.
    """
    # Добавляем несколько записей
    tools, plan, groups, cells, mass_drop = setup_data
    # Добавляем несколько записей
    group_id = groups.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)

    for tool in tools_by_group:
        cells = engine_cell.get_cells_by_tool(tool.id)
        mass_drop_id = engine_mass_drop.get_all_tasks()[0].id
        description = "Выдача инструмента"
        result = engine_drop.add_drop(tools_id=tool.id, mass_drop_id=mass_drop_id, cell_id=cells[0].id,
                                      description=description)
        assert result is True, "Запись не была добавлена"

    # Получаем записи по mass_drop_id = 2
    result = engine_drop.get_by_mass_drop_id(engine_mass_drop.get_all_tasks()[0].id)
    assert len(result) >= 2, "Количество записей по mass_drop_id не совпадает"
    # assert all(drop.mass_drop_id == 2 for drop in result), "Не все записи имеют правильный mass_drop_id"


def test_get_by_cell_id(engine_drop, test_session, setup_data, engine_tools, engine_cell, engine_mass_drop):
    """
    Тест получения записей Drop по cell_id.
    """
    # Добавляем несколько записей
    tools, plan, groups, cells, mass_drop = setup_data
    # Добавляем несколько записей
    group_id = groups.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)

    for tool in tools_by_group:
        cells = engine_cell.get_cells_by_tool(tool.id)
        mass_drop_id = engine_mass_drop.get_all_tasks()[0].id
        description = "Выдача инструмента"
        result = engine_drop.add_drop(tools_id=tool.id, mass_drop_id=mass_drop_id, cell_id=cells[0].id,
                                      description=description)
        assert result is True, "Запись не была добавлена"

    # Получаем записи по cell_id = 3
    result = engine_drop.get_by_cell_id(engine_cell.get_cells_by_tool(tools_by_group[0].id)[0].id)
    assert len(result) >= 1, "Количество записей по cell_id не совпадает"
    # assert all(drop.cell_id == 3 for drop in result), "Не все записи имеют правильный cell_id"


def test_update_drop_success(engine_drop, test_session, setup_data, engine_group, engine_tools, engine_cell,
                             engine_mass_drop):
    """
    Тест успешного обновления записи Drop.
    """
    # Добавляем запись
    tools, plan, group, cell, mass_drop = setup_data
    group_id = group.id
    tools_id = tools[0].id
    cells = engine_cell.get_all_cells()
    cell_id = cells[0].id
    mass_drop_id = engine_mass_drop.get_all_tasks()[0].id
    description = "Выдача инструмента"
    result = engine_drop.add_drop(tools_id=tools_id, mass_drop_id=mass_drop_id, cell_id=cell_id,
                                  description=description)
    assert result is True, "Запись не была добавлена"

    # Проверяем, что запись добавлена в базу данных
    drop = test_session.query(Drop).filter_by(tools_id=tools_id, mass_drop_id=mass_drop_id,
                                              cell_id=cell_id).first()
    drop_id = drop.id
    # Обновляем описание записи
    new_description = "Обновленное описание"
    result = engine_drop.update_drop(drop_id, description=new_description)
    assert result is True, "Запись не была обновлена"

    # Проверяем, что описание обновлено в базе данных
    updated_drop = test_session.query(Drop).filter_by(id=drop_id).first()
    assert updated_drop is not None, "Запись не найдена в базе данных"
    assert updated_drop.description == new_description, "Описание не было обновлено"


def test_delete_drop_success(engine_drop, test_session, setup_data, engine_cell, engine_mass_drop):
    """
    Тест успешного удаления записи Drop.
    """
    # Добавляем запись
    tools, plan, group, cell, mass_drop = setup_data
    group_id = group.id
    tools_id = tools[0].id
    cells = engine_cell.get_all_cells()
    cell_id = cells[0].id
    mass_drop_id = engine_mass_drop.get_all_tasks()[0].id
    description = "Выдача инструмента"
    result = engine_drop.add_drop(tools_id=tools_id, mass_drop_id=mass_drop_id, cell_id=cell_id,
                                  description=description)
    assert result is True, "Запись не была добавлена"

    # Проверяем, что запись добавлена в базу данных
    drop = test_session.query(Drop).filter_by(tools_id=tools_id, mass_drop_id=mass_drop_id,
                                              cell_id=cell_id).first()
    drop_id = drop.id
    # Удаляем запись
    result = engine_drop.delete_drop(drop_id)
    assert result is True, "Запись не была удалена"

    # Проверяем, что запись удалена
    deleted_drop = test_session.query(Drop).filter_by(id=drop_id).first()
    assert deleted_drop is None, "Удаленная запись все еще присутствует в базе данных"

# def test_add_drop_failure(engine_drop, test_session):
#     """
#     Тест на неудачное добавление записи Drop с недостающими обязательными полями.
#     """
#     # Пропускаем обязательные поля, например tools_id
#     result = engine_drop.add_drop(tools_id=None, mass_drop_id=2, cell_id=3)
#     assert result is False, "Запись была добавлена с недостающим обязательным полем"
