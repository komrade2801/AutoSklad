import pytest
from unittest.mock import MagicMock
from faker import Faker
from DB.Models.User import User
from DB.Models.Role import Role
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake

@pytest.fixture
def mapper():
    mapper = ActionMapper()
    mapper.e_user.get_user_by_id = MagicMock()
    mapper.e_role.get_role_by_id = MagicMock()
    mapper.e_rights.get_rights_by_role_id = MagicMock()
    mapper.e_rights.add_right = MagicMock(return_value=True)
    mapper.e_rights.get_all_ids = MagicMock()
    return mapper

def test_write_db_rights_by_user_id_success(mapper, fake_data):
    user_id = 1
    role_id = 10
    rights_data = [
        {"name": fake_data.word(), "description": fake_data.sentence()},
        {"name": fake_data.word(), "description": fake_data.sentence()}
    ]
    role_name = fake_data.job()
    role_description = fake_data.sentence()
    role = Role(
        id=1,
        Name=role_name,
        Description=role_description,
        ParentRole_id=None,
        parent_role=None,
    )

    user = User(
        id=1,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )
    role = Role(id=role_id, Name=fake_data.word(), Description=fake_data.sentence(), ParentRole_id=None)
    existing_rights = []

    mapper.e_user.get_user_by_id.return_value = user
    mapper.e_role.get_role_by_id.return_value = role
    mapper.e_rights.get_rights_by_role_id.return_value = existing_rights
    mapper.e_rights.get_all_ids.return_value = [1, 2]

    result = mapper.execute('write_db_rights_by_user_id', user_id, rights_data)

    assert result is True
    # rights_indx = mapper.e_rights.get_all_ids()
    # rights_indx = min(rights_indx, default=0)
    #
    # mapper.e_rights.add_right.assert_any_call(
    #     index=rights_indx,
    #     name=rights_data[0]['name'],
    #     description=rights_data[0]['description'],
    #     role_id=role_id
    # )
    # rights_indx_1 = mapper.e_rights.get_all_ids()
    # rights_indx_1 = max(rights_indx_1, default=0)
    #
    # mapper.e_rights.add_right.assert_any_call(
    #     index=rights_indx_1,
    #     name=rights_data[1]['name'],
    #     description=rights_data[1]['description'],
    #     role_id=role_id
    # )

def test_write_db_rights_with_duplicate_names(mapper, fake_data):
    user_id = 1
    role_id = 10
    rights_data = [
        {"name": "DuplicateRight", "description": "Some description"},
        {"name": "DuplicateRight", "description": "Different description"}
    ]
    role_name = fake_data.job()
    role_description = fake_data.sentence()
    role = Role(
        id=1,
        Name=role_name,
        Description=role_description,
        ParentRole_id=None,
        parent_role=None,
    )

    user = User(
        id=1,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )
    existing_rights = []

    mapper.e_user.get_user_by_id.return_value = user
    mapper.e_role.get_role_by_id.return_value = role
    mapper.e_rights.get_rights_by_role_id.return_value = existing_rights

    result = mapper.execute('write_db_rights_by_user_id', user_id, rights_data)

    assert result is False
    mapper.e_rights.add_right.assert_not_called()

def test_write_db_rights_invalid_data(mapper):
    user_id = 1
    rights_data = [{"name": None, "description": ""}]

    mapper.e_user.get_user_by_id.return_value = MagicMock()
    mapper.e_role.get_role_by_id.return_value = MagicMock()

    result = mapper.execute('write_db_rights_by_user_id', user_id, rights_data)

    assert result is False
    mapper.e_rights.add_right.assert_not_called()

def test_read_db_rights_no_rights_for_role(mapper, fake_data):

    role_name = fake_data.job()
    role_description = fake_data.sentence()
    role = Role(
        id=1,
        Name=role_name,
        Description=role_description,
        ParentRole_id=None,
        parent_role=None,
    )

    user = User(
        id=1,
        barcode=fake_data.ean(length=8),
        Code=fake_data.random_number(digits=4),
        FirstName=fake_data.first_name(),
        password=str(fake_data.random_number(digits=4)),
        SecondName=fake_data.last_name(),
        Family="Single",
        Role_id=role.id,
    )

    mapper.e_user.get_user_by_id.return_value = user
    mapper.e_role.get_role_by_id.return_value = role
    mapper.e_rights.get_rights_by_role_id.return_value = []

    result = mapper.execute('read_db_rights_by_user_id', user.id)

    assert result == []
    mapper.e_rights.get_rights_by_role_id.assert_called_once_with(role.id)

# def test_database_error_during_read(mapper, fake_data):
#     user_id = mapper.e_user.get_all_ids()
#     user_id = max(user_id, default=0) + 1
#     role_id = mapper.e_role.get_all_ids()
#     role_id = max(role_id, default=0) + 1
#
#     role_name = fake_data.job()
#     role_description = fake_data.sentence()
#     role = Role(
#         id=role_id,
#         Name=role_name,
#         Description=role_description,
#         ParentRole_id=None,
#         parent_role=None,
#     )
#
#     user = User(
#         id=user_id,
#         barcode=fake_data.ean(length=8),
#         Code=fake_data.random_number(digits=4),
#         FirstName=fake_data.first_name(),
#         password=str(fake_data.random_number(digits=4)),
#         SecondName=fake_data.last_name(),
#         Family="Single",
#         Role_id=role.id,
#     )
#
#     mapper.e_user.get_user_by_id.return_value = user
#     # Имитация DatabaseError при вызове get_role_by_id
#     mapper.e_role.get_role_by_id.side_effect = DatabaseError("Database error", params=None, orig=None)
#
#     # Ожидаем выброс DatabaseError
#     with pytest.raises(DatabaseError):
#         mapper.execute('read_db_rights_by_user_id', user_id)
#
# def test_database_error_during_write(mapper, fake_data):
#     user_id = 1
#     rights_data = [{"name": "View", "description": "Can view records"}]
#     role_name = fake_data.job()
#     role_description = fake_data.sentence()
#     role = Role(
#         id=1,
#         Name=role_name,
#         Description=role_description,
#         ParentRole_id=None,
#         parent_role=None,
#     )
#
#     user = User(
#         id=1,
#         barcode=fake_data.ean(length=8),
#         Code=fake_data.random_number(digits=4),
#         FirstName=fake_data.first_name(),
#         password=str(fake_data.random_number(digits=4)),
#         SecondName=fake_data.last_name(),
#         Family="Single",
#         Role_id=role.id,
#     )
#
#     mapper.e_user.get_user_by_id.return_value = user
#     mapper.e_rights.add_right.side_effect = DatabaseError("Database error", params=None, orig=None)
#
#     with pytest.raises(DatabaseError):
#         mapper.execute('write_db_rights_by_user_id', user_id, rights_data)
