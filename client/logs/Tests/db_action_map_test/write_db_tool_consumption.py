import pytest
from unittest.mock import MagicMock
from EventsSystem.action_db import ActionMapper

@pytest.fixture
def mapper():
    mapper = ActionMapper()
    mapper.e_cell.get_cells_by_tool = MagicMock(return_value=MagicMock(id=1))
    mapper.e_cell.delete = MagicMock(return_value=True)
    mapper.e_status.find_by_name = MagicMock(return_value=MagicMock(id=1))
    mapper.e_consumption.add_consumption = MagicMock(return_value=1)
    mapper.e_consumption.get_all_ids = MagicMock(return_value=[1, 2, 3])
    mapper.e_history.add_history = MagicMock(return_value=1)
    mapper.e_history.get_all_ids = MagicMock(return_value=[1, 2, 3])
    mapper.e_operations_consumption.add_operation = MagicMock(return_value=1)
    mapper.e_user.get_user_by_id = MagicMock(return_value=MagicMock(Role_id=1))
    return mapper


def test_write_db_tool_consumption_success(mapper):
    """
    Тест успешного выполнения функции write_db_tool_consumption.
    """
    # Выполняем действие
    result = mapper.write_db_tool_consumption(user_id=1, tool_id=1)

    # Проверяем результат
    assert result is True

    # Проверяем вызовы методов
    mapper.e_cell.get_cells_by_tool.assert_called_once_with(1)
    mapper.e_cell.delete.assert_called_once_with(1)
    mapper.e_status.find_by_name.assert_called_once_with("consumption")
    mapper.e_consumption.add_consumption.assert_called_once()
    mapper.e_history.add_history.assert_called_once()
    mapper.e_operations_consumption.add_operation.assert_called_once()


def test_write_db_tool_consumption_tool_not_found(mapper):
    """
    Тест: инструмент не найден в ячейке.
    """
    mapper.e_cell.get_cells_by_tool.return_value = None

    # Выполняем действие
    result = mapper.write_db_tool_consumption(user_id=1, tool_id=1)

    # Проверяем результат
    assert result is False
    mapper.e_cell.get_cells_by_tool.assert_called_once_with(1)
    mapper.e_cell.delete.assert_not_called()


def test_write_db_tool_consumption_status_not_found(mapper):
    """
    Тест: статус 'consumption' не найден.
    """
    mapper.e_status.find_by_name.return_value = None

    # Выполняем действие
    result = mapper.write_db_tool_consumption(user_id=1, tool_id=1)

    # Проверяем результат
    assert result is False
    mapper.e_status.find_by_name.assert_called_once_with("consumption")
    mapper.e_consumption.add_consumption.assert_not_called()


def test_write_db_tool_consumption_add_consumption_failed(mapper):
    """
    Тест: ошибка при добавлении записи в таблицу Consumption.
    """
    mapper.e_consumption.add_consumption.return_value = None

    # Выполняем действие
    result = mapper.write_db_tool_consumption(user_id=1, tool_id=1)

    # Проверяем результат
    assert result is False
    mapper.e_consumption.add_consumption.assert_called_once()
    mapper.e_history.add_history.assert_not_called()


def test_write_db_tool_consumption_exception(mapper):
    """
    Тест: исключение во время выполнения функции.
    """
    mapper.e_cell.get_cells_by_tool.side_effect = Exception("Test exception")

    # Выполняем действие
    result = mapper.write_db_tool_consumption(user_id=1, tool_id=1)

    # Проверяем результат
    assert result is False
