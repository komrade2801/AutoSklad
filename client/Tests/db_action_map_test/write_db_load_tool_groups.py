import datetime

import pytest
from faker import Faker
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    return Faker()


@pytest.fixture
def mapper():
    return ActionMapper()


def test_write_db_drop_tool_groups_success(mapper, fake_data):
    # Создание фиктивного mass_drop
    mass_drop_id = max(mapper.e_mass_drop.get_all_ids(), default=0) + 1
    mapper.e_mass_drop.add(id=mass_drop_id, description=fake_data.word())

    # Создание связанных записей Drop
    drop_ids = []
    cell_ids = []
    tools_ids = []
    for i in range(2):
        drop_id = max(mapper.e_drop.get_all_ids(), default=0) + 1
        cell_id = max(mapper.e_cell.get_all_ids(), default=0) + 1
        tool_id = max(mapper.e_tools.get_all_ids(), default=0) + 1

        mapper.e_drop.add(id=drop_id, cell_id=cell_id, tools_id=tool_id, mass_drop_id=mass_drop_id)
        mapper.e_tools.add_tool(
            id=tool_id,
            barcode=fake_data.ean(length=8),
            name=fake_data.word(),
            description ="test",
            img ="test.jpg",
            plan_id =1,
            groups_id =1,
        )
        tools = mapper.e_tools.get_tool_by_id(tool_id)
        all_statuses = mapper.e_status.all()
        status = next((s for s in all_statuses if s.stype == "mass_load_ready"), None)

        if not status:
            status_id = mapper.e_status.add(
                index=max(mapper.e_status.get_all_ids(), default=0) + 1,
                stype="mass_load_ready",
                description="Инструмент готов к выдаче"
            )
        else:
            status_id = status.id

        mapper.e_cell.add_cell(
            index=cell_id,
            number=fake_data.random_int(min=1, max=100),
            tools_id=tools.id,
            status_id=status_id,
            groups_id=tools.groups_id,
            description="test",
        )

        drop_ids.append(drop_id)
        cell_ids.append(cell_id)
        tools_ids.append(tool_id)

    # Создание операций DropOperations
    operation_ids = []
    history_ids = []
    for index in range(len(drop_ids)):
        drop_id = drop_ids[index]
        operation_id = max(mapper.e_drop_operations.get_all_ids(), default=0) + 1
        history_id = max(mapper.e_history.get_all_ids(), default=0) + 1

        mapper.e_drop_operations.add(
            id=operation_id,
            drop_id=drop_id,
            tools_id=fake_data.random_int(min=1, max=100),
            status_id=fake_data.random_int(min=1, max=10),
            history_id=history_id
        )
        mapper.e_history.add_history(
            id=history_id,
            user_id=1,
            role_id=1,
            tools_id=tools_ids[index],
            datetime_value=datetime.datetime.now(),
            status="test",
            description=fake_data.sentence(),

        )

        operation_ids.append(operation_id)
        history_ids.append(history_id)

    # Выполнение функции
    result = mapper.write_db_drop_tool_groups()

    # Проверка результата
    assert result is True

    # Проверка, что данные удалены
    assert mapper.e_mass_drop.get(mass_drop_id) is None
    for drop_id in drop_ids:
        assert mapper.e_drop.get(drop_id) is None
    for cell_id in cell_ids:
        assert mapper.e_cell.get(cell_id) is None
    for tool_id in tools_ids:
        assert mapper.e_tools.get(tool_id) is None
    for operation_id in operation_ids:
        assert mapper.e_drop_operations.get(operation_id) is None
    for history_id in history_ids:
        assert mapper.e_history.get(history_id) is None


def test_write_db_drop_tool_groups_failure(mapper):
    # Принудительно выбрасываем исключение для проверки обработки ошибок
    mapper.e_mass_drop.get_all_ids = lambda: []  # Подменяем метод

    result = mapper.write_db_drop_tool_groups()
    assert result is False


if __name__ == "__main__":
    pytest.main()
