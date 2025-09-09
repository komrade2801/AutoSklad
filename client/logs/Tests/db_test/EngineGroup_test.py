import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional
from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Models.Group import Group  # Импортируем модель Group
from DB.Models.Tools import Tools  # Импортируем модель Tools
from DB.Models.Cell import Cell
from DB.Engine.GroupCRUD import EngineGroup
from DB.Models.History import History  # Импорт класса History


# Фикстура для создания тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    # engine = create_engine("sqlite:///:memory:")
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    # SessionLocal.configure(bind=engine)
    # session = SessionLocal()
    return SessionLocal(test_engine)


# Фикстура для создания экземпляра EngineGroup
@pytest.fixture
def engine_group(test_session):
    """
    Создает экземпляр EngineGroup с тестовой сессией.
    """
    return EngineGroup(session=test_session)


def test_add_group_success(engine_group, test_session):
    """
    Тест успешного добавления группы.
    """
    engine_group.delete_all()

    name = "Test Group"
    description = "A test group for testing purposes."
    status = 1  # например, 1 — активный статус

    result = engine_group.add_group(name=name, description=description, status=status)
    assert result is True, "Группа не была добавлена"

    # Проверяем, что группа добавлена в базу данных
    added_group = test_session.query(Group).filter_by(name=name).first()
    assert added_group is not None, "Добавленная группа не найдена в базе данных"
    assert added_group.name == name
    assert added_group.description == description
    assert added_group.status == status


def test_get_group_by_id(engine_group, test_session):
    """
    Тест получения группы по ID.
    """
    # Добавляем группу
    new_group = Group(name="Test Group", description="Test Description", status=1)
    test_session.add(new_group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем группу по ID
    result = engine_group.get_group_by_id(new_group.id)
    assert result is not None, "Группа по ID не найдена"
    assert result.name == new_group.name
    assert result.description == new_group.description
    assert result.status == new_group.status


def test_update_group_success(engine_group, test_session):
    """
    Тест успешного обновления группы.
    """
    # Добавляем группу
    group = Group(name="Old Group", description="Old Description", status=0)
    test_session.add(group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Обновляем группу
    new_name = "Updated Group"
    new_description = "Updated Description"
    result = engine_group.update_group(group.id, name=new_name, description=new_description, status=1)
    assert result is True, "Группа не была обновлена"

    # Проверяем, что изменения сохранены
    updated_group = test_session.query(Group).filter_by(id=group.id).first()
    assert updated_group.name == new_name
    assert updated_group.description == new_description
    assert updated_group.status == 1


def test_delete_group_success(engine_group, test_session):
    """
    Тест успешного удаления группы.
    """
    # Добавляем группу
    group_to_delete = Group(name="Delete Group", description="To be deleted", status=0)
    test_session.add(group_to_delete)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Удаляем группу
    result = engine_group.delete_group(group_to_delete.id)
    assert result is True, "Группа не была успешно удалена"

    # Проверяем, что группа удалена
    deleted_group = test_session.query(Group).filter_by(id=group_to_delete.id).first()
    assert deleted_group is None, "Удалённая группа всё ещё присутствует в базе данных"


def test_get_all_groups(engine_group, test_session):
    """
    Тест получения всех групп.
    """
    # Удаляем все существующие группы
    test_session.query(Group).delete()
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Добавляем несколько групп
    for i in range(5):
        group = Group(name=f"Group {i}", description=f"Description {i}", status=1)
        test_session.add(group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Получаем все группы
    result = engine_group.get_all_groups()
    assert len(result) == 5, "Количество групп не совпадает"
    assert all(isinstance(group, Group) for group in result)


# def test_get_groups_by_status(engine_group, test_session):
#     """
#     Тест получения групп по статусу.
#     """
#     # Добавляем несколько групп с разными статусами
#     for status in [1, 0]:
#         for i in range(3):
#             group = Group(name=f"Group {status}-{i}", description=f"Description {i}", status=status)
#             test_session.add(group)
#     test_session.commit()
#
#     # Получаем группы с активным статусом
#     result_active = engine_group.get_groups_by_status(1)
#     assert len(result_active) == 3, "Количество активных групп неверно"
#
#     # Получаем группы с неактивным статусом
#     result_inactive = engine_group.get_groups_by_status(0)
#     assert len(result_inactive) == 3, "Количество неактивных групп неверно"


def test_get_cells_by_group(engine_group, test_session):
    """
    Тест получения связанных объектов Cells для группы.
    """
    # Добавляем группу и связанные с ней объекты
    new_group = Group(name="Group with Cells", description="Contains cells", status=1)
    test_session.add(new_group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Предположим, что у нас есть связь с моделью Cell
    # Здесь можно добавить создание объектов Cell и привязку их к группе

    result = engine_group.get_cells_by_group(new_group.id)
    assert result is not None, "Связанные объекты Cells не найдены"


def test_get_tools_by_group(engine_group, test_session):
    """
    Тест получения связанных объектов Tools для группы.
    """
    # Добавляем группу и связанные с ней объекты
    new_group = Group(name="Group with Tools", description="Contains tools", status=1)
    test_session.add(new_group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    # Предположим, что у нас есть связь с моделью Tools
    # Здесь можно добавить создание объектов Tools и привязку их к группе

    result = engine_group.get_tools_by_group(new_group.id)
    assert result is not None, "Связанные объекты Tools не найдены"
