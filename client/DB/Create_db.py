# DB/Create_db.py
import json
import time
import traceback
import dbSync
from DB.Data.sqlite_db import SessionLocal, engine
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.ConsumptionCRUD import EngineConsumption
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.DropOperationsCRUD import EngineDropOperations
from DB.Engine.ErrorsCRUD import EngineError
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.HelpCRUD import EngineHelp
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.IdentificationCRUD import EngineIdentification
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.MassDropCRUD import EngineMassDrop
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.RightsCRUD import EngineRights
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser
from DB.Models.Help import Help  # ----------------------------------- 1
from DB.Models.Error import Error  # --------------------------------- 2
from DB.Models.Role import Role  # ----------------------------------- 3
from DB.Models.Plan import Plan  # ----------------------------------- 4
from DB.Models.Group import Group  # --------------------------------- 5
from DB.Models.Rights import Rights  # ------------------------------- 6
from DB.Models.MassDrop import MassDrop  # --------------------------- 7
from DB.Models.MassLoad import MassLoad  # --------------------------- 8
from DB.Models.Status import Status  # ------------------------------- 9
from DB.Models.User import User  # ----------------------------------- 10
from DB.Models.Identification import Identification  # --------------- 11
from DB.Models.Tools import Tools  # --------------------------------- 12
from DB.Models.Cell import Cell  # ----------------------------------- 13
from DB.Models.Load import Load  # ----------------------------------- 14
from DB.Models.Drop import Drop  # ----------------------------------- 15
from DB.Models.Consumption import Consumption  # --------------------- 16
from DB.Models.History import History  # ----------------------------- 17
from DB.Models.DropOperations import DropOperations  # --------------- 18
from DB.Models.OperationsConsumption import OperationsConsumption  # - 19
from DB.Models.LoadOperations import LoadOperations  # --------------- 20
from DB.Models.ToolTypes import ToolTypes  # ---------------- 21
from sqlalchemy import create_engine
from DB.Data.base import Base
import os
from datetime import datetime
from pathlib import Path
from threading import RLock

from config import config_path, db_path

# Глобальное хранилище прогресса
progress_data = {
    "status": "idle",
    "messages": [],
    "current_stage": "",
    "percentage": 0
}
progress_lock = RLock()


def update_progress(message: str = None, stage: str = None, percentage: int = 0):
    with progress_lock:
        if stage:
            progress_data["current_stage"] = stage
        if message:
            progress_data["messages"].append(message)
        if percentage >= 0:
            progress_data["percentage"] = percentage


def run_setup_process():
    try:
        update_progress("Starting full setup", "init", 0)
        progress_data["status"] = "in_progress"

        rebuild_db()
        execute()

        update_progress("Setup complete", "complete", 100)
        progress_data["status"] = "complete"

    except Exception as e:
        update_progress(f"Setup failed: {str(e)}", "error", 0)
        progress_data["status"] = "error"


def rebuild_db():
    # 1) Determine the module folder and path to DB/Data
    current_dir = os.path.dirname(
        os.path.abspath(__file__))      # .../Vending/DB
    project_root = os.path.dirname(
        current_dir)                    # .../Vending
    # .../Vending/DB/Data
    data_dir = os.path.join(project_root, "DB", "Data")

    # 2) Ensure that the directory exists
    os.makedirs(data_dir, exist_ok=True)

    # 3) Build the full path to the database file
    db_filename = os.path.join(data_dir, db_path)

    # 4) Small pause to let the OS release any locks
    time.sleep(0.1)

    # 5) Remove the old file if it exists
    if os.path.exists(db_filename):
        try:
            os.remove(db_filename)
            print(f"Database file removed: {db_filename}")
        except Exception as e:
            print(f"Error removing database file: {e}")
            print(traceback.format_exc())
    else:
        print(
            f"No existing database file found; creating new one at: {db_filename}")

    # 6) Create an empty file
    try:
        open(db_filename, "w").close()
        print(f"Database file created: {db_filename}")
    except Exception as e:
        print(f"Error creating database file: {e}")
        print(traceback.format_exc())
        return

    # 7) Connect to SQLite and create tables
    engine = create_engine(f"sqlite:///{db_filename}")
    try:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        print("All tables have been successfully (re)created.")
    except Exception as e:
        print(f"Error during (re)creation of tables: {e}")
        print(traceback.format_exc())
    finally:
        engine.dispose()


def execute():
    try:

        update_progress("Starting database population", "execute", 0)
        e_cell = EngineCell(SessionLocal(engine()))
        e_consumption = EngineConsumption(SessionLocal(engine()))
        e_drop = EngineDrop(SessionLocal(engine()))
        e_drop_operations = EngineDropOperations(SessionLocal(engine()))
        e_error = EngineError(SessionLocal(engine()))
        e_group = EngineGroup(SessionLocal(engine()))
        e_help = EngineHelp(SessionLocal(engine()))
        e_history = EngineHistory(SessionLocal(engine()))
        e_identification = EngineIdentification(SessionLocal(engine()))
        e_load = EngineLoad(SessionLocal(engine()))
        e_load_operations = EngineLoadOperations(SessionLocal(engine()))
        e_mass_drop = EngineMassDrop(SessionLocal(engine()))
        e_mass_load = EngineMassLoad(SessionLocal(engine()))
        e_operations_consumption = EngineOperationsConsumption(
            SessionLocal(engine()))
        e_plan = EnginePlan(SessionLocal(engine()))
        e_rights = EngineRights(SessionLocal(engine()))
        e_role = EngineRole(SessionLocal(engine()))
        e_status = EngineStatus(SessionLocal(engine()))
        e_tools = EngineTools(SessionLocal(engine()))
        e_user = EngineUser(SessionLocal(engine()))
        e_cell.delete_all()
        e_consumption.delete_all()
        e_drop.delete_all()
        e_drop_operations.delete_all()
        e_error.delete_all()
        e_group.delete_all()
        e_help.delete_all()
        e_history.delete_all()
        e_identification.delete_all()
        e_load.delete_all()
        e_load_operations.delete_all()
        e_mass_drop.delete_all()
        e_mass_load.delete_all()
        e_operations_consumption.delete_all()
        e_plan.delete_all()
        e_rights.delete_all()
        e_role.delete_all()
        e_status.delete_all()
        e_tools.delete_all()
        e_user.delete_all()

        update_progress("База данных создана!", "complete", 10)

        # определяем папку этого модуля
        BASE_DIR = Path(__file__).parent.parent
        PAGE_DIR = BASE_DIR / "frontend/page"

        update_progress("Страницы добавлены!", "complete", 11)
        date_str = '2025-02-18'
        # вариант 1: получить datetime.date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        print("Устройство добавлено")
        update_progress("Устройство добавлено!", "complete", 12)
        status_names = [
            "start_system",
            "mass_drop_ready",
            "mass_load_ready",
            "mass_drop_init",
            "mass_load_init",
            "drop_ready",
            "load_ready",
        ]
        status_description = [
            "Инициализация системы!",
            "Инструмент извлечён из аппарата",
            "Инструмент готов к выдаче",
            "Объявлена массовая выгрузка",
            "Объявлена массовая загрузка",
            "Инструмент извлечён из аппарата",
            "Инструмент готов к выдаче",
        ]
        for key, name in enumerate(status_names):
            status = e_status.find_by_name(name)
            if not status:
                index = max(e_status.get_all_ids(), default=0) + 1
                e_status.add(
                    index=index,
                    stype=name,
                    description=status_description[key]
                )

        update_progress("Статусы добавлены!", "complete", 13)

        with open(config_path, encoding='utf-8', mode='r') as file:
            details = json.load(file)
            signature = details["signature"]
            cells = signature["cells"]
            cell_length = cells["length"]
            number = 1
            for _ in range(0, cell_length):
                index = max(e_cell.get_all_ids(), default=0) + 1
                e_cell.add_cell(
                    index=index,
                    number=number,
                    tools_id=0,
                    status_id=0,
                    groups_id=0,
                    description='Старт',
                )

                number += 1

                persent = ((number / cell_length) * 100)

                update_progress(
                    f"Ячейка {number} из {cell_length} добавлена!", "complete", persent)

        roles_and_pages = {
            'Developer': ['Выдача инструмента', 'История операций', 'История ошибок', 'Выгрузка №', 'Выгрузка №', 'История выгрузок', 'Загрузка №', 'Загрузка №', 'История загрузок',
                          'Библиотека инструмента', 'Добавление инструмента', 'Генерация штрихкода', 'Настройка', 'Добавление пользователя', 'Все пользователи', 'Редактирование конфигурации',
                          'Информация', 'Все устройства', 'Добавление устройства', 'Массовая загрузка', 'Массовая выгрузка', 'Управление запасами', 'Списание инструмента', 'История списаний',
                          'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников'],
            'Stockman': ["История операций", "История ошибок", "История выгрузок", "История загрузок", "Библиотека инструмента", "Генерация штрих-кода", "Массовая загрузка", "Массовая выгрузка"],
            'Admin': ['Все устройства', 'Добавление устройства', 'Редактирование конфигурации', 'Настройка', 'Все пользователи', 'Добавление пользователя', 'Информация', 'История ошибок',
                      'История загрузок', 'История выгрузок', 'История операций'],
            'Engineer': ['Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников', 'Все пользователи', 'Библиотека инструмента', 'Добавление инструмента', ],
            'Manager': ['Выдача инструмента', 'История операций', 'История ошибок', 'Выгрузка №', 'Выгрузка №', 'История выгрузок', 'Загрузка №', 'Загрузка №', 'История загрузок',
                        'Библиотека инструмента', 'Добавление инструмента', 'Генерация штрихкода', 'Настройка', 'Добавление пользователя', 'Все пользователи', 'Редактирование конфигурации',
                        'Информация', 'Все устройства', 'Добавление устройства', 'Массовая загрузка', 'Массовая выгрузка', 'Управление запасами', 'Списание инструмента', 'История списаний',
                        'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников'],
            'User': ['Выдача инструмента', 'Управление запасами', 'Списание инструмента', 'История списаний', ]
        }

        test_users = [
            {'barcode': 4850357853783, 'code': 1111, 'first_name': 'Максим',
                'second_name': 'Кудрявцев', 'family': 'Иванов', 'password': 1111, 'role_id': 1},
            {'barcode': 5879166479259, 'code': 2222, 'first_name': 'Платон',
                'second_name': 'Пестова', 'family': 'Игоревна', 'password': 2222, 'role_id': 2},
            {'barcode': 4736941559234, 'code': 3333, 'first_name': 'Валерий',
                'second_name': 'Комаров', 'family': 'Александрович', 'password': 3333, 'role_id': 3},
            {'barcode': 4589949233008, 'code': 4444, 'first_name': 'Милица',
                'second_name': 'Устинова', 'family': 'Максимовна', 'password': 4444, 'role_id': 4},
            {'barcode': 7185212918381, 'code': 5555, 'first_name': 'Михей',
                'second_name': 'Никифорова', 'family': 'Дмитриевна', 'password': 5555, 'role_id': 5},
            {'barcode': 2586362915568, 'code': 6666, 'first_name': 'Игнатий',
                'second_name': 'Фомичев', 'family': 'Дмитриевна', 'password': 6666, 'role_id': 6}
        ]

        for user in test_users:
            index = max(e_user.get_all_ids(), default=0) + 1
            e_user.add_user(
                index=index,
                barcode=user['barcode'],
                code=user['code'],
                first_name=user['first_name'],
                second_name=user['second_name'],
                family=user['family'],
                password=user['password'],
                role_id=user['role_id'],
            )

        update_progress("Пользователи добавлены", "complete", 90)

        for role_name in roles_and_pages:
            update_progress(f"Роль {role_name} добавлена", "complete", 95)

            e_role.add_role(
                name=role_name,
                description="",
                parent_role_id=None
            )
            page_stockman = roles_and_pages[role_name]

            role_id_max = max(e_role.get_all_ids())
            role = e_role.get_role_by_id(role_id_max)
            update_progress("Database populated", "execute", 100)

    except Exception as e:
        update_progress(f"Population error: {str(e)}", "error", 0)
        raise


CACHE_PATH = Path(__file__).parent.parent / 'command_queue.json'


def clear_command_queue_cache():
    """
    Очищает файл command_queue.json, записывая в него пустой список.
    Если файла нет — создаёт его.
    """
    CACHE_PATH.parent.mkdir(
        parents=True, exist_ok=True)  # убедиться, что папка есть
    with CACHE_PATH.open('w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    clear_command_queue_cache()
    dbSync.init_db = True
    rebuild_db()
    execute()
    dbSync.init_db = False
