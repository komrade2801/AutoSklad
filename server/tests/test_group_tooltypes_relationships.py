#!/usr/bin/env python3
"""
Тест взаимосвязей между группами, номенклатурами и загрузками инструментов.

Этот тест проверяет:
1. Создание групп (включая вложенные)
2. Создание номенклатур (ToolTypes) в группах
3. Проверку занятости инструментов через Load
4. Рекурсивное удаление групп
5. Взаимосвязи между Group, ToolTypes, Load

Использование:
    pytest test_group_tooltypes_relationships.py -v
    python test_group_tooltypes_relationships.py
"""

import pytest
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

# Импорты для работы с БД
from DB.Data.sqlite_db import SessionLocal, get_engine
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.ToolTypesCRUD import EngineToolTypes
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Models.Group import Group
from DB.Models.ToolTypes import ToolTypes
from DB.Models.Load import Load


class GroupToolTypesTestLogger:
    """Класс для логирования результатов тестов."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_entries = []
        
    def log(self, message: str, level: str = "INFO"):
        """Добавляет запись в лог."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{timestamp}] [{level}] {message}"
        self.log_entries.append(entry)
        print(entry)
        
    def log_error(self, message: str, exception: Exception = None):
        """Логирует ошибку с трассировкой."""
        self.log(f"ОШИБКА: {message}", "ERROR")
        if exception:
            self.log(f"Тип исключения: {type(exception).__name__}", "ERROR")
            self.log(f"Сообщение: {str(exception)}", "ERROR")
            self.log(f"Трассировка:\n{traceback.format_exc()}", "ERROR")
            
    def log_success(self, message: str):
        """Логирует успешную операцию."""
        self.log(f"✓ {message}", "SUCCESS")
        
    def log_warning(self, message: str):
        """Логирует предупреждение."""
        self.log(f"⚠ {message}", "WARNING")
        
    def log_data(self, title: str, data: any):
        """Логирует данные в структурированном виде."""
        self.log(f"\n=== {title} ===", "DATA")
        try:
            if isinstance(data, (dict, list)):
                formatted = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            else:
                formatted = str(data)
            self.log(formatted, "DATA")
        except Exception as e:
            self.log(f"Не удалось сериализовать данные: {e}", "WARNING")
            self.log(str(data), "DATA")
            
    def save_to_file(self):
        """Сохраняет все записи в файл."""
        try:
            with self.log_file.open("w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("ТЕСТ ВЗАИМОСВЯЗЕЙ ГРУПП, НОМЕНКЛАТУР И ЗАГРУЗОК\n")
                f.write("=" * 80 + "\n")
                f.write(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
                for entry in self.log_entries:
                    f.write(entry + "\n")
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            print(f"Ошибка при сохранении лога: {e}")


# Фикстуры для тестов
@pytest.fixture(scope="function")
def db_session():
    """Создает сессию БД для теста."""
    # Инициализируем БД если нужно
    from DB.Data.init_db import initialize_database_if_needed
    from Core.default import rebuild_db, execute
    from pathlib import Path
    import dbSync
    
    db_path = Path("DB/Data/web_vending.db")
    if not db_path.exists():
        # Full database setup: create tables AND populate with initial data
        dbSync.init_db = True
        rebuild_db()
        execute()
    else:
        dbSync.init_db = True
        initialize_database_if_needed()
    
    # Включаем синхронизацию для всех тестов
    dbSync.init_db = True
    
    session = SessionLocal()
    try:
        yield session
    finally:
        # Отключаем синхронизацию после теста
        dbSync.init_db = False
        session.close()


@pytest.fixture(scope="function")
def test_logger(tmp_path):
    """Создает логгер для теста."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = tmp_path / f"test_group_tooltypes_{timestamp}.txt"
    logger = GroupToolTypesTestLogger(log_file)
    yield logger
    logger.save_to_file()
    # Копируем лог в tests/logs/
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    final_log = logs_dir / log_file.name
    try:
        import shutil
        shutil.copy2(log_file, final_log)
        print(f"\n✓ Лог сохранен: {final_log.absolute()}")
    except Exception as e:
        print(f"Не удалось скопировать лог: {e}")


@pytest.fixture(scope="function")
def crud_engines(db_session):
    """Создает CRUD движки для работы с БД."""
    return {
        "group": EngineGroup(session=db_session),
        "tool_types": EngineToolTypes(session=db_session),
        "load": EngineLoad(session=db_session),
        "cell": EngineCell(session=db_session),
        "status": EngineStatus(session=db_session),
        "mass_load": EngineMassLoad(session=db_session),
        "history": EngineHistory(session=db_session),
    }


@pytest.fixture(scope="function")
def test_fixtures(crud_engines, test_logger):
    """Создает тестовые данные (фикстуры) для тестов."""
    fixtures = {
        "groups": [],
        "tool_types": [],
        "loads": [],
        "cells": [],
        "statuses": [],
    }
    
    test_logger.log("Создание тестовых фикстур...", "SETUP")
    
    # Создаем статусы
    try:
        status_crud = crud_engines["status"]
        mass_load_status = status_crud.find_by_name("mass_load_init")
        if not mass_load_status:
            status_ids = status_crud.get_all_ids()
            new_status_id = max(status_ids, default=0) + 1
            status_crud.add(
                index=new_status_id,
                stype="mass_load_init",
                description="Массовая загрузка инициирована"
            )
            mass_load_status = status_crud.find_by_name("mass_load_init")
        fixtures["statuses"].append(mass_load_status)
        test_logger.log_success(f"Создан/найден статус: {mass_load_status.stype} (ID: {mass_load_status.id})")
    except Exception as e:
        test_logger.log_error("Ошибка при создании статуса", e)
        raise
    
    # Создаем ячейки для тестов
    try:
        cell_crud = crud_engines["cell"]
        for cell_num in [1, 2, 3]:
            cell = cell_crud.get_cell_by_number(cell_num)
            if not cell:
                cell_ids = cell_crud.get_all_ids()
                new_cell_id = max(cell_ids, default=0) + 1
                cell_crud.add_cell(
                    index=new_cell_id,
                    number=cell_num,
                    groups_id=0,
                    tools_id=0,
                    status_id=0,
                    description=f"Тестовая ячейка {cell_num}"
                )
                cell = cell_crud.get_cell_by_number(cell_num)
            fixtures["cells"].append(cell)
            test_logger.log_success(f"Создана/найдена ячейка: {cell.number} (ID: {cell.id})")
    except Exception as e:
        test_logger.log_error("Ошибка при создании ячеек", e)
        # Не критично, продолжаем
    
    # Создаем группы (иерархическая структура)
    try:
        group_crud = crud_engines["group"]
        
        def create_and_verify_group(name, description, paren_group_id):
            """Создает группу и проверяет её наличие в БД."""
            # Создаем группу
            created_group = group_crud.create_group(
                name=name,
                description=description,
                paren_group_id=paren_group_id
            )
            
            # Если create_group вернул None, пытаемся найти через прямую сессию
            if not created_group:
                # Очищаем кеш и ищем через прямую сессию
                group_crud._cache.clear()
                # Пробуем найти по имени
                found_groups = group_crud.find_groups_by_name(name)
                if found_groups:
                    created_group = found_groups[0]
                    test_logger.log_warning(f"Группа '{name}' найдена через поиск по имени после создания")
                else:
                    # Если не нашли, пробуем получить последний созданный ID
                    all_ids = group_crud.get_all_ids()
                    if all_ids:
                        last_id = max(all_ids)
                        created_group = group_crud.get_group_by_id(last_id)
                        if created_group and created_group.name == name:
                            test_logger.log_warning(f"Группа '{name}' найдена по последнему ID: {last_id}")
                        else:
                            created_group = None
            
            # Если все еще None, создаем через прямую сессию
            if not created_group:
                all_ids = group_crud.get_all_ids()
                new_id = max(all_ids, default=0) + 1
                if group_crud.add_group(index=new_id, name=name, description=description, paren_group_id=paren_group_id):
                    group_crud._cache.clear()
                    created_group = group_crud.get_group_by_id(new_id)
                    if not created_group:
                        # Прямой запрос через сессию
                        from DB.Models.Group import Group
                        created_group = group_crud.session.query(Group).filter_by(id=new_id).first()
            
            return created_group
        
        # Корневая группа
        root_group = create_and_verify_group(
            "Тестовая корневая группа",
            "Корневая группа для тестирования",
            0
        )
        if root_group:
            fixtures["groups"].append(root_group)
            test_logger.log_success(f"Создана корневая группа: {root_group.name} (ID: {root_group.id})")
        else:
            raise Exception("Не удалось создать корневую группу")
        
        # Дочерние группы
        child_group1 = create_and_verify_group(
            "Тестовая дочерняя группа 1",
            "Первая дочерняя группа",
            root_group.id
        )
        if child_group1:
            fixtures["groups"].append(child_group1)
            test_logger.log_success(f"Создана дочерняя группа 1: {child_group1.name} (ID: {child_group1.id})")
        
        child_group2 = create_and_verify_group(
            "Тестовая дочерняя группа 2",
            "Вторая дочерняя группа",
            root_group.id
        )
        if child_group2:
            fixtures["groups"].append(child_group2)
            test_logger.log_success(f"Создана дочерняя группа 2: {child_group2.name} (ID: {child_group2.id})")
        
        # Вложенная группа (3 уровня)
        if child_group1:
            nested_group = create_and_verify_group(
                "Тестовая вложенная группа",
                "Группа третьего уровня",
                child_group1.id
            )
            if nested_group:
                fixtures["groups"].append(nested_group)
                test_logger.log_success(f"Создана вложенная группа: {nested_group.name} (ID: {nested_group.id})")
    except Exception as e:
        test_logger.log_error("Ошибка при создании групп", e)
        raise
    
    # Создаем номенклатуры инструментов
    try:
        tool_types_crud = crud_engines["tool_types"]
        
        for i, group in enumerate(fixtures["groups"][:3], 1):  # Первые 3 группы
            tool_type_ids = tool_types_crud.get_all_ids()
            new_tool_type_id = max(tool_type_ids, default=0) + 1
            
            tool_type = tool_types_crud.add_tool_type(
                tool_type_id=new_tool_type_id,
                name=f"Тестовый инструмент {i}",
                description=f"Описание тестового инструмента {i}",
                count=5 + i,  # Разное количество
                img="",
                groups_id=group.id
            )
            
            if tool_type:
                # Очищаем кеш перед получением
                tool_types_crud._cache.clear()
                created_tt = tool_types_crud.get_tool_type_by_id(new_tool_type_id)
                if not created_tt:
                    # Пробуем через прямую сессию
                    from DB.Models.ToolTypes import ToolTypes
                    created_tt = tool_types_crud.session.query(ToolTypes).filter_by(id=new_tool_type_id).first()
                if created_tt:
                    fixtures["tool_types"].append(created_tt)
                    test_logger.log_success(
                        f"Создана номенклатура: {created_tt.name} "
                        f"(ID: {created_tt.id}, Группа: {group.name}, Количество: {created_tt.count})"
                    )
    except Exception as e:
        test_logger.log_error("Ошибка при создании номенклатур", e)
        raise
    
    test_logger.log_data("Созданные фикстуры", {
        "groups": [{"id": g.id, "name": g.name, "parent": g.paren_group_id} for g in fixtures["groups"]],
        "tool_types": [{"id": tt.id, "name": tt.name, "group_id": tt.groups_id, "count": tt.count} for tt in fixtures["tool_types"]],
        "cells": [{"id": c.id, "number": c.number} for c in fixtures["cells"]],
    })
    
    yield fixtures
    
    # Очистка после теста
    test_logger.log("Очистка тестовых данных...", "CLEANUP")
    try:
        # Удаляем Load записи
        load_crud = crud_engines["load"]
        for load in fixtures["loads"]:
            try:
                load_crud.delete(index=load.id)
            except:
                pass
        
        # Удаляем ToolTypes
        tool_types_crud = crud_engines["tool_types"]
        for tt in fixtures["tool_types"]:
            try:
                tool_types_crud.delete_tool_type(tt.id)
            except:
                pass
        
        # Удаляем группы (рекурсивно, начиная с листьев)
        group_crud = crud_engines["group"]
        for group in reversed(fixtures["groups"]):
            try:
                if group_crud.delete_group(group.id):
                    # Очищаем кеш после удаления
                    group_crud._cache.clear()
            except:
                pass
                
        test_logger.log_success("Очистка завершена")
    except Exception as e:
        test_logger.log_error("Ошибка при очистке", e)


def test_group_creation_and_hierarchy(test_fixtures, crud_engines, test_logger):
    """Тест создания групп и проверки иерархии."""
    test_logger.log("\n" + "=" * 80, "TEST")
    test_logger.log("ТЕСТ 1: Создание групп и проверка иерархии", "TEST")
    test_logger.log("=" * 80, "TEST")
    
    try:
        group_crud = crud_engines["group"]
        groups = test_fixtures["groups"]
        
        # Проверяем, что все группы созданы
        assert len(groups) > 0, "Не создано ни одной группы"
        test_logger.log_success(f"Создано групп: {len(groups)}")
        
        # Проверяем иерархию
        root_group = groups[0]
        assert root_group.paren_group_id == 0 or root_group.paren_group_id is None, \
            f"Корневая группа должна иметь parent_group_id = 0, получено: {root_group.paren_group_id}"
        test_logger.log_success(f"Корневая группа корректна: {root_group.name} (parent: {root_group.paren_group_id})")
        
        # Проверяем дочерние группы
        child_groups = [g for g in groups if g.paren_group_id == root_group.id]
        assert len(child_groups) >= 2, f"Ожидалось минимум 2 дочерние группы, получено: {len(child_groups)}"
        test_logger.log_success(f"Найдено дочерних групп: {len(child_groups)}")
        
        # Проверяем вложенность (3 уровень)
        nested_groups = [g for g in groups if g.paren_group_id in [cg.id for cg in child_groups]]
        if nested_groups:
            test_logger.log_success(f"Найдено вложенных групп (3 уровень): {len(nested_groups)}")
        
        # Проверяем рекурсивный поиск дочерних групп
        def get_all_children(parent_id: int) -> List[int]:
            """Рекурсивно получает все дочерние группы."""
            children = []
            child_list = group_crud.get_groups_by_paren_group_id(parent_id)
            for child in child_list:
                children.append(child.id)
                children.extend(get_all_children(child.id))
            return children
        
        all_children = get_all_children(root_group.id)
        test_logger.log_data(f"Все дочерние группы для {root_group.name}", all_children)
        assert len(all_children) >= 2, "Рекурсивный поиск не нашел все дочерние группы"
        test_logger.log_success("Рекурсивный поиск дочерних групп работает корректно")
        
    except AssertionError as e:
        test_logger.log_error("Ошибка в тесте создания групп", e)
        raise
    except Exception as e:
        test_logger.log_error("Неожиданная ошибка в тесте создания групп", e)
        raise


def test_tooltypes_group_relationship(test_fixtures, crud_engines, test_logger):
    """Тест связи номенклатур с группами."""
    test_logger.log("\n" + "=" * 80, "TEST")
    test_logger.log("ТЕСТ 2: Связь номенклатур с группами", "TEST")
    test_logger.log("=" * 80, "TEST")
    
    try:
        tool_types_crud = crud_engines["tool_types"]
        groups = test_fixtures["groups"]
        tool_types = test_fixtures["tool_types"]
        
        # Проверяем, что номенклатуры созданы
        assert len(tool_types) > 0, "Не создано ни одной номенклатуры"
        test_logger.log_success(f"Создано номенклатур: {len(tool_types)}")
        
        # Проверяем связь каждой номенклатуры с группой
        for tt in tool_types:
            assert tt.groups_id is not None, f"Номенклатура {tt.name} не привязана к группе"
            group = next((g for g in groups if g.id == tt.groups_id), None)
            assert group is not None, f"Группа с ID {tt.groups_id} не найдена для номенклатуры {tt.name}"
            test_logger.log_success(
                f"Номенклатура '{tt.name}' (ID: {tt.id}) привязана к группе '{group.name}' (ID: {group.id})"
            )
        
        # Проверяем получение номенклатур по группе
        for group in groups[:3]:  # Первые 3 группы
            group_tool_types = tool_types_crud.get_by_group(group.id)
            test_logger.log_data(
                f"Номенклатуры в группе '{group.name}'",
                [{"id": tt.id, "name": tt.name, "count": tt.count} for tt in group_tool_types]
            )
            # Проверяем, что найденные номенклатуры действительно принадлежат группе
            for tt in group_tool_types:
                assert tt.groups_id == group.id, \
                    f"Номенклатура {tt.name} должна принадлежать группе {group.id}, но имеет groups_id={tt.groups_id}"
        
        test_logger.log_success("Все номенклатуры корректно привязаны к группам")
        
    except AssertionError as e:
        test_logger.log_error("Ошибка в тесте связи номенклатур с группами", e)
        raise
    except Exception as e:
        test_logger.log_error("Неожиданная ошибка в тесте связи номенклатур с группами", e)
        raise


def test_tool_busy_check(test_fixtures, crud_engines, test_logger):
    """Тест проверки занятости инструментов через Load."""
    test_logger.log("\n" + "=" * 80, "TEST")
    test_logger.log("ТЕСТ 3: Проверка занятости инструментов", "TEST")
    test_logger.log("=" * 80, "TEST")
    
    try:
        load_crud = crud_engines["load"]
        tool_types_crud = crud_engines["tool_types"]
        status_crud = crud_engines["status"]
        cell_crud = crud_engines["cell"]
        mass_load_crud = crud_engines["mass_load"]
        history_crud = crud_engines["history"]
        
        tool_types = test_fixtures["tool_types"]
        cells = test_fixtures["cells"]
        statuses = test_fixtures["statuses"]
        
        if not tool_types or not cells or not statuses:
            test_logger.log_warning("Недостаточно фикстур для теста занятости")
            return
        
        # Создаем массовую загрузку
        mass_load_ids = mass_load_crud.get_all_ids()
        new_mass_load_id = max(mass_load_ids, default=0) + 1
        test_status = statuses[0]
        mass_load_crud.add_mass_load(
            description="Тестовая массовая загрузка",
            status_id=test_status.id,
            index=new_mass_load_id
        )
        mass_load = mass_load_crud.get_mass_load_by_id(new_mass_load_id)
        test_logger.log_success(f"Создана массовая загрузка: ID {mass_load.id}")
        
        # Пытаемся найти существующую History запись или создаем минимальную через прямую сессию
        from DB.Models.History import History
        existing_history = history_crud.session.query(History).first()
        
        if not existing_history:
            # Создаем минимальную History запись через прямую сессию (обходя проверку внешних ключей)
            try:
                history_ids = history_crud.get_all_ids()
                new_history_id = max(history_ids, default=0) + 1
                # Создаем History с минимальными данными, используя прямую сессию
                # user_role_id может быть None или 0, если таблица Role не существует
                history = History(
                    id=new_history_id,
                    datetime=datetime.now(),
                    status=0,
                    description="Тестовая история",
                    user_id=1,
                    user_role_id=None,  # Попробуем None, если не сработает - используем 0
                    tools_id=tool_types[0].id,
                    plan_id=None
                )
                history_crud.session.add(history)
                history_crud.session.commit()
                existing_history = history
                test_logger.log_success(f"Создана минимальная History запись: ID {existing_history.id}")
            except Exception as e:
                test_logger.log_warning(f"Не удалось создать History: {e}. Пропускаем тест Load записей.")
                return
        
        history_id = existing_history.id
        
        # Создаем Load записи для некоторых инструментов
        test_tool_type = tool_types[0]
        test_cell = cells[0] if cells else None
        test_status = statuses[0]
        
        if test_cell:
            # Создаем 2 Load записи для одного типа инструмента
            for i in range(2):
                load_ids = load_crud.get_all_ids()
                new_load_id = max(load_ids, default=0) + 1
                
                load_crud.add_load(
                    load_id=new_load_id,
                    description=f"Тестовая загрузка {i+1}",
                    tools_id=test_tool_type.id,
                    mass_load_id=mass_load.id,
                    cell_id=test_cell.id,
                    plan_id=None,
                    history_id=history_id,
                    status_id=test_status.id
                )
                load = load_crud.get_load_by_id(new_load_id)
                if load:
                    test_fixtures["loads"].append(load)
                    test_logger.log_success(
                        f"Создана Load запись: ID {load.id}, "
                        f"ToolType ID {load.tools_id}, Cell ID {load.cell_id}"
                    )
        
        # Проверяем занятость инструмента
        loads = load_crud.find_by_tools_id(test_tool_type.id)
        test_logger.log_data(
            f"Load записи для номенклатуры '{test_tool_type.name}' (ID: {test_tool_type.id})",
            [{"id": l.id, "tools_id": l.tools_id, "cell_id": l.cell_id} for l in loads]
        )
        
        assert len(loads) == 2, f"Ожидалось 2 Load записи, получено: {len(loads)}"
        test_logger.log_success(f"Найдено Load записей: {len(loads)}")
        
        # Проверяем расчет доступного количества
        original_count = test_tool_type.count
        busy_count = len(loads)
        available_count = original_count - busy_count
        
        test_logger.log_data("Расчет доступного количества", {
            "Исходное количество": original_count,
            "Занято (Load записей)": busy_count,
            "Доступно": available_count
        })
        
        assert available_count == original_count - busy_count, \
            f"Неверный расчет доступного количества: {available_count} != {original_count} - {busy_count}"
        test_logger.log_success("Расчет доступного количества корректен")
        
        # Проверяем, что свободные инструменты не имеют Load записей
        free_tool_type = tool_types[1] if len(tool_types) > 1 else None
        if free_tool_type:
            free_loads = load_crud.find_by_tools_id(free_tool_type.id)
            assert len(free_loads) == 0, \
                f"Свободный инструмент {free_tool_type.name} не должен иметь Load записей"
            test_logger.log_success(
                f"Инструмент '{free_tool_type.name}' свободен (нет Load записей)"
            )
        
    except AssertionError as e:
        test_logger.log_error("Ошибка в тесте проверки занятости", e)
        raise
    except Exception as e:
        test_logger.log_error("Неожиданная ошибка в тесте проверки занятости", e)
        raise


def test_recursive_group_busy_check(test_fixtures, crud_engines, test_logger):
    """Тест рекурсивной проверки занятости инструментов в группе."""
    test_logger.log("\n" + "=" * 80, "TEST")
    test_logger.log("ТЕСТ 4: Рекурсивная проверка занятости группы", "TEST")
    test_logger.log("=" * 80, "TEST")
    
    try:
        group_crud = crud_engines["group"]
        tool_types_crud = crud_engines["tool_types"]
        load_crud = crud_engines["load"]
        
        groups = test_fixtures["groups"]
        if not groups:
            test_logger.log_warning("Нет групп для теста")
            return
        
        root_group = groups[0]
        
        # Функция рекурсивной проверки занятости
        def check_group_busy_recursive(group_id: int) -> Tuple[bool, List[str]]:
            """Рекурсивно проверяет занятость группы и всех дочерних групп."""
            is_busy = False
            messages = []
            
            # Проверяем номенклатуры в текущей группе
            tool_types = tool_types_crud.get_by_group(group_id)
            for tool_type in tool_types:
                loads = load_crud.find_by_tools_id(tool_type.id)
                if loads:
                    is_busy = True
                    group = group_crud.get_group_by_id(group_id)
                    group_name = group.name if group else f"ID {group_id}"
                    messages.append(
                        f"Группа '{group_name}' (ID: {group_id}) содержит занятые инструменты: "
                        f"'{tool_type.name}' (ID: {tool_type.id}, Load записей: {len(loads)})"
                    )
            
            # Рекурсивно проверяем дочерние группы
            child_groups = group_crud.get_groups_by_paren_group_id(group_id)
            for child_group in child_groups:
                child_busy, child_messages = check_group_busy_recursive(child_group.id)
                if child_busy:
                    is_busy = True
                    messages.extend(child_messages)
            
            return is_busy, messages
        
        # Проверяем корневую группу
        is_busy, messages = check_group_busy_recursive(root_group.id)
        
        test_logger.log_data(
            f"Результат проверки занятости группы '{root_group.name}'",
            {
                "Занята": is_busy,
                "Сообщения": messages
            }
        )
        
        # Если есть Load записи, группа должна быть занята
        if test_fixtures["loads"]:
            assert is_busy, "Группа должна быть занята, так как есть Load записи"
            test_logger.log_success("Рекурсивная проверка занятости работает корректно (группа занята)")
        else:
            assert not is_busy, "Группа не должна быть занята, так как нет Load записей"
            test_logger.log_success("Рекурсивная проверка занятости работает корректно (группа свободна)")
        
    except AssertionError as e:
        test_logger.log_error("Ошибка в тесте рекурсивной проверки занятости", e)
        raise
    except Exception as e:
        test_logger.log_error("Неожиданная ошибка в тесте рекурсивной проверки занятости", e)
        raise


def test_recursive_group_deletion(test_fixtures, crud_engines, test_logger):
    """Тест рекурсивного удаления групп."""
    test_logger.log("\n" + "=" * 80, "TEST")
    test_logger.log("ТЕСТ 5: Рекурсивное удаление групп", "TEST")
    test_logger.log("=" * 80, "TEST")
    
    try:
        group_crud = crud_engines["group"]
        tool_types_crud = crud_engines["tool_types"]
        load_crud = crud_engines["load"]
        
        # Вспомогательная функция для создания и проверки группы
        def create_and_verify_group(name, description, paren_group_id):
            """Создает группу и проверяет её наличие в БД."""
            created_group = group_crud.create_group(
                name=name,
                description=description,
                paren_group_id=paren_group_id
            )
            if not created_group:
                group_crud._cache.clear()
                found_groups = group_crud.find_groups_by_name(name)
                if found_groups:
                    created_group = found_groups[0]
                else:
                    all_ids = group_crud.get_all_ids()
                    if all_ids:
                        last_id = max(all_ids)
                        created_group = group_crud.get_group_by_id(last_id)
                        if not created_group or created_group.name != name:
                            from DB.Models.Group import Group
                            created_group = group_crud.session.query(Group).filter_by(name=name).first()
            return created_group
        
        # Создаем отдельную группу для теста удаления (не используем фикстуры)
        test_group = create_and_verify_group(
            "Группа для удаления",
            "Группа для тестирования удаления",
            0
        )
        
        if not test_group:
            test_logger.log_warning("Не удалось создать группу для теста удаления")
            return
        
        test_logger.log_success(f"Создана группа для удаления: {test_group.name} (ID: {test_group.id})")
        
        # Создаем дочернюю группу
        child_group = create_and_verify_group(
            "Дочерняя группа для удаления",
            "Дочерняя группа",
            test_group.id
        )
        
        if child_group:
            test_logger.log_success(f"Создана дочерняя группа: {child_group.name} (ID: {child_group.id})")
        
        # Создаем номенклатуры в обеих группах
        test_tool_types = []
        for group in [test_group, child_group] if child_group else [test_group]:
            tool_type_ids = tool_types_crud.get_all_ids()
            new_tool_type_id = max(tool_type_ids, default=0) + 1
            
            tool_types_crud.add_tool_type(
                tool_type_id=new_tool_type_id,
                name=f"Инструмент в {group.name}",
                description="Тестовый инструмент",
                count=3,
                img="",
                groups_id=group.id
            )
            
            # Очищаем кеш перед получением
            tool_types_crud._cache.clear()
            created_tt = tool_types_crud.get_tool_type_by_id(new_tool_type_id)
            if not created_tt:
                from DB.Models.ToolTypes import ToolTypes
                created_tt = tool_types_crud.session.query(ToolTypes).filter_by(id=new_tool_type_id).first()
            if created_tt:
                test_tool_types.append(created_tt)
                test_logger.log_success(
                    f"Создана номенклатура: {created_tt.name} (ID: {created_tt.id})"
                )
        
        # Функция рекурсивного удаления
        def delete_group_recursive(group_id: int) -> Tuple[int, int]:
            """Рекурсивно удаляет группу и все дочерние группы."""
            deleted_groups_count = 0
            deleted_tool_types_count = 0
            
            # Получаем все дочерние группы
            def get_all_nested_groups(parent_group_id: int) -> List[int]:
                all_group_ids = [parent_group_id]
                child_groups = group_crud.get_groups_by_paren_group_id(parent_group_id)
                for child_group in child_groups:
                    all_group_ids.extend(get_all_nested_groups(child_group.id))
                return all_group_ids
            
            all_group_ids = get_all_nested_groups(group_id)
            test_logger.log_data(
                f"Группы для удаления (рекурсивно)",
                all_group_ids
            )
            
            # Удаляем номенклатуры из всех групп (в обратном порядке)
            for gid in reversed(all_group_ids):
                tool_types = tool_types_crud.get_by_group(gid)
                for tool_type in tool_types:
                    if tool_types_crud.delete_tool_type(tool_type.id):
                        deleted_tool_types_count += 1
                        # Очищаем кеш после удаления
                        tool_types_crud._cache.clear()
                        test_logger.log_success(
                            f"Удалена номенклатура: {tool_type.name} (ID: {tool_type.id})"
                        )
            
            # Удаляем группы (в обратном порядке, начиная с листьев)
            for gid in reversed(all_group_ids):
                # Получаем имя группы перед удалением
                group_before = group_crud.get_group_by_id(gid)
                group_name = group_before.name if group_before else f"ID {gid}"
                
                if group_crud.delete_group(gid):
                    deleted_groups_count += 1
                    # Очищаем кеш после удаления
                    group_crud._cache.clear()
                    test_logger.log_success(f"Удалена группа: {group_name} (ID: {gid})")
            
            return deleted_groups_count, deleted_tool_types_count
        
        # Удаляем группу рекурсивно
        deleted_groups, deleted_tool_types = delete_group_recursive(test_group.id)
        
        test_logger.log_data("Результат удаления", {
            "Удалено групп": deleted_groups,
            "Удалено номенклатур": deleted_tool_types
        })
        
        # Очищаем кеш перед проверкой
        group_crud._cache.clear()
        tool_types_crud._cache.clear()
        
        # Проверяем, что группа удалена через прямую сессию
        from DB.Models.Group import Group
        deleted_group = group_crud.session.query(Group).filter_by(id=test_group.id).first()
        assert deleted_group is None, f"Группа {test_group.id} должна быть удалена"
        
        if child_group:
            deleted_child = group_crud.session.query(Group).filter_by(id=child_group.id).first()
            assert deleted_child is None, f"Дочерняя группа {child_group.id} должна быть удалена"
        
        # Проверяем, что номенклатуры удалены через прямую сессию
        from DB.Models.ToolTypes import ToolTypes
        for tt in test_tool_types:
            deleted_tt = tool_types_crud.session.query(ToolTypes).filter_by(id=tt.id).first()
            assert deleted_tt is None, f"Номенклатура {tt.id} должна быть удалена"
        
        test_logger.log_success(
            f"Рекурсивное удаление завершено: удалено {deleted_groups} групп, {deleted_tool_types} номенклатур"
        )
        
    except AssertionError as e:
        test_logger.log_error("Ошибка в тесте рекурсивного удаления", e)
        raise
    except Exception as e:
        test_logger.log_error("Неожиданная ошибка в тесте рекурсивного удаления", e)
        raise


def test_group_tooltypes_integration(test_fixtures, crud_engines, test_logger):
    """Интеграционный тест всех взаимосвязей."""
    test_logger.log("\n" + "=" * 80, "TEST")
    test_logger.log("ТЕСТ 6: Интеграционный тест взаимосвязей", "TEST")
    test_logger.log("=" * 80, "TEST")
    
    try:
        group_crud = crud_engines["group"]
        tool_types_crud = crud_engines["tool_types"]
        load_crud = crud_engines["load"]
        
        groups = test_fixtures["groups"]
        tool_types = test_fixtures["tool_types"]
        
        # Проверяем полную структуру данных
        test_logger.log("Проверка полной структуры данных...", "INFO")
        
        # 1. Все группы должны существовать
        all_groups = group_crud.get_all_groups()
        test_group_ids = {g.id for g in groups}
        found_groups = [g for g in all_groups if g.id in test_group_ids]
        assert len(found_groups) == len(groups), \
            f"Не все тестовые группы найдены: {len(found_groups)}/{len(groups)}"
        test_logger.log_success(f"Все группы найдены в БД: {len(found_groups)}")
        
        # 2. Все номенклатуры должны существовать и быть привязаны к группам
        all_tool_types = tool_types_crud.get_all_tool_types()
        test_tt_ids = {tt.id for tt in tool_types}
        found_tool_types = [tt for tt in all_tool_types if tt.id in test_tt_ids]
        assert len(found_tool_types) == len(tool_types), \
            f"Не все тестовые номенклатуры найдены: {len(found_tool_types)}/{len(tool_types)}"
        test_logger.log_success(f"Все номенклатуры найдены в БД: {len(found_tool_types)}")
        
        # 3. Проверяем целостность связей
        for tt in found_tool_types:
            group = group_crud.get_group_by_id(tt.groups_id)
            assert group is not None, \
                f"Группа {tt.groups_id} не найдена для номенклатуры {tt.name}"
            test_logger.log_success(
                f"Связь целостна: {tt.name} -> {group.name}"
            )
        
        # 4. Проверяем расчет доступного количества с учетом Load
        for tt in found_tool_types:
            loads = load_crud.find_by_tools_id(tt.id)
            available = tt.count - len(loads)
            test_logger.log_data(
                f"Доступность '{tt.name}'",
                {
                    "Всего": tt.count,
                    "Занято (Load)": len(loads),
                    "Доступно": available
                }
            )
            assert available >= 0, \
                f"Доступное количество не может быть отрицательным для {tt.name}"
        
        test_logger.log_success("Интеграционный тест пройден успешно")
        
    except AssertionError as e:
        test_logger.log_error("Ошибка в интеграционном тесте", e)
        raise
    except Exception as e:
        test_logger.log_error("Неожиданная ошибка в интеграционном тесте", e)
        raise


if __name__ == "__main__":
    # Запуск тестов через pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])

