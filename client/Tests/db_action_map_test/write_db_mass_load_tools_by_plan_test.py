import pytest
from faker import Faker

from DB.Models.Cell import Cell
from DB.Models.Tools import Tools
from EventsSystem.action_db import ActionMapper, MassLoadLenEqCellToolsError


# from action_mapper import ActionMapper, MassLoadLenEqCellToolsError


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


@pytest.fixture
def mapper():
    return ActionMapper()


def test_write_db_mass_load_tools_by_plan_success(mapper, fake_data):
    # Генерация тестовых данных
    # Добавление плана
    plan_indx = mapper.e_plan.get_all_ids()
    if not plan_indx:
        plan_indx = 1
    else:
        plan_indx = max(plan_indx) + 1

    mapper.e_plan.add(
        id=plan_indx,
        enterprise=fake_data.company(),
        barcode=fake_data.ean(length=13),
        name=fake_data.word(),
        description=fake_data.sentence(),
        designation=fake_data.word(),
        index_list=fake_data.random_int(min=1, max=10),
        list_count=fake_data.random_int(min=1, max=10)
    )

    # Добавление группы
    group_indx = mapper.e_group.get_all_ids()
    if not group_indx:
        group_indx = 1
    else:
        group_indx = max(group_indx) + 1

    mapper.e_group.add(
        id=group_indx,
        name=fake_data.word(),
        description=fake_data.sentence(),
        status=fake_data.random_int(min=0, max=1)
    )
    group = mapper.e_group.get(group_indx)
    plan = mapper.e_plan.get(plan_indx)
    # Добавление инструментов и ячеек
    tools_data = []
    cells_data = []
    for i in range(1, 3):

        tools_indx = mapper.e_tools.get_all_ids()
        if not tools_indx:
            tools_indx = 1
        else:
            tools_indx = max(tools_indx) + 1

        cell_indx = mapper.e_cell.get_all_ids()
        if not cell_indx:
            cell_indx = 1
        else:
            cell_indx = max(cell_indx) + 1

        barcode = fake_data.ean(length=8)
        name = fake_data.word()
        description = fake_data.sentence()
        img = fake_data.file_name(extension='png')

        mapper.e_tools.add_tool(
            id=tools_indx,
            barcode=barcode,
            name=name,
            description=description,
            img=img,
            plan_id=plan.id,
            groups_id=group.id
        )
        tool = mapper.e_tools.get(tools_indx)
        tools_data.append(tool)

        status = mapper.e_status.find_by_name("mass_drop_init")

        if not status:
            index = max(mapper.e_status.get_all_ids(), default=0)
            mapper.e_status.add(
                index=index + 1,
                stype="mass_drop_init",
                description="Объявлена массовая загрузка"
            )

        mapper.e_cell.add_cell(
            index=cell_indx,
            number=cell_indx,
            groups_id=None,
            tools_id=tools_indx,
            status_id=status.id
        )
        cell = mapper.e_cell.get(cell_indx)
        cells_data.append(cell)

    # Выполнение действия
    action = 'write_db_mass_load_tools_by_plan'
    result = mapper.execute(action, plan.id, tools_data, cells_data)

    # Проверка результата
    assert result is True


def test_write_db_mass_load_tools_by_plan_length_mismatch(mapper, fake_data):
    # Генерация тестовых данных с несовпадающими длинами
    barcode = fake_data.ean(length=8)
    name = fake_data.word()
    description = fake_data.sentence()
    img = fake_data.file_name(extension='png')

    tools_data = [
        Tools(
            id=9999,
            barcode=barcode,
            name=name,
            description=description,
            img=img,
            plan_id=1,
            groups_id=1
        )
    ]
    cells_data = [
        Cell(
            id=9998,
            number=149,
            description="test",
            groups_id=1,
            tools_id=1,
        ),
        Cell(
            id=9999,
            number=150,
            description="test",
            groups_id=1,
            tools_id=1,
        )
    ]

    # Проверка на выброс исключения
    with pytest.raises(MassLoadLenEqCellToolsError):
        mapper.write_db_mass_load_tools_by_plan(1, tools_data, cells_data)


# Если необходимо, добавьте другие тесты для проверки граничных случаев и ошибок
if __name__ == "__main__":
    pytest.main()
