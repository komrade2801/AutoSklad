import pytest
from unittest.mock import MagicMock
from faker import Faker
from EventsSystem.action_db import ActionMapper


@pytest.fixture
def fake_data():
    fake = Faker()
    return fake


@pytest.fixture
def mapper():
    # Создаём объект `ActionMapper` и замокаем методы движков
    mapper = ActionMapper()
    mapper.e_plan.add_plan = MagicMock(return_value=True)
    mapper.e_plan.update_plan = MagicMock(return_value=True)
    mapper.e_plan.get_plan_by_barcode = MagicMock(side_effect=lambda barcode: None)
    return mapper


@pytest.fixture
def fake_plan_data(fake_data):
    return [
        {
            'enterprise': fake_data.company(),
            'barcode': fake_data.ean(length=8),
            'name': fake_data.word(),
            'description': fake_data.sentence(),
            'designation': fake_data.word(),
            'list_id': 1,
            'list_count': fake_data.random_int(min=1, max=10),
            'parent_plan_id': None
        }
    ]


def test_execute_write_db_plans_success(mapper, fake_plan_data):
    """
    Тест успешного добавления новых чертежей через execute.
    """
    # Выполнение действия
    result = mapper.execute('write_db_plans', fake_plan_data)

    # Проверка результата
    assert result is True

    # Проверка вызовов методов
    for plan in fake_plan_data:
        mapper.e_plan.add_plan.assert_any_call(
            enterprise=plan['enterprise'],
            barcode=plan['barcode'],
            name=plan['name'],
            description=plan['description'],
            designation=plan['designation'],
            list_id=plan['list_id'],
            list_count=plan['list_count'],
            parent_plan_id=plan['parent_plan_id']
        )


def test_execute_write_db_plans_existing(mapper, fake_plan_data):
    """
    Тест успешного обновления существующих чертежей через execute.
    """
    # Настройка возврата существующего плана
    existing_plan = MagicMock(id=1)
    mapper.e_plan.get_plan_by_barcode.side_effect = lambda barcode: existing_plan if barcode == fake_plan_data[0]['barcode'] else None

    # Выполнение действия
    result = mapper.execute('write_db_plans', fake_plan_data)

    # Проверка результата
    assert result is True

    # Проверка вызовов методов
    mapper.e_plan.update_plan.assert_called_once_with(
        existing_plan.id,
        **fake_plan_data[0]
    )
    mapper.e_plan.add_plan.assert_not_called()


def test_execute_write_db_plans_error(mapper, fake_plan_data):
    """
    Тест ошибки при добавлении нового чертежа через execute.
    """
    # Настройка возврата ошибки при добавлении
    mapper.e_plan.add_plan.return_value = False

    # Выполнение действия
    result = mapper.execute('write_db_plans', fake_plan_data)

    # Проверка результата
    assert result is False


def test_execute_write_db_plans_update_error(mapper, fake_plan_data):
    """
    Тест ошибки при обновлении существующего чертежа через execute.
    """
    # Настройка возврата существующего плана
    existing_plan = MagicMock(id=1)
    mapper.e_plan.get_plan_by_barcode.side_effect = lambda barcode: existing_plan if barcode == fake_plan_data[0]['barcode'] else None

    # Настройка ошибки обновления
    mapper.e_plan.update_plan.return_value = False

    # Выполнение действия
    result = mapper.execute('write_db_plans', fake_plan_data)

    # Проверка результата
    assert result is False
