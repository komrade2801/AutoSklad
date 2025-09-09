import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from DB.Engine.HelpCRUD import EngineHelp
from DB.Models.Help import Help
from DB.Data.db import SessionLocal
from DB.Data.db import engine


# Фикстура для настройки тестовой базы данных
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
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineHelp
@pytest.fixture
def engine_help(test_session):
    """
    Создает экземпляр EngineHelp с тестовой сессией.
    """
    return EngineHelp(session=test_session)


def test_add_help_entry_success(engine_help, test_session):
    """
    Тест успешного добавления записи в таблицу Help.
    """
    engine_help.delete_all()
    text = "Это текст справочной записи"
    data = datetime.utcnow()

    # Добавляем запись
    result = engine_help.add_help_entry(text=text, data=data)
    assert result is True, "Запись не была добавлена"

    # Проверяем, что запись добавлена в базу данных
    added_help = test_session.query(Help).filter_by(text=text, data=data).first()
    assert added_help is not None, "Добавленная запись не найдена в базе данных"
    assert added_help.text == text
    assert added_help.data == data
    engine_help.delete(added_help.id)


def test_add_help_entry_without_data(engine_help, test_session):
    """
    Тест добавления записи без указания даты. Дата должна быть текущей.
    """
    text = "Текст без даты"

    # Добавляем запись
    result = engine_help.add_help_entry(text=text)
    assert result is True, "Запись не была добавлена"

    # Проверяем, что дата записи была установлена корректно (текущая дата)
    added_help = test_session.query(Help).filter_by(text=text).first()
    assert added_help is not None, "Добавленная запись не найдена в базе данных"
    assert added_help.text == text
    assert added_help.data is not None, "Дата записи не установлена"
    engine_help.delete(added_help.id)


def test_get_help_by_id_success(engine_help, test_session):
    """
    Тест получения записи по ID.
    """
    text = "Текст для поиска по ID"
    help_entry = Help(text=text, data=datetime.utcnow())
    test_session.add(help_entry)
    test_session.commit()

    # Получаем запись по ID
    result = engine_help.get_help_by_id(help_entry.id)
    assert result is not None, "Запись по ID не найдена"
    assert result.text == text
    engine_help.delete(result.id)


def test_get_help_by_id_not_found(engine_help):
    """
    Тест получения записи по ID, которая не существует.
    """
    result = engine_help.get_help_by_id(9999)  # ID, который точно не существует
    assert result is None, "Запись не должна быть найдена"


def test_update_help_entry_success(engine_help, test_session):
    """
    Тест успешного обновления записи в таблице Help.
    """
    text = "Текст для обновления"
    new_text = "Обновленный текст"
    help_entry = Help(text=text, data=datetime.utcnow())
    test_session.add(help_entry)
    test_session.commit()

    # Обновляем запись
    result = engine_help.update_help_entry(help_entry.id, text=new_text)
    assert result is True, "Запись не была обновлена"

    # Проверяем, что запись обновлена
    updated_help = test_session.query(Help).filter_by(id=help_entry.id).first()
    assert updated_help is not None, "Обновленная запись не найдена"
    assert updated_help.text == new_text
    engine_help.delete(updated_help.id)


def test_update_help_entry_partial_fields(engine_help, test_session):
    """
    Тест частичного обновления записи (обновление только текста).
    """
    text = "Текст для частичного обновления"
    new_data = datetime.utcnow()
    help_entry = Help(text=text, data=datetime.utcnow())
    test_session.add(help_entry)
    test_session.commit()

    # Частичное обновление записи
    result = engine_help.update_help_entry(help_entry.id, data=new_data)
    assert result is True, "Запись не была обновлена"

    # Проверяем, что только дата была обновлена
    updated_help = test_session.query(Help).filter_by(id=help_entry.id).first()
    assert updated_help is not None, "Обновленная запись не найдена"
    assert updated_help.data == new_data
    assert updated_help.text == text  # Текст должен остаться неизменным
    engine_help.delete(updated_help.id)


def test_delete_help_entry_success(engine_help, test_session):
    """
    Тест успешного удаления записи.
    """
    text = "Текст для удаления"
    help_entry = Help(text=text, data=datetime.utcnow())
    test_session.add(help_entry)
    test_session.commit()

    # Удаляем запись
    result = engine_help.delete_help_entry(help_entry.id)
    assert result is True, "Запись не была удалена"

    # Проверяем, что запись удалена
    deleted_help = test_session.query(Help).filter_by(id=help_entry.id).first()
    assert deleted_help is None, "Удаленная запись всё ещё присутствует в базе данных"


def test_get_all_help_entries(engine_help, test_session):
    """
    Тест получения всех записей из таблицы Help.
    """
    # Удаляем все существующие записи
    test_session.query(Help).delete()
    test_session.commit()

    # Добавляем несколько записей
    for i in range(5):
        help_entry = Help(text=f"Текст справочной записи {i}", data=datetime.utcnow())
        test_session.add(help_entry)
    test_session.commit()

    # Получаем все записи
    result = engine_help.get_all_help_entries()
    assert len(result) == 5, "Количество всех записей неверно"
    assert all(isinstance(entry, Help) for entry in result), "Все элементы не являются записями Help"
    test_session.query(Help).delete()


# def test_add_help_entry_integrity_error(engine_help, test_session):
#     """
#     Тест обработки ошибки при добавлении записи с нарушением уникальности.
#     """
#     text = "Текст с уникальной ошибкой"
#     help_entry = Help(text=text, data=datetime.utcnow())
#     test_session.add(help_entry)
#     test_session.commit()
#
#     # Попытка добавить дублирующую запись
#     with pytest.raises(IntegrityError):
#         duplicate_entry = Help(text=text, data=datetime.utcnow())
#         test_session.add(duplicate_entry)
#         test_session.commit()

