import random
import time

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Engine.BaseCRUD import BaseCRUD
from DB.Models.MassLoad import MassLoad
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Data.db import SessionLocal
from DB.Data.db import engine


# Фикстура для настройки тестовой базы данных (в памяти)
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    # Создание таблицы в базе данных
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineMassLoad
@pytest.fixture
def engine_mass_load(test_session):
    """
    Создает экземпляр EngineMassLoad с тестовой сессией.
    """
    return EngineMassLoad(session=test_session)


def test_add_mass_load_success(engine_mass_load, test_session):
    """
    Тест успешного добавления задачи массовой загрузки.
    """
    engine_mass_load.delete_all()

    description = "Задача массовой загрузки 1"
    all_ids = engine_mass_load.get_all_ids()
    _id = random.choice([num for num in range(1, 9999) if num not in all_ids])

    result = engine_mass_load.add_mass_load(
        index=_id,
        description=description
    )

    assert result is True, "Задача не была успешно добавлена"

    time.sleep(0.1)  # Задержка перед проверкой базы данных

    # Проверяем, что задача была добавлена в базу данных
    added_task = test_session.query(MassLoad).filter_by(description=description).first()
    assert added_task is not None, "Добавленная задача не найдена в базе данных"
    assert added_task.description == description, "Описание задачи не совпадает"


# def test_add_mass_load_integrity_error(engine_mass_load, test_session):
#     """
#     Тест на IntegrityError, если задача с таким же описанием уже существует.
#     """
#     description = "Задача массовой загрузки 1"
#
#     # Добавляем задачу
#     engine_mass_load.add_mass_load(description)
#
#     # Пытаемся добавить задачу с таким же описанием
#     result = engine_mass_load.add_mass_load(description)
#
#     assert result is False, "Задача с таким же описанием была добавлена"
#
#     # Проверяем, что в базе данных только одна задача с этим описанием
#     tasks = test_session.query(MassLoad).filter_by(description=description).all()
#     assert len(tasks) == 1, "В базе данных несколько задач с одинаковым описанием"


# def test_get_all_mass_loads(engine_mass_load, test_session):
#     """
#     Тест получения всех задач массовой загрузки.
#     """
#     # Добавляем несколько задач
#     for i in range(3):
#         engine_mass_load.add_mass_load(f"Задача {i + 1}")
#
#     # Получаем все задачи
#     result = engine_mass_load.get_all_mass_loads()
#     assert len(result) == 3, "Количество задач массовой загрузки неверно"
#     assert all(isinstance(task, MassLoad) for task in result), "Ожидаются объекты MassLoad"


def test_get_mass_load_by_id(engine_mass_load, test_session):
    """
    Тест получения задачи по ID.
    """
    # Добавляем задачу
    description = "Задача для поиска"
    engine_mass_load.add_mass_load(index=random.randint(1, 9999), description=description)

    # Получаем задачу по ID
    task = test_session.query(MassLoad).filter_by(description=description).first()
    result = engine_mass_load.get_mass_load_by_id(task.id)

    assert result is not None, "Задача не найдена по ID"
    assert result.description == description, "Описание задачи не совпадает"


def test_update_mass_load(engine_mass_load, test_session):
    """
    Тест обновления задачи массовой загрузки.
    """
    # Добавляем задачу
    description = "Задача для обновления"
    engine_mass_load.add_mass_load(index=random.randint(1, 9999), description=description)

    # Получаем задачу по ID
    task = test_session.query(MassLoad).filter_by(description=description).first()

    # Обновляем описание задачи
    new_description = "Обновленная задача"
    result = engine_mass_load.update_mass_load(task.id, description=new_description)

    assert result is True, "Задача не была обновлена"

    # Проверяем, что задача обновлена в базе данных
    updated_task = test_session.query(MassLoad).filter_by(id=task.id).first()
    assert updated_task.description == new_description, "Описание задачи не обновилось"


def test_delete_mass_load(engine_mass_load, test_session):
    """
    Тест удаления задачи массовой загрузки.
    """
    # Добавляем задачу
    description = "Задача для удаления"
    engine_mass_load.add_mass_load(index=random.randint(1, 9999), description=description)

    # Получаем задачу по ID
    task = test_session.query(MassLoad).filter_by(description=description).first()

    # Удаляем задачу
    result = engine_mass_load.delete_mass_load(task.id)

    assert result is True, "Задача не была успешно удалена"

    # Проверяем, что задача удалена
    deleted_task = test_session.query(MassLoad).filter_by(id=task.id).first()
    assert deleted_task is None, "Задача всё ещё присутствует в базе данных"

# def test_delete_all_mass_loads(engine_mass_load, test_session):
#     """
#     Тест удаления всех задач массовой загрузки.
#     """
#     # Добавляем несколько задач
#     for i in range(3):
#         engine_mass_load.add_mass_load(f"Задача {i + 1}")
#
#     # Удаляем все задачи
#     result = engine_mass_load.delete_all_mass_loads()
#
#     assert result is True, "Не удалось удалить все задачи"
#
#     # Проверяем, что задачи удалены
#     all_tasks = test_session.query(MassLoad).all()
#     assert len(all_tasks) == 0, "Не все задачи были удалены"


# def test_count_mass_loads(engine_mass_load, test_session):
#     """
#     Тест подсчёта количества задач массовой загрузки.
#     """
#     # Добавляем несколько задач
#     for i in range(3):
#         engine_mass_load.add_mass_load(f"Задача {i + 1}")
#
#     # Проверяем количество задач
#     result = engine_mass_load.count()
#     assert result == 3, f"Ожидалось 3 задачи, но найдено {result}"
