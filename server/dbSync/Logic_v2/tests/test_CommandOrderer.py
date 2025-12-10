"""
Unit-тесты для CommandOrderer.

Покрытие:
- Группировка команд по записям
- Сжатие последовательностей (compression)
- Валидация операций
- Топологическая сортировка
- Проверка FK зависимостей

Автор: AI Assistant
Дата: 9 декабря 2025
"""

import unittest
import sys
from pathlib import Path

# Добавляем путь к родительской директории для импорта
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dbSync.Logic_v2.CommandOrderer import CommandOrderer


class TestCommandOrderer(unittest.TestCase):
    """Тесты для CommandOrderer"""
    
    def setUp(self):
        """Создание экземпляра CommandOrderer перед каждым тестом"""
        self.orderer = CommandOrderer()
    
    def test_empty_commands(self):
        """Тест: пустой список команд"""
        commands = []
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        self.assertEqual(len(ordered), 0)
        self.assertEqual(len(warnings), 0)
    
    def test_single_command(self):
        """Тест: одна команда проходит без изменений"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "Tool"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0]["operation"], "ADD")
    
    def test_compression_add_update_delete(self):
        """Тест: ADD + UPDATE + DELETE → DELETE"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # После оптимизации должна остаться только DELETE
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0]["operation"], "DELETE")
        self.assertEqual(ordered[0]["data"]["id"], 1)
    
    def test_compression_add_update(self):
        """Тест: ADD + UPDATE → ADD с объединёнными данными"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A", "count": 5}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Должна остаться только ADD с объединёнными данными
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0]["operation"], "ADD")
        self.assertEqual(ordered[0]["data"]["name"], "B")  # Обновлённое имя
        self.assertEqual(ordered[0]["data"]["count"], 5)  # Оригинальный count
    
    def test_compression_multiple_updates(self):
        """Тест: Множественные UPDATE → один UPDATE"""
        commands = [
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "count": 10}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "description": "Desc"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Должен остаться один UPDATE с объединёнными данными
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0]["operation"], "UPDATE")
        self.assertIn("name", ordered[0]["data"])
        self.assertIn("count", ordered[0]["data"])
        self.assertIn("description", ordered[0]["data"])
    
    def test_compression_multiple_adds(self):
        """Тест: Множественные ADD → последний ADD"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "B"}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "C"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Должен остаться только последний ADD
        self.assertEqual(len(ordered), 1)
        self.assertEqual(ordered[0]["data"]["name"], "C")
        self.assertGreater(len(warnings), 0)  # Должно быть предупреждение
    
    def test_resurrection_delete_add(self):
        """Тест: DELETE + ADD → оба сохраняются (воскрешение)"""
        commands = [
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "New"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Оба должны сохраниться (удаление старой + создание новой)
        self.assertEqual(len(ordered), 2)
        self.assertEqual(ordered[0]["operation"], "DELETE")
        self.assertEqual(ordered[1]["operation"], "ADD")
        self.assertGreater(len(warnings), 0)  # Предупреждение о воскрешении
    
    def test_validation_update_without_add(self):
        """Тест: UPDATE без ADD → предупреждение"""
        commands = [
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        self.assertEqual(len(ordered), 1)
        self.assertGreater(len(warnings), 0)
        self.assertIn("without preceding ADD", warnings[0])
    
    def test_validation_delete_without_add(self):
        """Тест: DELETE без ADD → предупреждение"""
        commands = [
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        self.assertEqual(len(ordered), 1)
        self.assertGreater(len(warnings), 0)
        self.assertIn("without preceding ADD", warnings[0])
    
    def test_topological_sort_by_table(self):
        """Тест: Сортировка по приоритету таблиц"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "Tool"}},
            {"operation": "ADD", "table": "Group", "data": {"id": 1, "name": "Group"}},
            {"operation": "ADD", "table": "Status", "data": {"id": 1, "stype": "Active"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Порядок: Status (0) → Group (10) → ToolTypes (20)
        self.assertEqual(ordered[0]["table"], "Status")
        self.assertEqual(ordered[1]["table"], "Group")
        self.assertEqual(ordered[2]["table"], "ToolTypes")
    
    def test_topological_sort_by_operation(self):
        """Тест: Сортировка по приоритету операций"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 2}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 3, "name": "B"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Порядок операций: DELETE → UPDATE → ADD
        self.assertEqual(ordered[0]["operation"], "DELETE")
        self.assertEqual(ordered[1]["operation"], "UPDATE")
        self.assertEqual(ordered[2]["operation"], "ADD")
    
    def test_fk_check_group_tooltype(self):
        """Тест: Проверка FK Group → ToolTypes"""
        commands = [
            {"operation": "DELETE", "table": "Group", "data": {"id": 1}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "Tool", "groups_id": 1}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Должно быть предупреждение о FK violation
        self.assertGreater(len(warnings), 0)
        fk_warning = [w for w in warnings if "FK violation" in w or "deleted in this batch" in w]
        self.assertGreater(len(fk_warning), 0)
    
    def test_multiple_records(self):
        """Тест: Несколько записей обрабатываются независимо"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 2, "name": "C"}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 3}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # ID=1: ADD+UPDATE → ADD
        # ID=2: ADD → ADD
        # ID=3: DELETE → DELETE
        # Итого: 3 команды
        self.assertEqual(len(ordered), 3)
    
    def test_complex_scenario(self):
        """Тест: Сложный сценарий из документации (инцидент)"""
        commands = [
            {"operation": "ADD", "table": "Group", "data": {"id": 2, "name": "Group2"}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "123", "groups_id": 2}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "2"}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # После оптимизации:
        # - ToolTypes: ADD+UPDATE+DELETE → DELETE
        # - Group: ADD → ADD
        # Итого: 2 команды (DELETE ToolTypes, ADD Group)
        # Порядок: DELETE идёт первым (освобождает FK)
        
        self.assertEqual(len(ordered), 2)
        
        # Находим DELETE ToolTypes и ADD Group
        delete_cmd = [c for c in ordered if c["operation"] == "DELETE"][0]
        add_cmd = [c for c in ordered if c["operation"] == "ADD"][0]
        
        self.assertEqual(delete_cmd["table"], "ToolTypes")
        self.assertEqual(add_cmd["table"], "Group")
    
    def test_stats(self):
        """Тест: Статистика работы CommandOrderer"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}}
        ]
        
        self.orderer.reset_stats()
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        stats = self.orderer.get_stats()
        
        self.assertEqual(stats["total_processed"], 3)
        self.assertEqual(stats["total_compressed"], 2)  # 3 → 1 команда
        self.assertGreater(stats["compression_ratio"], 0)
    
    def test_bulk_operations_without_id(self):
        """Тест: Команды без ID обрабатываются отдельно"""
        commands = [
            {"operation": "ADD", "table": "History", "data": {"description": "Action 1"}},
            {"operation": "ADD", "table": "History", "data": {"description": "Action 2"}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Обе команды должны сохраниться (разные bulk операции)
        self.assertEqual(len(ordered), 2)


class TestCommandOrdererIntegration(unittest.TestCase):
    """Интеграционные тесты CommandOrderer"""
    
    def setUp(self):
        self.orderer = CommandOrderer()
    
    def test_real_world_scenario_1(self):
        """Реальный сценарий: создание группы с инструментами"""
        commands = [
            {"operation": "ADD", "table": "Group", "data": {"id": 1, "name": "Инструменты"}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "Отвёртка", "groups_id": 1}},
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 2, "name": "Молоток", "groups_id": 1}},
            {"operation": "ADD", "table": "Cell", "data": {"id": 1, "tools_id": 1, "number": 101}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # Порядок: Group → ToolTypes → Cell (по FK зависимостям)
        self.assertEqual(len(ordered), 4)
        self.assertEqual(ordered[0]["table"], "Group")
        self.assertEqual(ordered[3]["table"], "Cell")
    
    def test_real_world_scenario_2(self):
        """Реальный сценарий: каскадное удаление"""
        commands = [
            {"operation": "DELETE", "table": "Cell", "data": {"id": 1}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 2}},
            {"operation": "DELETE", "table": "Group", "data": {"id": 1}}
        ]
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        # DELETE должны идти в обратном порядке FK:
        # Cell → ToolTypes → Group
        self.assertEqual(len(ordered), 4)
        
        # Cell должна быть первой (самый высокий приоритет при DELETE)
        cell_idx = next(i for i, c in enumerate(ordered) if c["table"] == "Cell")
        group_idx = next(i for i, c in enumerate(ordered) if c["table"] == "Group")
        
        self.assertLess(cell_idx, group_idx, "Cell должна удаляться до Group")


if __name__ == "__main__":
    unittest.main()

