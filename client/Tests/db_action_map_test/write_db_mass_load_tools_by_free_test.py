import pytest
from faker import Faker
from DB.Models.Cell import Cell
from DB.Models.Tools import Tools
from EventsSystem.action_db import ActionMapper, MassLoadLenEqCellToolsError, MassLoadToolPlanIDError


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


@pytest.fixture
def mapper():
    return ActionMapper()


def test_write_db_mass_load_tools_by_free_success(mapper, fake_data):
    # Генерация тестовых данных
    tools_data = []
    cells_data = []

    for i in range(1, 3):
        tools_indx = mapper.e_tools.get_all_ids()
        tools_indx = max(tools_indx) + 1 if tools_indx else 1

        cell_indx = mapper.e_cell.get_all_ids()
        cell_indx = max(cell_indx) + 1 if cell_indx else 1

        barcode = fake_data.ean(length=8)
        name = fake_data.word()
        description = fake_data.sentence()
        img = fake_data.file_name(extension='png')

        # Добавляем инструмент
        mapper.e_tools.add_tool(
            id=tools_indx,
            barcode=barcode,
            name=name,
            description=description,
            img=img,
            plan_id=None,  # Штрих-код план должен быть пустым
            groups_id=None
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
    result = mapper.execute("write_db_mass_load_tools_by_free",tools_data, cells_data)

    # Проверка результата
    assert result is True


def test_write_db_mass_load_tools_by_free_len_mismatch(mapper, fake_data):
    # Генерация тестовых данных с несовпадающими длинами
    tools_data = [
        Tools(
            id=9999,
            barcode=fake_data.ean(length=8),
            name=fake_data.word(),
            description=fake_data.sentence(),
            img=fake_data.file_name(extension='png'),
            plan_id=None,
            groups_id=None
        )
    ]
    cells_data = [
        Cell(
            id=9998,
            number=149,
            description="test",
            groups_id=None,
            tools_id=9999,
        ),
        Cell(
            id=9999,
            number=150,
            description="test",
            groups_id=None,
            tools_id=9999,
        ),
        Cell(
            id=10000,
            number=151,
            description="test",
            groups_id=None,
            tools_id=9999,
        )
    ]

    # Проверка на выброс исключения
    with pytest.raises(MassLoadLenEqCellToolsError):
        # mapper.write_db_mass_load_tools_by_free(tools_data, cells_data)
        mapper.execute("write_db_mass_load_tools_by_free",tools_data, cells_data)


def test_write_db_mass_load_tools_by_free_plan_id_not_empty(mapper, fake_data):
    # Генерация тестовых данных с ненулевым идентификатором плана
    tools_data = [
        Tools(
            id=9999,
            barcode=fake_data.ean(length=8),
            name=fake_data.word(),
            description=fake_data.sentence(),
            img=fake_data.file_name(extension='png'),
            plan_id=1,  # Это значение должно быть пустым в данной функции
            groups_id=None
        )
    ]
    cells_data = [
        Cell(
            id=9998,
            number=149,
            description="test",
            groups_id=None,
            tools_id=9999,
        )
    ]

    # Проверка на выброс исключения
    with pytest.raises(MassLoadToolPlanIDError):
        mapper.execute("write_db_mass_load_tools_by_free",tools_data, cells_data)


# Добавьте дополнительные тесты для проверки других крайних случаев и ошибок
if __name__ == "__main__":
    pytest.main()
