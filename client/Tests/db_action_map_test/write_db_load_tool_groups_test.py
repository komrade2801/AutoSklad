import datetime

import pytest
from faker import Faker
from DB.Models.Role import Role
from DB.Models.User import User
from EventsSystem.action_db import ActionMapper

@pytest.fixture
def fake_data():
    return Faker()

@pytest.fixture
def mapper():
    return ActionMapper()

def test_write_db_load_tool_groups_success(mapper, fake_data):

    mapper.e_load_operations.delete_all()
    mapper.e_cell.delete_all()
    mapper.e_history.delete_all()
    mapper.e_status.delete_all()
    mapper.e_tools.delete_all()
    mapper.e_load.delete_all()
    mapper.e_mass_load.delete_all()
    mapper.e_user.delete_all()
    mapper.e_role.delete_all()

    role = Role(
        id=max((mapper.e_role.get_all_ids()), default=0)+1,
        Name="Admin",
        Description="Root user"
    )
    user = User(
        id=max((mapper.e_user.get_all_ids()), default=0)+1,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )

    mapper.e_role.add_role(
        name=role.name,
        description=role.description,
    )

    mapper.e_user.add_user(
        index=user.id,
        barcode=user.barcode,
        code=user.code,
        first_name=user.first_name,
        second_name=user.second_name,
        family=user.family,
        password=user.password,
        role_id=user.role_id,
    )
    # Создание фиктивного mass_load
    mass_load_id = max(mapper.e_mass_load.get_all_ids(), default=0) + 1
    mapper.e_mass_load.add(id=mass_load_id, description=fake_data.word())

    # Создание связанных записей Load
    load_ids = []
    cell_ids = []
    tools_ids = []
    for i in range(2):
        load_id = max(mapper.e_load.get_all_ids(), default=0) + 1
        cell_id = max(mapper.e_cell.get_all_ids(), default=0) + 1
        tool_id = max(mapper.e_tools.get_all_ids(), default=0) + 1

        mapper.e_load.add(id=load_id, cell_id=cell_id, tools_id=tool_id, mass_load_id=mass_load_id)
        mapper.e_tools.add_tool(
            id=tool_id,
            barcode=fake_data.ean(length=8),
            name=fake_data.word(),
            description="test",
            img="test.jpg",
            plan_id=1,
            groups_id=1,
        )
        tools = mapper.e_tools.get_tool_by_id(tool_id)
        all_statuses = mapper.e_status.all()
        status_id = None
        # status = next((s for s in all_statuses if s.stype == "mass_load_ready"), None)

        status = mapper.e_status.find_by_name("mass_load_init")

        if not status:
            index = max(mapper.e_status.get_all_ids(), default=0)
            mapper.e_status.add(
                index=index + 1,
                stype="mass_load_init",
                description="Объявлена массовая загрузка"
            )

        mapper.e_cell.add_cell(
            index=cell_id,
            number=cell_id,
            tools_id=tools.id,
            status_id=max(mapper.e_status.get_all_ids()),
            groups_id=tools.groups_id,
            description="test",
        )

        load_ids.append(load_id)
        cell_ids.append(cell_id)
        tools_ids.append(tool_id)

    # Создание операций LoadOperations
    operation_ids = []
    history_ids = []
    for index in range(len(load_ids)):
        status_id = max(mapper.e_status.get_all_ids())
        load_id = load_ids[index]
        operation_id = max(mapper.e_load_operations.get_all_ids(), default=0) + 1
        history_id = max(mapper.e_history.get_all_ids(), default=0) + 1

        mapper.e_load_operations.add_operation(
            id=operation_id,
            date=datetime.datetime.now(),
            load_id=load_id,
            load_tools_id=tools_ids[index],
            status_id=status_id,
            history_id=history_id,
            description=fake_data.sentence()
        )
        mapper.e_history.add_history(
            id=history_id,
            user_id=user.id,
            role_id=user.role_id,
            tools_id=tools_ids[index],
            datetime_value=datetime.datetime.now(),
            status="test",
            description=fake_data.sentence(),
        )

        operation_ids.append(operation_id)
        history_ids.append(history_id)

    # Выполнение функции
    result = mapper.write_db_load_tool_groups(user_id=user.id, status="ready", description="test")

    # Проверка результата
    assert result is True

    # Проверка обновления статусов
    for cell_id in cell_ids:
        cell = mapper.e_cell.get(cell_id)
        assert cell.status_id != status_id

    for load_id in load_ids:
        operations = mapper.e_load_operations.get_operations_by_load_id(load_id)
        operation_id = -1
        for operation in operations:
            if operation_id < operation.id:
                operation_id = operation.id
        operation = mapper.e_load_operations.get(operation_id)
        assert operation.status_id != status_id

def test_write_db_load_tool_groups_failure(mapper):
    # Принудительно выбрасываем исключение для проверки обработки ошибок
    mapper.e_mass_load.get_all_ids = lambda: []  # Подменяем метод

    result = mapper.write_db_load_tool_groups(user_id=1, status="ready", description="test")
    assert result is False

if __name__ == "__main__":
    pytest.main()
