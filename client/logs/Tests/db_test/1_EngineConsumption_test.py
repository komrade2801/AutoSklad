import random
import traceback

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# from DB import config
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.StatusCRUD import EngineStatus
from DB.Models.Cell import Cell
from DB.Models.Consumption import Consumption
from DB.Engine.ConsumptionCRUD import EngineConsumption
from DB.Data.db import SessionLocal, engine
from DB.Models.Group import Group
from DB.Models.Plan import Plan
from DB.Models.Tools import Tools
from DB.Models.Status import Status


# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    # config.db_path = config.db_path_test
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    return SessionLocal()


# Фикстура для экземпляра EngineConsumption
@pytest.fixture
def engine_consumption(test_session):
    """
    Создает экземпляр EngineConsumption с тестовой сессией.
    """
    return EngineConsumption(session=test_session)


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


@pytest.fixture
def engine_status(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineStatus(session=test_session)


@pytest.fixture
def setup_data(test_session, engine_cell, engine_tools, engine_group, engine_consumption, engine_status):
    """
    Создает тестовые данные для инструментов, планов и групп.
    """
    engine_cell.delete_all()
    engine_tools.delete_all()
    engine_group.delete_all()
    engine_consumption.delete_all()

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
    for i in range(2):
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

    cells = []
    for tool in tools:
        status = engine_status.find_by_name("mass_drop_init")
        if not status:
            index = max(engine_status.get_all_ids(), default=0)
            engine_status.add(
                index=index + 1,
                stype="mass_drop_init",
                description="Объявлена массовая загрузка"
            )
            status = engine_status.get(index)
        index = max(engine_cell.get_all_ids(), default=0) + 1
        cell = Cell(
            id=index,
            number=index,
            description=tool.name,
            groups_id=group.id,
            tools_id=tool.id,
            status_id=status.id,
        )
        test_session.add(cell)
        cells.append(cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    return tools, plan, group, cells


def test_get_by_tool_id(engine_consumption, test_session, engine_group, engine_tools, setup_data, engine_cell):
    """
    Тест получения записей расхода по идентификатору инструмента.
    """
    # Добавляем тестовые данные

    tools, plan, group, cell = setup_data

    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    cells_id = max(engine_cell.get_all_ids(), default=0) + 1

    consumption1 = Consumption(
        tools_id=tool_id,
        cell_id=cells_id
    )
    consumption2 = Consumption(
        tools_id=tool_id,
        cell_id=cells_id
    )
    test_session.add(consumption1)
    test_session.add(consumption2)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Проверяем получение записей по идентификатору инструмента
    result = engine_consumption.get_by_tool_id(tool_id)
    assert len(result) > 1, "Количество записей расхода по инструменту не совпадает"
    assert all(consumption.tools_id == tool_id for consumption in result)
    test_session.query(Plan).delete()
    test_session.query(Tools).delete()
    test_session.query(Group).delete()
    test_session.query(Consumption).delete()


def test_get_by_cell_id(engine_consumption, test_session, setup_data, engine_group, engine_tools, engine_cell):
    """
    Тест получения записей расхода по идентификатору ячейки.
    """
    # Добавляем тестовые данные

    tool, plan, group, cell = setup_data

    groups = engine_group.get_all_groups()
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_1_id = tools_by_group[0].id
    tool_2_id = tools_by_group[1].id
    cell_1_id = engine_cell.get_cells_by_tool(tool_1_id)[0].id
    cell_2_id = engine_cell.get_cells_by_tool(tool_2_id)[0].id
    consumption1 = Consumption(tools_id=tool_1_id, cell_id=cell_1_id)
    consumption2 = Consumption(tools_id=tool_2_id, cell_id=cell_2_id)
    test_session.add(consumption1)
    test_session.add(consumption2)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Проверяем получение записей по идентификатору ячейки
    result = engine_consumption.get_by_cell_id(cell_1_id)
    assert len(result) == 1, "Количество записей расхода по ячейке не совпадает"
    test_session.query(Plan).delete()
    test_session.query(Group).delete()
    test_session.query(Tools).delete()
    test_session.query(Consumption).delete()


# def test_get_recent(engine_consumption, test_session, engine_cell, engine_tools, engine_group, setup_data):
#     """
#     Тест получения последних записей расхода.
#     """
#     tool, plan, group, cell = setup_data
#
#     groups = engine_group.get_all_groups()
#     group_id = group.id
#     tools_by_group = engine_tools.get_tools_by_group(group_id)
#     tool_2_id = tools_by_group[1].id
#     cell_2_id = engine_cell.get_cells_by_tool(tool_2_id)[0].id
#     test_session.commit()
#     # Добавляем несколько записей
#     for i in range(15):
#         consumption = Consumption(tools_id=tool_2_id, cell_id=cell_2_id)
#         test_session.add(consumption)
#     test_session.commit()
#
#     # Получаем последние 5 записей
#     result = engine_consumption.get_recent(limit=5)
#     assert len(result) > 3, "Количество последних записей расхода неверно"
#     test_session.query(Plan).delete()
#     test_session.query(Tools).delete()
#     test_session.query(Group).delete()
#     test_session.query(Consumption).delete()


def test_update_comment(engine_consumption, test_session, setup_data, engine_group, engine_tools, engine_cell):
    """
    Тест обновления комментария для записи расхода.
    """
    tool, plan, group, cell = setup_data

    groups = engine_group.get_all_groups()
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[1].id
    cell_id = engine_cell.get_cells_by_tool(tool_id)[0].id
    # Добавляем запись
    consumption = Consumption(tools_id=tool_id, cell_id=cell_id)
    test_session.add(consumption)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Обновляем комментарий
    tools_id = 1
    result = engine_consumption.update_comment(consumption.id, 1, 1)
    assert result is True, "Комментарий не был обновлен"

    # Проверяем обновление
    updated_consumption = test_session.query(Consumption).filter_by(id=consumption.id).first()
    assert updated_consumption.tools_id == tools_id, "Комментарий не обновился"
    test_session.query(Plan).delete()
    test_session.query(Group).delete()
    test_session.query(Tools).delete()
    test_session.query(Cell).delete()
    test_session.query(Consumption).delete()


def test_delete_by_tool_id(engine_consumption, test_session, setup_data, engine_group, engine_tools, engine_cell):
    """
    Тест удаления всех записей расхода по инструменту.
    """
    tool, plan, group, cell = setup_data

    groups = engine_group.get_all_groups()
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_1_id = tools_by_group[0].id
    tool_2_id = tools_by_group[1].id
    cell_1_id = engine_cell.get_cells_by_tool(tool_1_id)[0].id
    cell_2_id = engine_cell.get_cells_by_tool(tool_2_id)[0].id
    # Добавляем запись
    consumption1 = Consumption(tools_id=tool_1_id, cell_id=cell_1_id)
    consumption2 = Consumption(tools_id=tool_2_id, cell_id=cell_2_id)
    test_session.add(consumption1)
    test_session.add(consumption2)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Проверяем удаление
    deleted_count = engine_consumption.delete_by_tool_id(tool_1_id)
    assert deleted_count == 1, "Количество удаленных записей неверно"

    # Проверяем, что записи удалены
    deleted_consumptions = test_session.query(Consumption).filter_by(tools_id=tool_1_id).all()
    assert len(deleted_consumptions) == 0, "Записи не были удалены"
    test_session.query(Plan).delete()
    test_session.query(Group).delete()
    test_session.query(Tools).delete()
    test_session.query(Cell).delete()
    test_session.query(Consumption).delete()


def test_get_by_tool_id_no_results(engine_consumption, test_session):
    """
    Тест получения записей расхода по инструменту, если записей нет.
    """
    # Проверяем, что для несуществующего инструмента не будет записей
    result = engine_consumption.get_by_tool_id(999)
    assert len(result) == 0, "Записи не должны быть найдены для несуществующего инструмента"


def test_get_by_cell_id_no_results(engine_consumption, test_session):
    """
    Тест получения записей расхода по ячейке, если записей нет.
    """
    # Проверяем, что для несуществующей ячейки не будет записей
    result = engine_consumption.get_by_cell_id(999)
    assert len(result) == 0, "Записи не должны быть найдены для несуществующей ячейки"


def test_update_comment_fail(engine_consumption, test_session):
    """
    Тест неудачного обновления комментария для записи расхода (если запись не существует).
    """
    # Попытка обновить несуществующую запись
    result = engine_consumption.update_comment(999, 1,1)
    assert result is False, "Обновление комментария не должно быть успешным"


def test_delete_by_tool_id_no_results(engine_consumption, test_session):
    """
    Тест удаления записей расхода по инструменту, если записей нет.
    """
    # Проверяем удаление записей для несуществующего инструмента
    deleted_count = engine_consumption.delete_by_tool_id(999)
    assert deleted_count == 0, "Количество удаленных записей для несуществующего инструмента не должно быть больше 0"
