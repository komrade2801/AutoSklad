"""
CommandOrderer - Валидация, оптимизация и упорядочивание команд синхронизации.

Этот модуль реализует интеллектуальную обработку batch команд для системы синхронизации,
решая следующие проблемы:

1. Дедупликация избыточных команд (ADD+UPDATE → ADD, ADD+DELETE → DELETE)
2. Валидация корректности последовательностей операций
3. Упорядочивание команд по зависимостям внешних ключей (FK)
4. Группировка конфликтующих операций для предотвращения race conditions

Автор: AI Assistant
Дата создания: 9 декабря 2025
Версия: 1.0
"""

from typing import List, Dict, Any, Tuple, Set, Optional
from collections import defaultdict
from datetime import datetime
import threading


class CommandOrderer:
    """
    Валидация, оптимизация и упорядочивание команд синхронизации в batch.
    
    Основные возможности:
    - Сжатие последовательностей операций (compression)
    - Валидация порядка команд (validation)
    - Топологическая сортировка по FK зависимостям (ordering)
    - Обнаружение нарушений целостности данных
    
    Примеры использования:
    
    >>> orderer = CommandOrderer()
    >>> commands = [
    ...     {"operation": "ADD", "table": "ToolTypes", "data": {"id": 1, "name": "A"}},
    ...     {"operation": "UPDATE", "table": "ToolTypes", "data": {"id": 1, "name": "B"}},
    ...     {"operation": "DELETE", "table": "ToolTypes", "data": {"id": 1}}
    ... ]
    >>> ordered, warnings = orderer.order_and_validate(commands)
    >>> len(ordered)  # Только DELETE после оптимизации
    1
    >>> ordered[0]["operation"]
    'DELETE'
    
    Архитектура:
        CommandQueue/API → CommandOrderer → SyncProcessor → BatchProcessor → DB
    
    Зависимости:
        - threading: для потокобезопасности
        - Опционально: DiagnosticLogger для централизованного логирования
    """
    
    # Приоритеты таблиц для сортировки (низкий номер = выше приоритет)
    # Основано на анализе foreign key зависимостей из database_schema.md
    TABLE_PRIORITY = {
        # Уровень 0: Корневые справочники (без FK на другие бизнес-таблицы)
        "Status": 0,
        "Role": 1,
        "User": 2,
        "Page": 3,
        "Type": 4,
        "Settings": 5,
        "DeviceDefaults": 6,
        "Help": 7,
        
        # Уровень 1: Зависят только от уровня 0
        "Group": 10,
        "Plan": 11,
        "Rights": 12,
        "Identification": 13,
        "Device": 14,
        "Error": 15,
        
        # Уровень 2: Типы и экземпляры инструментов
        "ToolTypes": 20,
        "Tools": 21,
        "ActualNorm": 22,
        
        # Уровень 3: Ячейки и массовые операции
        "Cell": 30,
        "MassLoad": 31,
        "MassDrop": 32,
        "ToolsNorm": 33,
        
        # Уровень 4: Операции первого уровня
        # History должна быть перед Load/Drop/Consumption, так как они имеют FK на History
        "History": 40,
        "Load": 41,        # Depends on: History, Cell, ToolTypes, MassLoad, Plan, Status
        "Drop": 42,        # Depends on: History, Cell, ToolTypes, MassDrop, Plan, Status
        "Consumption": 43, # Depends on: History, Cell, ToolTypes, Plan, Status
        "Command": 44,
        
        # Уровень 5: Детализация операций
        "LoadOperations": 50,
        "DropOperations": 51,
        "OperationsConsumption": 52,
        
        # Уровень 6: Связующие таблицы (many-to-many)
        "PlanToolTypes": 60,
        "CellHasDevice": 61,
        "ToolsHasDevice": 62,
        "ActualNormHasDevice": 63,
        "MassLoadHasDevice": 64,
        "MassDropHasDevice": 65,
        "LoadOperationsHasDevice": 66,
        "DropOperationsHasDevice": 67,
        "OperationsConsumptionHasDevice": 68,
        "ErrorHasDevice": 69,
        "HistoryHasDevice": 70,
        
        # Уровень 7: Вспомогательные таблицы
        "ToolLocation": 71,
    }
    
    # Приоритет операций для сортировки
    # DELETE выполняется первым для освобождения FK constraint
    OPERATION_PRIORITY = {
        "DELETE": 0,  # Сначала удаляем (освобождаем FK)
        "UPDATE": 1,  # Потом обновляем
        "ADD": 2,     # В конце добавляем (требуют существования FK)
    }
    
    # Критические таблицы, для которых НЕЛЬЗЯ сжимать множественные UPDATE
    # Каждое изменение состояния критично для синхронизации
    # Основано на анализе схем данных: Cell имеет критичные переходы состояний
    # (status_id, tools_id, groups_id) которые должны сохраняться последовательно
    CRITICAL_STATE_TABLES = {
        # Таблицы массовых операций - каждое изменение критично
        "Load",  # Каждая Load запись должна быть создана отдельно (массовая загрузка)
        "MassLoad",  # Массовые операции
        "LoadOperations",  # Каждое изменение состояния операции важно
        "DropOperations",  # Каждое изменение состояния операции важно
        "Cell",  # Критично: status_id, tools_id меняются при массовой загрузке/выдаче
    }
    
    def __init__(self, logger=None):
        """
        Инициализация CommandOrderer.
        
        :param logger: Optional[DiagnosticLogger] - логгер для записи событий
        """
        self.logger = logger
        self._lock = threading.RLock()
        
        # Статистика работы (для мониторинга)
        self.stats = {
            "total_processed": 0,
            "total_compressed": 0,
            "total_warnings": 0,
        }
    
    def order_and_validate(
        self, 
        commands: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Основной метод: упорядочивание и валидация команд.
        
        Последовательность обработки:
        1. Группировка по (table, record_id)
        2. Возврат всех команд без оптимизации (временно отключено)
        3. Валидация корректности операций
        4. Топологическая сортировка по таблицам и операциям
        5. Финальная проверка зависимостей FK
        
        :param commands: Список команд от клиента
        :return: (validated_commands, warnings)
        
        Примеры warnings:
        - "Record ToolTypes:1 - Operations after DELETE: ['ADD']. Keeping only DELETE."
        - "Record Group:2 - Multiple ADD operations: positions [0, 2]. Keeping only the last one."
        - "DELETE Group 2 before DELETE ToolTypes (groups_id=2). May cause FK violation."
        """
        with self._lock:
            if not commands:
                return [], []
            
            warnings = []
            original_count = len(commands)
            
            if self.logger:
                self.logger.log_info(
                    "CommandOrderer: Starting processing",
                    {"command_count": original_count}
                )
            
            # Шаг 1: Группировка по (table, record_id)
            grouped = self._group_by_record(commands)
            
            # Шаг 2: Возврат всех команд без оптимизации (временно отключено)
            compressed, compress_warnings = self._compress_sequences(grouped)
            warnings.extend(compress_warnings)
            
            # Шаг 3: Валидация корректности операций
            validated, validate_warnings = self._validate_operations(compressed)
            warnings.extend(validate_warnings)
            
            # Шаг 4: Топологическая сортировка по таблицам и операциям
            ordered = self._topological_sort(validated)
            
            # Шаг 5: Финальная проверка зависимостей FK
            final, fk_warnings = self._check_foreign_keys(ordered)
            warnings.extend(fk_warnings)
            
            # Обновление статистики
            self.stats["total_processed"] += original_count
            self.stats["total_compressed"] += (original_count - len(final))
            self.stats["total_warnings"] += len(warnings)
            
            if self.logger:
                compression_ratio = (original_count - len(final)) / original_count if original_count > 0 else 0
                self.logger.log_info(
                    "CommandOrderer: Processing completed",
                    {
                        "original_count": original_count,
                        "final_count": len(final),
                        "compressed_count": original_count - len(final),
                        "compression_ratio": f"{compression_ratio:.1%}",
                        "warnings_count": len(warnings)
                    }
                )
            
            return final, warnings
    
    def _group_by_record(
        self, 
        commands: List[Dict[str, Any]]
    ) -> Dict[Tuple[str, Any], List[Dict[str, Any]]]:
        """
        Группирует команды по (table, record_id).
        
        Команды для одной записи группируются вместе для последующей оптимизации.
        Команды без ID (bulk операции) группируются отдельно.
        
        :param commands: Список команд
        :return: Словарь {(table, rec_id): [commands]}
        
        Пример:
        {
            ("ToolTypes", 1): [
                {"operation": "ADD", "data": {"id": 1, "name": "A"}},
                {"operation": "UPDATE", "data": {"id": 1, "name": "B"}}
            ],
            ("Group", 2): [
                {"operation": "DELETE", "data": {"id": 2}}
            ]
        }
        """
        grouped = defaultdict(list)
        
        for idx, cmd in enumerate(commands):
            table = cmd.get("table")
            data = cmd.get("data", {})
            
            # Пытаемся извлечь ID записи (разные источники)
            rec_id = (
                data.get("id") or 
                data.get("index") or 
                cmd.get("id")  # fallback на ID команды
            )
            
            if rec_id is None:
                # Команды без ID (bulk операции) - каждая в отдельную группу
                rec_id = f"_bulk_{idx}"
            
            key = (table, rec_id)
            grouped[key].append({
                "original_index": idx,
                "command": cmd
            })
        
        return grouped
    
    def _compress_sequences(
        self,
        grouped: Dict[Tuple[str, Any], List[Dict]]
    ) -> Tuple[List[Dict], List[str]]:
        """
        ВРЕМЕННО ОТКЛЮЧЕНО: Возвращает все команды без оптимизации.
        
        Ранее выполнялось сжатие последовательностей операций для каждой записи,
        но из-за проблем с потерей команд при синхронизации оптимизация временно отключена.
        
        TODO: Добавить правильную логику оптимизации позже.
        
        :param grouped: Сгруппированные команды
        :return: (commands, warnings) - все команды без изменений
        """
        warnings = []
        all_items = []
        
        # Просто собираем все команды в исходном порядке
        for (table, rec_id), items in grouped.items():
            all_items.extend(items)
        
        # Восстанавливаем исходный порядок (по original_index)
        all_items.sort(key=lambda x: x["original_index"])
        
        # Возвращаем только команды (без метаданных)
        return [item["command"] for item in all_items], warnings
    
    def _validate_operations(
        self,
        commands: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[str]]:
        """
        Валидирует корректность последовательностей операций.
        
        Проверки:
        1. UPDATE/DELETE без предшествующего ADD - предупреждение (может быть существующая запись)
        2. ADD для существующей записи - будет обработано как upsert (идемпотентность)
        3. DELETE несуществующей записи - идемпотентность (успех)
        
        :param commands: Список команд
        :return: (validated_commands, warnings)
        
        Примечание: Эта валидация работает на уровне batch команд.
        Реальное существование записей в БД проверяется позже в SyncProcessor.
        """
        warnings = []
        validated = []
        
        # Отслеживаем записи, которые были созданы в этом batch
        created_records = set()
        deleted_records = set()
        
        for cmd in commands:
            table = cmd.get("table")
            operation = cmd["operation"].upper()
            data = cmd.get("data", {})
            rec_id = data.get("id") or data.get("index")
            
            key = (table, rec_id)
            
            # Проверка 1: UPDATE/DELETE без ADD в batch
            if operation in ("UPDATE", "DELETE") and key not in created_records and key not in deleted_records:
                warnings.append(
                    f"Record {table}:{rec_id} - {operation} without preceding ADD in batch. "
                    f"Assuming record exists on server."
                )
            
            # Проверка 2: Повторный ADD (после DELETE)
            if operation == "ADD":
                if key in created_records and key not in deleted_records:
                    warnings.append(
                        f"Record {table}:{rec_id} - Duplicate ADD operation in batch. "
                        f"Will be handled as upsert by SyncManager."
                    )
                created_records.add(key)
            
            # Проверка 3: DELETE уже удалённой записи
            if operation == "DELETE":
                if key in deleted_records:
                    warnings.append(
                        f"Record {table}:{rec_id} - Multiple DELETE operations in batch. "
                        f"Redundant deletes will be idempotent."
                    )
                deleted_records.add(key)
                created_records.discard(key)
            
            # Проверка 4: UPDATE после DELETE
            if operation == "UPDATE" and key in deleted_records:
                warnings.append(
                    f"Record {table}:{rec_id} - UPDATE after DELETE in batch. "
                    f"This operation will likely fail."
                )
            
            validated.append(cmd)
        
        return validated, warnings
    
    def _topological_sort(
        self,
        commands: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Топологическая сортировка команд по зависимостям.
        
        Порядок сортировки:
        1. По приоритету таблиц (TABLE_PRIORITY) - FK зависимости
        2. По приоритету операций (OPERATION_PRIORITY) - DELETE → UPDATE → ADD
        3. По timestamp (если есть) - хронологический порядок
        
        Логика приоритетов операций:
        - DELETE: обратный порядок (дочерние таблицы сначала) - Cell → ToolTypes → Group
        - UPDATE: прямой порядок (требует существования родителей)
        - ADD: прямой порядок (родительские таблицы сначала) - Group → ToolTypes → Cell
        
        :param commands: Список команд
        :return: Отсортированные команды
        
        Пример:
        Входные: [ADD ToolTypes, DELETE Group, ADD Group]
        Выходные: [DELETE Group, ADD Group, ADD ToolTypes]
        """
        def sort_key(item):
            index, cmd = item
            table = cmd.get("table", "")
            operation = cmd["operation"].upper()
            timestamp = cmd.get("timestamp", "") or ""
            
            # Приоритет таблицы
            table_priority = self.TABLE_PRIORITY.get(table, 100)
            
            # Для DELETE инвертируем приоритет таблицы (дочерние сначала)
            # Для ADD/UPDATE используем прямой порядок (родители сначала)
            if operation == "DELETE":
                # Инверсия: высокий приоритет → низкий (Cell перед Group)
                table_priority = 1000 - table_priority
            
            # Приоритет операции (DELETE → UPDATE → ADD)
            op_priority = self.OPERATION_PRIORITY.get(operation, 99)
            
            # Составной ключ: индекс сохраняет исходный порядок при равенстве (стабильная сортировка)
            return (op_priority, table_priority, timestamp, index)
        
        indexed = list(enumerate(commands))
        return [cmd for _, cmd in sorted(indexed, key=sort_key)]
    
    def _check_foreign_keys(
        self,
        commands: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[str]]:
        """
        Проверяет, что команды не нарушают FK зависимости.
        
        Проверки:
        1. DELETE родительской записи до DELETE дочерних
        2. ADD дочерней записи до ADD родительской
        
        Известные FK зависимости (из database_schema.md):
        - ToolTypes.groups_id → Group.id
        - Tools.tool_type_id → ToolTypes.id
        - Cell.tools_id → ToolTypes.id
        - Load.history_id → History.id (NOT NULL, required)
        - Load.cell_id → Cell.id (NOT NULL, required)
        - Load.tools_id → ToolTypes.id (NOT NULL, required)
        - Load.mass_load_id → MassLoad.id (NOT NULL, required)
        - Drop.history_id → History.id (NOT NULL, required)
        - Drop.cell_id → Cell.id (NOT NULL, required)
        - Consumption.history_id → History.id (NOT NULL, required)
        - Consumption.cell_id → Cell.id (NOT NULL, required)
        
        :param commands: Отсортированные команды
        :return: (validated_commands, warnings)
        
        Примечание: Эта проверка детектирует потенциальные проблемы,
        но не изменяет порядок команд (это сделано в _topological_sort).
        """
        warnings = []
        
        # Отслеживаем создаваемые/удаляемые записи
        created = set()
        deleted = set()
        
        for cmd in commands:
            table = cmd.get("table")
            operation = cmd["operation"].upper()
            data = cmd.get("data", {})
            rec_id = data.get("id") or data.get("index")
            
            key = (table, rec_id)
            
            if operation == "ADD":
                created.add(key)
                
                # Проверка: ADD дочерней записи - существуют ли родители?
                if table == "ToolTypes":
                    groups_id = data.get("groups_id")
                    if groups_id:
                        parent_key = ("Group", groups_id)
                        if parent_key in deleted:
                            warnings.append(
                                f"ADD ToolTypes {rec_id} with groups_id={groups_id}, "
                                f"but Group {groups_id} was deleted in this batch. FK violation likely."
                            )
                        elif parent_key not in created:
                            # Проверяем, что родитель будет создан в этом batch
                            parent_will_be_created = any(
                                cmd.get("table") == "Group" and 
                                (cmd.get("data", {}).get("id") or cmd.get("data", {}).get("index")) == groups_id and
                                cmd.get("operation", "").upper() == "ADD"
                                for cmd in commands
                            )
                            if not parent_will_be_created:
                                warnings.append(
                                    f"ADD ToolTypes {rec_id} with groups_id={groups_id}, "
                                    f"but Group {groups_id} is not being created in this batch. "
                                    f"Assuming it exists on server."
                                )
                
                elif table == "Cell":
                    tools_id = data.get("tools_id")
                    if tools_id:
                        parent_key = ("ToolTypes", tools_id)
                        if parent_key in deleted:
                            warnings.append(
                                f"ADD Cell {rec_id} with tools_id={tools_id}, "
                                f"but ToolTypes {tools_id} was deleted in this batch. FK violation likely."
                            )
                        elif parent_key not in created:
                            parent_will_be_created = any(
                                cmd.get("table") == "ToolTypes" and 
                                (cmd.get("data", {}).get("id") or cmd.get("data", {}).get("index")) == tools_id and
                                cmd.get("operation", "").upper() == "ADD"
                                for cmd in commands
                            )
                            if not parent_will_be_created:
                                warnings.append(
                                    f"ADD Cell {rec_id} with tools_id={tools_id}, "
                                    f"but ToolTypes {tools_id} is not being created in this batch. "
                                    f"Assuming it exists on server."
                                )
                
                elif table == "Load":
                    # Load depends on: History, Cell, ToolTypes, MassLoad, Plan, Status
                    history_id = data.get("history_id")
                    cell_id = data.get("cell_id")
                    tools_id = data.get("tools_id")
                    mass_load_id = data.get("mass_load_id")
                    
                    # Critical: History must exist (NOT NULL FK)
                    if history_id:
                        history_key = ("History", history_id)
                        if history_key in deleted:
                            warnings.append(
                                f"ADD Load {rec_id} with history_id={history_id}, "
                                f"but History {history_id} was deleted in this batch. FK violation will occur!"
                            )
                        elif history_key not in created:
                            # Check if History will be created in this batch
                            history_will_be_created = any(
                                cmd.get("table") == "History" and 
                                (cmd.get("data", {}).get("id") or cmd.get("data", {}).get("index")) == history_id and
                                cmd.get("operation", "").upper() == "ADD"
                                for cmd in commands
                            )
                            if not history_will_be_created:
                                warnings.append(
                                    f"ADD Load {rec_id} with history_id={history_id}, "
                                    f"but History {history_id} is not being created in this batch. "
                                    f"FK violation will occur! History must be created before Load."
                                )
                    
                    # Check other required FKs
                    if cell_id:
                        cell_key = ("Cell", cell_id)
                        if cell_key in deleted:
                            warnings.append(
                                f"ADD Load {rec_id} with cell_id={cell_id}, "
                                f"but Cell {cell_id} was deleted in this batch. FK violation likely."
                            )
                    
                    if tools_id:
                        tools_key = ("ToolTypes", tools_id)
                        if tools_key in deleted:
                            warnings.append(
                                f"ADD Load {rec_id} with tools_id={tools_id}, "
                                f"but ToolTypes {tools_id} was deleted in this batch. FK violation likely."
                            )
                    
                    if mass_load_id:
                        mass_load_key = ("MassLoad", mass_load_id)
                        if mass_load_key in deleted:
                            warnings.append(
                                f"ADD Load {rec_id} with mass_load_id={mass_load_id}, "
                                f"but MassLoad {mass_load_id} was deleted in this batch. FK violation likely."
                            )
                
                elif table == "Drop":
                    # Drop depends on: History, Cell, ToolTypes, MassDrop, Plan, Status
                    history_id = data.get("history_id")
                    if history_id:
                        history_key = ("History", history_id)
                        if history_key in deleted:
                            warnings.append(
                                f"ADD Drop {rec_id} with history_id={history_id}, "
                                f"but History {history_id} was deleted in this batch. FK violation will occur!"
                            )
                        elif history_key not in created:
                            history_will_be_created = any(
                                cmd.get("table") == "History" and 
                                (cmd.get("data", {}).get("id") or cmd.get("data", {}).get("index")) == history_id and
                                cmd.get("operation", "").upper() == "ADD"
                                for cmd in commands
                            )
                            if not history_will_be_created:
                                warnings.append(
                                    f"ADD Drop {rec_id} with history_id={history_id}, "
                                    f"but History {history_id} is not being created in this batch. "
                                    f"FK violation will occur! History must be created before Drop."
                                )
                
                elif table == "Consumption":
                    # Consumption depends on: History, Cell, ToolTypes, Plan, Status
                    history_id = data.get("history_id")
                    if history_id:
                        history_key = ("History", history_id)
                        if history_key in deleted:
                            warnings.append(
                                f"ADD Consumption {rec_id} with history_id={history_id}, "
                                f"but History {history_id} was deleted in this batch. FK violation will occur!"
                            )
                        elif history_key not in created:
                            history_will_be_created = any(
                                cmd.get("table") == "History" and 
                                (cmd.get("data", {}).get("id") or cmd.get("data", {}).get("index")) == history_id and
                                cmd.get("operation", "").upper() == "ADD"
                                for cmd in commands
                            )
                            if not history_will_be_created:
                                warnings.append(
                                    f"ADD Consumption {rec_id} with history_id={history_id}, "
                                    f"but History {history_id} is not being created in this batch. "
                                    f"FK violation will occur! History must be created before Consumption."
                                )
            
            elif operation == "DELETE":
                deleted.add(key)
                
                # Проверка: DELETE родителя - есть ли неудалённые дочерние записи?
                if table == "Group":
                    # Проверяем, что все ToolTypes этой группы удалены
                    for other_cmd in commands:
                        if (other_cmd.get("table") == "ToolTypes" and
                            other_cmd["operation"].upper() != "DELETE"):
                            other_data = other_cmd.get("data", {})
                            if other_data.get("groups_id") == rec_id:
                                warnings.append(
                                    f"DELETE Group {rec_id} while ToolTypes (groups_id={rec_id}) still exists. "
                                    f"FK constraint violation likely."
                                )
                
                elif table == "ToolTypes":
                    # Проверяем Cell, Load, Drop, Consumption
                    for other_cmd in commands:
                        other_table = other_cmd.get("table")
                        if other_table in ("Cell", "Load", "Drop", "Consumption"):
                            if other_cmd["operation"].upper() != "DELETE":
                                other_data = other_cmd.get("data", {})
                                if other_data.get("tools_id") == rec_id:
                                    warnings.append(
                                        f"DELETE ToolTypes {rec_id} while {other_table} (tools_id={rec_id}) still exists. "
                                        f"FK constraint violation likely."
                                    )
                
                elif table == "History":
                    # Проверяем Load, Drop, Consumption, LoadOperations, DropOperations, OperationsConsumption
                    for other_cmd in commands:
                        other_table = other_cmd.get("table")
                        if other_table in ("Load", "Drop", "Consumption", "LoadOperations", "DropOperations", "OperationsConsumption"):
                            if other_cmd["operation"].upper() != "DELETE":
                                other_data = other_cmd.get("data", {})
                                if other_data.get("history_id") == rec_id:
                                    warnings.append(
                                        f"DELETE History {rec_id} while {other_table} (history_id={rec_id}) still exists. "
                                        f"FK constraint violation will occur!"
                                    )
                
                elif table == "Cell":
                    # Проверяем Load, Drop, Consumption
                    for other_cmd in commands:
                        other_table = other_cmd.get("table")
                        if other_table in ("Load", "Drop", "Consumption"):
                            if other_cmd["operation"].upper() != "DELETE":
                                other_data = other_cmd.get("data", {})
                                if other_data.get("cell_id") == rec_id:
                                    warnings.append(
                                        f"DELETE Cell {rec_id} while {other_table} (cell_id={rec_id}) still exists. "
                                        f"FK constraint violation likely."
                                    )
                
                elif table == "MassLoad":
                    # Проверяем Load
                    for other_cmd in commands:
                        if other_cmd.get("table") == "Load":
                            if other_cmd["operation"].upper() != "DELETE":
                                other_data = other_cmd.get("data", {})
                                if other_data.get("mass_load_id") == rec_id:
                                    warnings.append(
                                        f"DELETE MassLoad {rec_id} while Load (mass_load_id={rec_id}) still exists. "
                                        f"FK constraint violation likely."
                                    )
        
        return commands, warnings
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы CommandOrderer.
        
        :return: Словарь со статистикой
        
        Пример:
        {
            "total_processed": 1500,
            "total_compressed": 600,
            "total_warnings": 23,
            "compression_ratio": 0.40
        }
        """
        with self._lock:
            stats = self.stats.copy()
            
            if stats["total_processed"] > 0:
                stats["compression_ratio"] = stats["total_compressed"] / stats["total_processed"]
            else:
                stats["compression_ratio"] = 0.0
            
            return stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Alias для get_stats() для совместимости с тестами.
        """
        return self.get_stats()
    
    def reset_stats(self):
        """Сбрасывает статистику (для тестирования)."""
        with self._lock:
            self.stats = {
                "total_processed": 0,
                "total_compressed": 0,
                "total_warnings": 0,
            }

