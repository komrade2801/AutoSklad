import pytest
from faker import Faker
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    return Faker()


@pytest.fixture
def mapper():
    return ActionMapper()


@pytest.fixture
def setup_data(mapper, fake_data):
    """
    Создает тестовые данные для инструментов, групп, статусов и операций.
    """
    # Очистка всех таблиц перед тестированием
    mapper.e_cell.delete_all()
    mapper.e_tools.delete_all()
    mapper.e_group.delete_all()
    mapper.e_status.delete_all()
    mapper.e_drop_operations.delete_all()
    mapper.e_operations_consumption.delete_all()
    mapper.e_load_operations.delete_all()

    # Создание тестовой группы
    group_id = max(mapper.e_group.get_all_ids(), default=0) + 1
    mapper.e_group.add_group(
        index=group_id,
        name="Test Group",
        description="Group for testing",
        status=0
    )

    # Создание тестового статуса
    status_ready_id = max(mapper.e_status.get_all_ids(), default=0) + 1
    mapper.e_status.add(
        index=status_ready_id,
        stype="load_ready",
        description="Instrument is ready for loading"
    )

    # Добавление инструментов и их привязка к группе
    for i in range(3):
        tool_id = max(mapper.e_tools.get_all_ids(), default=0) + 1
        mapper.e_tools.add_tool(
            id=tool_id,
            barcode=fake_data.ean13(),
            name=f"Tool {i+1}",
            description=f"Description for tool {i+1}",
            img=f"tool{i+1}.png",
            plan_id=None,
            groups_id=group_id
        )
        # Привязка инструмента к ячейке
        cell_id = max(mapper.e_cell.get_all_ids(), default=0) + 1
        mapper.e_cell.add_cell(
            index=cell_id,
            number=cell_id,
            description=f"Cell for tool {i+1}",
            groups_id=group_id,
            tools_id=tool_id,
            status_id=status_ready_id
        )

    return group_id, mapper.e_tools.all()


def test_read_db_tool_names_success(mapper, setup_data):
    """
    Тест: успешное извлечение инструментов из группы.
    """
    group_id, tools = setup_data

    # Выполнение метода
    result = mapper.read_db_tool_names(group_id)

    # Проверка результатов
    assert len(result) == len(tools)
    for tool in tools:
        assert tool in result


def test_read_db_tool_names_empty_group(mapper):
    """
    Тест: пустая группа инструментов.
    """
    # Создание пустой группы
    group_id = max(mapper.e_group.get_all_ids(), default=0) + 1
    mapper.e_group.add_group(
        index=group_id,
        name="Empty Group",
        description="No tools in this group",
        status=0
    )

    # Выполнение метода
    result = mapper.read_db_tool_names(group_id)

    # Проверка результатов
    assert result == []


def test_read_db_tool_names_invalid_conditions(mapper, setup_data):
    """
    Тест: исключение инструментов, не удовлетворяющих условиям.
    """
    group_id, tools = setup_data
    cells = mapper.e_cell.all()
    status_id = max(mapper.e_status.get_all_ids(), default=0) + 1
    mapper.e_status.add(
        index=status_id,
        stype="drop_ready",
        description="Instrument is ready for drop"
    )

    # Изменяем статусы ячеек, чтобы инструменты не проходили проверку
    for cell in cells:
        mapper.e_cell.update_cell_status(cell.id, status_id)

    # Выполнение метода
    result = mapper.read_db_tool_names(group_id)

    # Проверка результатов
    assert result == []
