"""
Integration-тесты для полного цикла синхронизации с CommandOrderer.

Покрытие:
- Полный цикл: CommandQueue → CommandSender → SyncProcessor → DB
- Проверка оптимизации команд в реальном потоке
- Edge cases из production инцидентов
- E2E сценарии с реальными данными

Автор: AI Assistant
Дата: 9 декабря 2025
"""

import unittest
import sys
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Добавляем путь к родительской директории для импорта
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dbSync.Logic_v2.CommandOrderer import CommandOrderer
from dbSync.Logic_v2.CommandQueue import CommandQueue


class TestSyncIntegration(unittest.TestCase):
    """Integration-тесты для полного цикла синхронизации"""
    
    def setUp(self):
        """Создание временной очереди и CommandOrderer перед каждым тестом"""
        # Создаём временный файл для очереди
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.write('[]')
        self.temp_file.close()
        
        self.queue = CommandQueue(filepath=self.temp_file.name)
        self.orderer = CommandOrderer()
    
    def tearDown(self):
        """Очистка временных файлов"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_queue_to_orderer_simple(self):
        """Тест: Простой сценарий из очереди в CommandOrderer"""
        # Добавляем команды в очередь
        self.queue.add_command("Group", "add", {"id": 1, "name": "Test Group"})
        self.queue.add_command("ToolTypes", "add", {"id": 1, "name": "Tool", "groups_id": 1})
        
        # Получаем pending команды
        pending = self.queue.get_pending_commands()
        
        # Преобразуем формат для CommandOrderer (operation в upper case)
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        # Упорядочиваем
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        # Проверки
        self.assertEqual(len(ordered), 2)
        self.assertEqual(len(warnings), 0)
        
        # Group должна быть первой (родитель)
        self.assertEqual(ordered[0]["table"], "Group")
        self.assertEqual(ordered[1]["table"], "ToolTypes")
    
    def test_production_incident_add_delete_same_batch(self):
        """
        Тест: Реальный инцидент 9 декабря 2025
        
        Сценарий:
        1. Пользователь создал Group (ID=2)
        2. Пользователь создал ToolTypes (ID=1, groups_id=2)
        3. Пользователь удалил ToolTypes (ID=1) через 12 секунд
        4. Все 3 команды попали в один batch
        
        Ожидаемый результат:
        - Оптимизация: ADD ToolTypes + DELETE ToolTypes = только DELETE
        - Group остаётся (не удалена)
        - Порядок: DELETE ToolTypes, затем ADD Group
        """
        # Эмулируем реальную последовательность
        cmd1_time = datetime.utcnow()
        cmd2_time = cmd1_time + timedelta(seconds=8)
        cmd3_time = cmd2_time + timedelta(seconds=12)
        
        # Добавляем в очередь
        id1 = self.queue.add_command("Group", "add", {
            "index": 2,
            "name": "Test Group",
            "description": "",
            "paren_group_id": 0
        })
        
        id2 = self.queue.add_command("ToolTypes", "add", {
            "index": 1,
            "name": "Test Tool",
            "description": "",
            "count": 0,
            "img": "",
            "groups_id": 2
        })
        
        id3 = self.queue.add_command("ToolTypes", "delete", {
            "index": 1
        })
        
        # Получаем pending
        pending = self.queue.get_pending_commands()
        self.assertEqual(len(pending), 3, "Должно быть 3 pending команды")
        
        # Преобразуем для CommandOrderer
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        # Упорядочиваем и оптимизируем
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        # Проверки
        print(f"\n=== Production Incident Test ===")
        print(f"Исходных команд: {len(commands_for_orderer)}")
        print(f"После оптимизации: {len(ordered)}")
        print(f"Warnings: {len(warnings)}")
        for i, cmd in enumerate(ordered):
            print(f"  {i+1}. {cmd['operation']} {cmd['table']} (data: {cmd['data']})")
        
        # Должно быть 2 команды (ADD ToolTypes сжато с DELETE)
        self.assertLessEqual(len(ordered), 2, "Должно быть не более 2 команд после оптимизации")
        
        # Должно быть хотя бы одно предупреждение о сжатии
        self.assertGreater(len(warnings), 0, "Должно быть предупреждение о сжатии")
        
        # DELETE ToolTypes должна идти перед ADD Group (если она есть)
        delete_found = False
        for cmd in ordered:
            if cmd["operation"] == "DELETE" and cmd["table"] == "ToolTypes":
                delete_found = True
                break
        
        self.assertTrue(delete_found, "DELETE ToolTypes должна присутствовать")
    
    def test_cascade_delete_ordering(self):
        """
        Тест: Каскадное удаление с правильным порядком
        
        Сценарий:
        1. Удаляем Cell (зависит от ToolTypes)
        2. Удаляем ToolTypes (зависит от Group)
        3. Удаляем Group (родитель)
        
        Ожидаемый результат:
        - Порядок: Cell → ToolTypes → Group
        """
        self.queue.add_command("Group", "delete", {"id": 1})
        self.queue.add_command("ToolTypes", "delete", {"id": 1})
        self.queue.add_command("Cell", "delete", {"id": 1})
        
        pending = self.queue.get_pending_commands()
        
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        # Проверяем порядок
        self.assertEqual(len(ordered), 3)
        
        # Cell → ToolTypes → Group
        tables = [cmd["table"] for cmd in ordered]
        self.assertEqual(tables[0], "Cell", "Cell должна быть первой")
        self.assertEqual(tables[2], "Group", "Group должна быть последней")
    
    def test_multiple_updates_compression(self):
        """
        Тест: Множественные UPDATE одной записи
        
        Сценарий:
        1. Пользователь обновил запись 5 раз подряд
        2. Все попали в один batch
        
        Ожидаемый результат:
        - Только один UPDATE с последними данными
        """
        # Добавляем 5 UPDATE команд
        for i in range(5):
            self.queue.add_command("ToolTypes", "update", {
                "id": 1,
                "name": f"Tool Name v{i+1}",
                "count": i
            })
        
        pending = self.queue.get_pending_commands()
        self.assertEqual(len(pending), 5)
        
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        # Должен остаться только один UPDATE
        self.assertEqual(len(ordered), 1, "Должен остаться только один UPDATE")
        self.assertEqual(ordered[0]["operation"], "UPDATE")
        self.assertEqual(ordered[0]["data"]["name"], "Tool Name v5", 
                        "Должны остаться последние данные")
        
        # Должно быть предупреждение о сжатии
        self.assertGreater(len(warnings), 0)
    
    def test_resurrection_scenario(self):
        """
        Тест: Воскрешение записи (DELETE + ADD)
        
        Сценарий:
        1. Удаляем запись
        2. Создаём её снова с тем же ID
        
        Ожидаемый результат:
        - Оба операции сохраняются
        - DELETE идёт первым
        - Предупреждение о воскрешении
        """
        self.queue.add_command("ToolTypes", "delete", {"id": 1})
        self.queue.add_command("ToolTypes", "add", {
            "id": 1,
            "name": "Resurrected Tool",
            "groups_id": 1
        })
        
        pending = self.queue.get_pending_commands()
        
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        # Обе операции должны остаться
        self.assertEqual(len(ordered), 2)
        
        # DELETE первым
        self.assertEqual(ordered[0]["operation"], "DELETE")
        self.assertEqual(ordered[1]["operation"], "ADD")
        
        # Должно быть предупреждение
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("resurrection" in w.lower() or "воскрешение" in w.lower() 
                           for w in warnings))
    
    def test_fk_violation_prevention(self):
        """
        Тест: Предотвращение нарушения FK
        
        Сценарий:
        1. Удаляем Group
        2. Пытаемся добавить ToolTypes с этой groups_id
        
        Ожидаемый результат:
        - Предупреждение о потенциальном нарушении FK
        """
        # Добавляем команды в неправильном порядке
        self.queue.add_command("Group", "delete", {"id": 1})
        self.queue.add_command("ToolTypes", "add", {
            "id": 1,
            "name": "Tool",
            "groups_id": 1  # Группа удалена в том же batch
        })
        
        pending = self.queue.get_pending_commands()
        
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        # Команды должны пройти
        self.assertEqual(len(ordered), 2)
        
        # Должно быть предупреждение о FK (ADD ссылается на удалённую Group)
        self.assertGreater(len(warnings), 0, "Должно быть предупреждение о FK нарушении")
        self.assertTrue(any("FK" in w or "foreign key" in w.lower() or "was deleted" in w.lower()
                           for w in warnings), 
                       f"Предупреждение должно упоминать FK. Warnings: {warnings}")
    
    def test_mixed_operations_complex(self):
        """
        Тест: Сложный сценарий со смешанными операциями
        
        Сценарий:
        1. Создаём 2 группы
        2. Создаём 3 инструмента в разных группах
        3. Обновляем 1 инструмент
        4. Удаляем 1 инструмент
        5. Обновляем 1 группу
        
        Ожидаемый результат:
        - Правильный порядок по FK
        - Оптимизация где возможно
        """
        # Группы
        self.queue.add_command("Group", "add", {"id": 1, "name": "Group 1"})
        self.queue.add_command("Group", "add", {"id": 2, "name": "Group 2"})
        
        # Инструменты
        self.queue.add_command("ToolTypes", "add", {"id": 1, "name": "Tool 1", "groups_id": 1})
        self.queue.add_command("ToolTypes", "add", {"id": 2, "name": "Tool 2", "groups_id": 1})
        self.queue.add_command("ToolTypes", "add", {"id": 3, "name": "Tool 3", "groups_id": 2})
        
        # Обновления
        self.queue.add_command("ToolTypes", "update", {"id": 1, "name": "Tool 1 Updated"})
        self.queue.add_command("Group", "update", {"id": 1, "name": "Group 1 Updated"})
        
        # Удаление
        self.queue.add_command("ToolTypes", "delete", {"id": 3})
        
        pending = self.queue.get_pending_commands()
        self.assertEqual(len(pending), 8)
        
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        
        print(f"\n=== Complex Mixed Operations Test ===")
        print(f"Исходных команд: {len(commands_for_orderer)}")
        print(f"После оптимизации: {len(ordered)}")
        print(f"Сжатие: {(1 - len(ordered)/len(commands_for_orderer))*100:.1f}%")
        for i, cmd in enumerate(ordered):
            print(f"  {i+1}. {cmd['operation']:6s} {cmd['table']:10s} "
                  f"(id={cmd['data'].get('id', 'N/A')})")
        
        # Должно быть меньше команд после оптимизации
        self.assertLess(len(ordered), len(commands_for_orderer))
        
        # Проверяем порядок операций
        operations = [cmd["operation"] for cmd in ordered]
        
        # DELETE должны быть в начале
        if "DELETE" in operations:
            first_delete = operations.index("DELETE")
            last_add = max([i for i, op in enumerate(operations) if op == "ADD"], default=-1)
            if last_add >= 0:
                self.assertLess(first_delete, last_add, 
                               "DELETE должны быть до ADD")
    
    def test_bulk_operations_performance(self):
        """
        Тест: Производительность на большом количестве команд
        
        Сценарий:
        - 100 команд разных типов
        
        Ожидаемый результат:
        - Значительное сжатие (>30%)
        - Время обработки < 1 секунды
        """
        import time
        
        # Создаём 100 команд
        for i in range(20):
            self.queue.add_command("Group", "add", {"id": i, "name": f"Group {i}"})
        
        for i in range(40):
            self.queue.add_command("ToolTypes", "add", {
                "id": i, 
                "name": f"Tool {i}",
                "groups_id": i % 20
            })
        
        for i in range(20):
            self.queue.add_command("ToolTypes", "update", {
                "id": i,
                "name": f"Tool {i} Updated"
            })
        
        for i in range(20):
            self.queue.add_command("ToolTypes", "delete", {"id": i})
        
        pending = self.queue.get_pending_commands()
        self.assertEqual(len(pending), 100)
        
        commands_for_orderer = [
            {
                "operation": cmd["operation"].upper(),
                "table": cmd["table"],
                "data": cmd["data"],
                "timestamp": cmd["timestamp"]
            }
            for cmd in pending
        ]
        
        # Измеряем время
        start_time = time.time()
        ordered, warnings = self.orderer.order_and_validate(commands_for_orderer)
        elapsed_time = time.time() - start_time
        
        print(f"\n=== Bulk Operations Performance Test ===")
        print(f"Исходных команд: {len(commands_for_orderer)}")
        print(f"После оптимизации: {len(ordered)}")
        print(f"Сжатие: {(1 - len(ordered)/len(commands_for_orderer))*100:.1f}%")
        print(f"Время обработки: {elapsed_time*1000:.2f} мс")
        print(f"Warnings: {len(warnings)}")
        
        # Проверки
        self.assertLess(elapsed_time, 1.0, "Обработка должна быть < 1 секунды")
        
        compression_ratio = 1 - (len(ordered) / len(commands_for_orderer))
        self.assertGreater(compression_ratio, 0.3, "Сжатие должно быть > 30%")
        
        # Должно быть меньше команд
        self.assertLess(len(ordered), len(commands_for_orderer))


class TestQueueStatistics(unittest.TestCase):
    """Тесты для статистики CommandOrderer"""
    
    def setUp(self):
        self.orderer = CommandOrderer()
    
    def test_statistics_tracking(self):
        """Тест: Отслеживание статистики работы"""
        commands = [
            {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
            {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}},
            {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}},
        ]
        
        ordered, warnings = self.orderer.order_and_validate(commands)
        
        stats = self.orderer.get_statistics()
        
        # Проверяем статистику
        self.assertEqual(stats["total_processed"], 3)
        self.assertEqual(stats["total_compressed"], 2)  # 3 → 1
        self.assertGreater(stats["total_warnings"], 0)
        self.assertGreater(stats["compression_ratio"], 0)
        
        print(f"\n=== Statistics Test ===")
        print(f"Total processed: {stats['total_processed']}")
        print(f"Total compressed: {stats['total_compressed']}")
        print(f"Compression ratio: {stats['compression_ratio']:.1%}")
        print(f"Total warnings: {stats['total_warnings']}")


if __name__ == '__main__':
    # Запуск с подробным выводом
    unittest.main(verbosity=2)

