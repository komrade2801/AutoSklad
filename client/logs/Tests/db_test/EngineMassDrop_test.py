import traceback

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Data.base import Base
from DB.Models.MassDrop import MassDrop
from DB.Engine.MassDropCRUD import EngineMassDrop  # Импортируем класс для тестирования
from DB.Data.db import SessionLocal
from DB.Data.db import engine


# Фикстура для создания тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных в памяти.
    """
    # engine = create_engine('sqlite:///:memory:')
    # Base.metadata.create_all(engine)
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineMassDrop
@pytest.fixture
def engine_mass_drop(test_session):
    """
    Создает экземпляр EngineMassDrop с тестовой сессией.
    """
    return EngineMassDrop(test_session)


def test_add_task_success(engine_mass_drop, test_session):
    """
    Тест успешного добавления задачи.
    """
    engine_mass_drop.delete_all()
    description = "Удаление устаревших данных"

    result = engine_mass_drop.add_task(description)
    assert result is True, "Задача не была добавлена"

    # Проверяем, что задача добавлена в базу данных
    added_task = test_session.query(MassDrop).filter_by(description=description).first()
    assert added_task is not None, "Добавленная задача не найдена в базе данных"
    assert added_task.description == description


def test_get_task_by_id(engine_mass_drop, test_session):
    """
    Тест получения задачи по ID.
    """
    description = "Удаление устаревших данных"
    task = MassDrop(description=description)
    test_session.add(task)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Получаем задачу по ID
    result = engine_mass_drop.get_task(task.id)
    assert result is not None, "Задача по ID не найдена"
    assert result.description == description


def test_update_task_success(engine_mass_drop, test_session):
    """
    Тест успешного обновления задачи.
    """
    description = "Удаление устаревших данных"
    task = MassDrop(description=description)
    test_session.add(task)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Обновляем описание задачи
    new_description = "Удаление старых записей"
    result = engine_mass_drop.update_task(task.id, description=new_description)
    assert result is True, "Задача не была успешно обновлена"

    # Проверяем, что описание обновлено
    updated_task = test_session.query(MassDrop).filter_by(id=task.id).first()
    assert updated_task.description == new_description


def test_update_task_not_found(engine_mass_drop):
    """
    Тест обновления несуществующей задачи.
    """
    result = engine_mass_drop.update_task(task_id=999, description="Новое описание")
    assert result is False, "Обновление несуществующей задачи не должно быть успешным"


def test_delete_task_success(engine_mass_drop, test_session):
    """
    Тест успешного удаления задачи.
    """
    description = "Удаление устаревших данных"
    task = MassDrop(description=description)
    test_session.add(task)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        print(traceback.format_exc())
        raise

    # Удаляем задачу
    result = engine_mass_drop.delete_task(task.id)
    assert result is True, "Задача не была успешно удалена"

    # Проверяем, что задача удалена
    deleted_task = test_session.query(MassDrop).filter_by(id=task.id).first()
    assert deleted_task is None, "Удалённая задача всё ещё присутствует в базе данных"


def test_delete_task_not_found(engine_mass_drop):
    """
    Тест удаления несуществующей задачи.
    """
    result = engine_mass_drop.delete_task(task_id=999)
    assert result is False, "Удаление несуществующей задачи не должно быть успешным"

# def test_count_tasks(engine_mass_drop, test_session):
#     """
#     Тест подсчета количества задач.
#     """
#     # Добавляем несколько задач
#     descriptions = ["Задача 1", "Задача 2", "Задача 3"]
#     for description in descriptions:
#         task = MassDrop(description=description)
#         test_session.add(task)
#     test_session.commit()
#
#     # Получаем количество задач
#     result = engine_mass_drop.count_tasks()
#     assert result == 3, "Количество задач в базе данных неверно"


# def test_add_task_integrity_error(engine_mass_drop, test_session):
#     """
#     Тест обработки ошибки при добавлении задачи с некорректными данными.
#     """
#     # Добавляем задачу с пустым описанием, если это запрещено в базе данных
#     result = engine_mass_drop.add_task(description=None)
#     assert result is False, "Задача с некорректными данными добавлена"
#
#     # Проверяем, что задача с пустым описанием не добавлена в базу данных
#     added_task = test_session.query(MassDrop).filter_by(description=None).first()
#     assert added_task is None, "Задача с некорректными данными найдена в базе данных"


# def test_get_all_tasks(engine_mass_drop, test_session):
#     """
#     Тест получения всех задач.
#     """
#     # Добавляем несколько задач
#     descriptions = ["Задача 1", "Задача 2", "Задача 3"]
#     for description in descriptions:
#         task = MassDrop(description=description)
#         test_session.add(task)
#     test_session.commit()
#
#     # Получаем все задачи
#     result = engine_mass_drop.get_all_tasks()
#     assert len(result) == 3, "Количество всех задач неверно"
#     assert all(task.description in descriptions for task in result)
