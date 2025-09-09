import random
import traceback

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from DB.Engine.CellCRUD import EngineCell  # Импортируем тестируемый класс
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.StatusCRUD import EngineStatus
from DB.Models.Cell import Cell  # Импортируем модель Cell
from DB.Models.Group import Group  # Импортируем модель Group
from DB.Models.Plan import Plan
from DB.Models.Status import Status
from DB.Models.Tools import Tools  # Импортируем модель Tools
from DB.Engine.BaseCRUD import BaseCRUD  # Импортируем базовый CRUD-класс
from DB.Data.db import SessionLocal
from DB.Data.db import engine


# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создаёт движок базы данных для тестов (SQLite в памяти).
    """
    # engine = create_engine("sqlite:///:memory:")
    # BaseCRUD.metadata.create_all(bind=engine)
    return engine


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создаёт сессию для тестовой базы данных.
    """
    # Session = sessionmaker(bind=test_engine)
    return SessionLocal()


# Фикстура для экземпляра EngineCell
@pytest.fixture
def engine_cell(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


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


# Фикстура для экземпляра EnginePlan
@pytest.fixture
def engine_plan(test_session):
    """
    Создает экземпляр EnginePlan с тестовой сессией.
    """
    return EnginePlan(session=test_session)


# Фикстура для экземпляра EnginePlan
@pytest.fixture
def engine_status(test_session):
    """
    Создает экземпляр EnginePlan с тестовой сессией.
    """
    return EngineStatus(session=test_session)


@pytest.fixture
def setup_data(test_session, engine_tools, engine_group, engine_plan, engine_cell, engine_status):
    """
    Создает тестовые данные для инструментов, планов и групп.
    """
    engine_tools.delete_all()
    engine_group.delete_all()
    engine_plan.delete_all()
    engine_cell.delete_all()

    all_ids = engine_plan.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])
    # Статус и массовое удаление
    status = Status(
        id=random.randint(1, 9999),
        stype="mass_drop_init",
        description="The status is inactive.",
        created_at=datetime.now()
    )
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
    all_ids = engine_group.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    group = Group(id=_id, name="Old Group", description="Old Description", status=0)

    all_ids = engine_tools.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    tool = Tools(
        id=_id,
        barcode="67890",
        name="Отвертка",
        description="Плоская отвертка",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(tool)
    test_session.add(plan)
    test_session.add(group)
    status_id = engine_status.find_by_name("mass_drop_init")
    if status_id is None:
        test_session.add(status)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    return tool, plan, group, status


def test_add_cell_success(engine_cell, test_session, setup_data, engine_tools, engine_status):
    """
    Тест успешного добавления ячейки.
    """

    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id

    cell_id = engine_cell.get_all_ids()
    cell_id = max(cell_id) + 1 if cell_id else 1

    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )

    result = engine_cell.add_cell(
        index=cell_id,
        number=4,
        groups_id=group_id,
        tools_id=tool_id,
        status_id=status.id,
        description="Test Cell"
    )

    assert result is True, "Ячейка не была добавлена"

    # Проверяем, что ячейка добавлена в базу данных
    added_cell = test_session.query(Cell).filter_by(number=4).first()
    assert added_cell is not None, "Добавленная ячейка не найдена в базе данных"
    assert added_cell.description == "Test Cell"
    engine_cell.delete_cell(added_cell.id)


def test_get_cell_by_id(engine_cell, test_session, engine_status, setup_data, engine_tools):
    """
    Тест получения ячейки по ID.
    """
    # Добавляем тестовую ячейку
    cell_id = engine_cell.get_all_ids()
    cell_id = max(cell_id) + 1 if cell_id else 1
    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )

    engine_cell.add_cell(
        index=cell_id,
        number=4,
        groups_id=group_id,
        tools_id=tool_id,
        status_id=status.id,
        description="Test Get ID"
    )
    test_cell = engine_cell.get(cell_id)
    test_session.add(test_cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем ячейку по ID
    retrieved_cell = engine_cell.get_cell_by_id(test_cell.id)
    assert retrieved_cell is not None, "Ячейка по ID не найдена"
    assert retrieved_cell.description == "Test Get ID"
    engine_cell.delete_cell(retrieved_cell.id)


# def test_get_cells_with_groups_and_tools(engine_cell, test_session, setup_data):
#     """
#     Тест получения всех ячеек с загруженными группами и инструментами.
#     """
#     # Добавляем тестовые группы и инструменты
#     # group = Group(name="Test Group")
#     # tool = Tools(name="Test Tool")
#     #
#     # test_session.add_all([group, tool])
#     # test_session.commit()
#     tool, plan, group = setup_data
#     # Добавляем ячейку с ссылками на группу и инструмент
#     cell = Cell(
#         number=3,
#         description="Test Join",
#         groups_id=group.id,
#         tools_id=tool.id
#     )
#     test_session.add(cell)
#     test_session.commit()
#
#     # Проверяем метод получения всех ячеек
#     cells = engine_cell.get_cells_with_groups_and_tools()
#     assert len(cells) > 0, "Ячейки не найдены"
#     assert cells[0].groups.name == "Test Group"
#     assert cells[0].tools.name == "Test Tool"


def test_update_cell(engine_cell, test_session, engine_group, setup_data, engine_tools, engine_status):
    """
    Тест успешного обновления ячейки.
    """
    cell_id = engine_cell.get_all_ids()
    cell_id = max(cell_id) + 1 if cell_id else 1
    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )
    engine_cell.add_cell(
        index=cell_id,
        number=cell_id,
        groups_id=group_id,
        tools_id=tool_id,
        status_id=status.id
    )
    cell = engine_cell.get(cell_id)
    test_session.add(cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Обновляем ячейку
    result = engine_cell.update_cell(cell.id, description="After Update")
    assert result is True, "Ячейка не была обновлена"

    # Проверяем обновление
    updated_cell = test_session.query(Cell).filter_by(id=cell.id).first()
    assert updated_cell.description == "After Update"
    engine_cell.delete_cell(updated_cell.id)


def test_delete_cell(engine_cell, test_session, setup_data, engine_tools, engine_status):
    """
    Тест успешного удаления ячейки.
    """
    # Добавляем тестовую ячейку
    cell_id = engine_cell.get_all_ids()
    cell_id = max(cell_id) + 1 if cell_id else 1
    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )
    engine_cell.add_cell(
        index=cell_id,
        number=4,
        groups_id=group_id,
        tools_id=tool_id,
        status_id=status.id
    )
    cell = engine_cell.get(cell_id)

    test_session.add(cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаляем ячейку
    result = engine_cell.delete_cell(cell.id)
    assert result is True, "Ячейка не была удалена"

    # Проверяем, что ячейка удалена
    deleted_cell = test_session.query(Cell).filter_by(id=cell.id).first()
    assert deleted_cell is None, "Удалённая ячейка всё ещё присутствует в базе данных"


def test_get_cells_by_group(engine_cell, test_session, engine_group, setup_data, engine_tools, engine_status):
    """
    Тест получения ячеек по группе.
    """
    # Добавляем тестовую группу и ячейку
    group = Group(name="Group for Test")
    test_session.add(group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise
    # Добавляем тестовую ячейку
    cell_id = engine_cell.get_all_ids()
    cell_id = max(cell_id) + 1 if cell_id else 1
    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )
    engine_cell.add_cell(
        index=cell_id,
        number=4,
        groups_id=group_id,
        tools_id=tool_id,
        status_id=status.id,
        description="Group Cell"
    )
    cell = engine_cell.get(cell_id)

    test_session.add(cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Проверяем метод
    cells = engine_cell.get_cells_by_group(group.id)
    assert len(cells) == 1, "Ячейки для группы не найдены"
    assert cells[0].description == "Group Cell"
    engine_cell.delete_cell(cell.id)
    engine_group.delete_group(group.id)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise


def test_get_cells_by_tool(engine_cell, test_session, engine_tools, setup_data, engine_status):
    """
    Тест получения ячеек по инструменту.
    """
    # Добавляем тестовый инструмент и ячейку

    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )
    cell_id = engine_cell.get_all_ids()
    cell_id = max(cell_id) + 1 if cell_id else 1
    engine_cell.add_cell(
        index=cell_id,
        number=4,
        groups_id=group_id,
        tools_id=tool_id,
        status_id=status.id,
        description="Tool Cell"
    )
    cell = engine_cell.get(cell_id)

    test_session.add(cell)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Проверяем метод
    cells = engine_cell.get_cells_by_tool(tool.id)
    assert len(cells) == 1, "Ячейки для инструмента не найдены"
    assert cells[0].description == "Tool Cell"
    engine_cell.delete_cell(cell.id)
    engine_tools.delete_tool(tool.id)
    # engine_group.delete_group(group.id)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise


def test_get_all_cells(engine_cell, test_session, setup_data, engine_tools, engine_group, engine_status):
    """
    Тест получения всех ячеек.
    """
    # Удаляем все ячейки для чистоты теста
    test_session.query(Cell).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise
    tool, plan, group, status = setup_data
    group_id = group.id
    tools_by_group = engine_tools.get_tools_by_group(group_id)
    tool_id = tools_by_group[0].id
    status = engine_status.find_by_name("mass_drop_init")
    if not status:
        index = max(engine_status.get_all_ids(), default=0)
        engine_status.add(
            index=index + 1,
            stype="mass_drop_init",
            description="Объявлена массовая загрузка"
        )
    # Добавляем несколько тестовых ячеек
    for i in range(3):
        cell_id = engine_cell.get_all_ids()
        cell_id = max(cell_id) + 1 if cell_id else 1
        engine_cell.add_cell(
            index=cell_id,
            number=cell_id,
            groups_id=group_id,
            tools_id=tool_id,
            status_id=status.id,
            description="Group Cell"
        )
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Проверяем метод
    cells = engine_cell.get_all_cells()
    assert len(cells) >= 2, "Количество всех ячеек неверно"
    test_session.query(Plan).delete()
    test_session.query(Tools).delete()
    test_session.query(Group).delete()
    test_session.query(Cell).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise
