import random

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
    Создает тестовые данные для инструментов, планов и групп.
    """
    mapper.e_cell.delete_all()
    mapper.e_tools.delete_all()
    mapper.e_group.delete_all()
    plan_id = max(mapper.e_plan.get_all_ids(), default=0) + 1
    mapper.e_plan.add_plan(
        plan_id=plan_id,
        plan_enterprise="TestEnterprise",
        plan_barcode=str(random.randint(111111111111, 999999999999)),
        plan_name="Test Plan",
        plan_description="Test Description",
        plan_designation="Design 1",
        plan_index_list=1,
        plan_list_count=5,
        plan_parent_plan_id=None,
        plan_parent_plan=None,
    )
    group_id = max(mapper.e_group.get_all_ids(), default=0) + 1
    mapper.e_group.add_group(
        index=group_id,
        name="Old Group",
        description="Old Description",
        status=0
    )

    for i in range(2):
        mapper.e_tools.add_tool(
            id=max(mapper.e_tools.get_all_ids(), default=0) + 1,
            barcode=str(random.randint(111111111111, 999999999999)),
            name="Отвертка",
            description="Плоская отвертка",
            img="screwdriver.png",
            plan_id=plan_id,
            groups_id=group_id
        )

    tools = mapper.e_tools.all()
    for tool in tools:
        status = mapper.e_status.find_by_name("mass_drop_init")
        if not status:
            index = max(mapper.e_status.get_all_ids(), default=0)
            mapper.e_status.add(
                index=index + 1,
                stype="mass_drop_init",
                description="Объявлена массовая загрузка"
            )
            status = mapper.e_status.get(index)
        index = max(mapper.e_cell.get_all_ids(), default=0) + 1
        mapper.e_cell.add_cell(
            index=index,
            number=index,
            description=tool.name,
            groups_id=group_id,
            tools_id=tool.id,
            status_id=status.id,
        )
    plan = mapper.e_plan.all()
    group = mapper.e_group.all()
    cells = mapper.e_cell.all()
    return tools, plan, group, cells

def test_read_db_tools_collection_success(mapper, setup_data):
    """
    Тест: успешное извлечение коллекции инструментов.
    """
    tools, plan, group, cells = setup_data

    # Выполнение действия
    result = mapper.read_db_tools_collection(group[0].id)

    # Проверяем результат
    assert len(result) >= 2
    assert result[0] == tools[0]
    assert result[1] == tools[1]


def test_read_db_tools_collection_empty_group(mapper):
    """
    Тест: пустая группа инструментов.
    """
    # Выполнение действия
    result = mapper.read_db_tools_collection(group_id=2)

    # Проверяем результат
    assert result == []