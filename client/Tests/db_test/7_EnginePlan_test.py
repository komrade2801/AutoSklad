import random

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Models.Plan import Plan
from DB.Engine.PlanCRUD import EnginePlan
from DB.Data.db import SessionLocal
from DB.Data.db import engine


# Фикстура для создания тестовой базы данных
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
    # Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    # session = Session()
    #
    # # Создаем все необходимые таблицы
    # Plan.metadata.create_all(bind=test_engine)
    return SessionLocal(test_engine)


# Фикстура для экземпляра EnginePlan
@pytest.fixture
def engine_plan(test_session):
    """
    Создает экземпляр EnginePlan с тестовой сессией.
    """
    return EnginePlan(session=test_session)


def test_add_plan_success(engine_plan, test_session):
    """
    Тест успешного добавления чертежа.
    """
    engine_plan.delete_all()

    result = engine_plan.add_plan(
        enterprise="TestEnterprise",
        barcode="1234567890123",
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        list_id=1,
        list_count=5
    )

    assert result is True, "Чертеж не был добавлен"

    # Проверяем, что чертеж добавлен в базу данных
    added_plan = test_session.query(Plan).filter_by(barcode="1234567890123").first()
    assert added_plan is not None, "Добавленный чертеж не найден в базе данных"
    assert added_plan.name == "Test Plan"
    assert added_plan.enterprise == "TestEnterprise"
    # Удаляем чертеж
    result = engine_plan.delete_plan(added_plan.id)
    assert result is True, "Чертеж не был успешно удален"


def test_get_plan_by_barcode(engine_plan, test_session):
    """
    Тест получения чертежа по штрих-коду.
    """
    # Добавляем чертеж
    plan = Plan(
        id=random.randint(1, 9999),
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111,999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    test_session.add(plan)
    test_session.commit()

    # Проверяем получение чертежа по штрих-коду
    result = engine_plan.get_plan_by_barcode(plan.barcode)
    assert result is not None, "Чертеж по штрих-коду не найден"
    assert result.name == "Test Plan"
    # Удаляем чертеж
    result = engine_plan.delete_plan(result.id)
    assert result is True, "Чертеж не был успешно удален"


# def test_get_plans_by_enterprise(engine_plan, test_session):
#     """
#     Тест получения всех чертежей по названию предприятия.
#     """
#     result = engine_plan.get_plans_by_enterprise("TestEnterprise")
#     count_old = len(result)
#
#     step = 3
#     # Добавляем несколько чертежей
#     for i in range(step):
#         plan = Plan(
#             enterprise="TestEnterprise",
#             barcode=f"1234567890{i}",
#             name=f"Test Plan {i}",
#             description="Test Description",
#             designation="Design 1",
#             index_list=1,
#             list_count=5
#         )
#         test_session.add(plan)
#     test_session.commit()
#
#     # Получаем все чертежи по предприятию
#     results = engine_plan.get_plans_by_enterprise("TestEnterprise")
#     assert len(results) == count_old+2, "Количество чертежей по предприятию не совпадает"
#     assert all(plan.enterprise == "TestEnterprise" for plan in results)
#     for result in results:
#         # Удаляем чертеж
#         result = engine_plan.delete_plan(result.id)
#         assert result is True, "Чертеж не был успешно удален"


def test_update_plan_success(engine_plan, test_session):
    """
    Тест успешного обновления чертежа.
    """
    # Добавляем чертеж
    plan = Plan(
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111,999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    test_session.add(plan)
    test_session.commit()

    # Обновляем данные чертежа
    result = engine_plan.update_plan(plan.id, name="Updated Plan name", description="Updated Description")
    assert result is True, "Чертеж не был обновлен"

    # Проверяем, что чертеж обновлен
    updated_plan = test_session.query(Plan).filter_by(id=plan.id).first()
    assert updated_plan.name == "Updated Plan name"
    assert updated_plan.description == "Updated Description"


def test_delete_plan_success(engine_plan, test_session):
    """
    Тест успешного удаления чертежа.
    """
    # Добавляем чертеж
    plan_to_delete = Plan(
        enterprise="TestEnterprise",
        barcode="1234567890123",
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    test_session.add(plan_to_delete)
    test_session.commit()

    # Удаляем чертеж
    result = engine_plan.delete_plan(plan_to_delete.id)
    assert result is True, "Чертеж не был успешно удален"

    # Проверяем, что чертеж удален
    deleted_plan = test_session.query(Plan).filter_by(id=plan_to_delete.id).first()
    assert deleted_plan is None, "Удалённый чертеж всё ещё присутствует в базе данных"


def test_get_hierarchy(engine_plan, test_session):
    """
    Тест получения иерархии чертежей.
    """
    # Добавляем родительский чертеж
    parent_plan = Plan(
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111,999999999999)),
        name="Parent Plan",
        description="Parent Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    test_session.add(parent_plan)
    test_session.commit()

    # Добавляем дочерний чертеж
    child_plan = Plan(
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111,999999999999)),
        name="Child Plan",
        description="Child Description",
        designation="Design 2",
        index_list=1,
        list_count=3,
        parent_plan_id=parent_plan.id
    )
    test_session.add(child_plan)
    test_session.commit()

    # Получаем иерархию для родительского чертежа
    result = engine_plan.get_hierarchy(parent_plan.id)
    assert len(result) == 2, "Неверное количество чертежей в иерархии"
    assert result[0].name == "Parent Plan"
    assert result[1].name == "Child Plan"


# def test_get_plan_with_relations(engine_plan, test_session):
#     """
#     Тест получения чертежа с связанными объектами.
#     """
#     # Добавляем чертеж с дополнительными связанными объектами
#     plan = Plan(
#         enterprise="TestEnterprise",
#         barcode="1234567890123",
#         name="Test Plan with Relations",
#         description="Test Description",
#         designation="Design 1",
#         index_list=1,
#         list_count=5
#     )
#     test_session.add(plan)
#     test_session.commit()
#
#     # Получаем чертеж с связанными объектами
#     result = engine_plan.get_plan_with_relations(plan.id)
#     assert result is not None, "Чертеж с связанными объектами не найден"
#     assert result.name == "Test Plan with Relations"


def test_get_all_plans(engine_plan, test_session):
    """
    Тест получения всех чертежей.
    """
    # Добавляем несколько чертежей
    for i in range(2):
        plan = Plan(
            enterprise="TestEnterprise",
            barcode=str(random.randint(111111111111, 999999999999)),
            name=f"Test Plan {i}",
            description="Test Description",
            designation="Design 1",
            index_list=1,
            list_count=5
        )
        test_session.add(plan)
    test_session.commit()

    # Получаем все чертежи
    result = engine_plan.get_all_plans()
    assert len(result) > 0, "Количество чертежей в базе данных не совпадает"
