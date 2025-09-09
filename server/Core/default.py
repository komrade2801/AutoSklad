#Core/default.py
import sys
from datetime import datetime
from pathlib import Path
from threading import RLock
from sqlalchemy import create_engine

from DB.Data import sqlite_db
from DB.Data.base import Base
import dbSync
from Core.Parser import HtmlTitleParser
from options import db_path, Host, port, AES_KEY, SENDER_TIMEOUT, RECEIVER_TIMEOUT
import json
import os

# Глобальное хранилище прогресса
progress_data = {
    "status": "idle",  # idle, in_progress, complete, error
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
        #
        # stages = [
        #     ("Creating tables", 20),
        #     ("Seeding data", 40),
        #     ("Generating indexes", 60),
        #     ("Optimizing", 80),
        #     ("Finalizing", 100)
        # ]

        # Запуск процессов
        rebuild_db()
        execute()

        update_progress("Setup complete", "complete", 100)
        progress_data["status"] = "complete"

    except Exception as e:
        update_progress(f"Setup failed: {str(e)}", "error", 0)
        progress_data["status"] = "error"


def rebuild_db():
    try:
        update_progress("Starting database rebuild", "rebuild", 0)
        # Закрываем все сессии
        from DB.Data.sqlite_db import get_engine
        get_engine().dispose(True)

        import psutil

        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                files = proc.info['open_files']
                if files:
                    for f in files:
                        if "web_vending.db" in f.path:
                            print(f"Process {proc.info['name']} PID {proc.info['pid']} держит файл {f.path}")
                            winsound.Beep(400, 300)  # Частота 1000 Гц, длительность 500 мс
                            winsound.Beep(600, 200)  # Частота 1000 Гц, длительность 500 мс
                            winsound.Beep(700, 400)  # Частота 1000 Гц, длительность 500 мс

                            sys.exit()

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Небольшая пауза для ОС
        import time
        time.sleep(0.1)

        # Ваш оригинальный код
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Получаем текущую директорию
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Один раз поднимаемся из Core в WEB
        web_dir = os.path.dirname(current_dir)
        # Формируем путь к DB/Data
        parent_dir = os.path.join(web_dir, "DB", "Data")
        db_filename = os.path.join(parent_dir, db_path)
        # Определите имя файла, который хотите удалить
        # Проверьте, существует ли файл
        if os.path.exists(db_filename):
            try:

                os.remove(db_filename)
                print(f"Файл '{db_filename}' был успешно удален.")
            except Exception as e:
                print(f"Ошибка при удалении файла: {e}")
        else:
            print(f"Файл '{db_filename}' не найден.")
        # Включение логирования SQLAlchemy
        # logging.basicConfig()
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

        # Создаем движок базы данных с использованием относительного пути
        # engine = create_engine(f'sqlite:///{db_path}')
        # Создаем файл и записываем в него пример данных
        try:
            with open(db_filename, 'w') as file:
                # Вы можете записывать строки в файл, используя метод write(), echo=True
                file.write('')
            print(f"Файл '{db_filename}' был успешно создан.")
        except Exception as e:
            print(f"Ошибка при создании файла: {e}")
        # Создание базы данных и таблиц

        # modules = [Help, Error, Role, Plan, Group, Rights, MassDrop, MassLoad, Status, User, Identification, Tools, Cell,
        #            Load, Drop, Consumption, History, DropOperations, OperationsConsumption, LoadOperations]
        # modules = [Cell, Error, Group, Help, History, Identification, Plan, Rights, Role, Tools, User, MassLoad, MassDrop,
        #            LoadOperations, OperationsConsumption, Drop, Status, Load, DropOperations, Consumption]

        from DB.Models.Cell import Cell  # ------------------------------------------------------------------------1
        from DB.Models.CellHasDevice import CellHasDevice  # ------------------------------------------------------2
        from DB.Models.Command import Command  # ------------------------------------------------------------------3
        from DB.Models.Consumption import Consumption  # ----------------------------------------------------------4
        from DB.Models.Device import Device  # --------------------------------------------------------------------5
        from DB.Models.Drop import Drop  # ------------------------------------------------------------------------6
        from DB.Models.DropOperations import DropOperations  # ----------------------------------------------------7
        from DB.Models.DropOperationsHasDevice import DropOperationsHasDevice  # ----------------------------------8
        from DB.Models.Error import Error  # ----------------------------------------------------------------------9
        from DB.Models.ErrorHasDevice import ErrorHasDevice  # ---------------------------------------------------10
        from DB.Models.Group import Group  # ---------------------------------------------------------------------11
        from DB.Models.Help import Help  # -----------------------------------------------------------------------12
        from DB.Models.History import History  # -----------------------------------------------------------------13
        from DB.Models.Identification import Identification  # ---------------------------------------------------14
        from DB.Models.Load import Load  # -----------------------------------------------------------------------15
        from DB.Models.LoadOperations import LoadOperations  # ---------------------------------------------------16
        from DB.Models.LoadOperationsHasDevice import LoadOperationsHasDevice  # ---------------------------------17
        from DB.Models.MassDrop import MassDrop  # ---------------------------------------------------------------18
        from DB.Models.MassLoad import MassLoad  # ---------------------------------------------------------------19
        from DB.Models.MassDropHasDevice import MassDropHasDevice  # ---------------------------------------------20
        from DB.Models.MassLoadHasDevice import MassLoadHasDevice  # ---------------------------------------------21
        from DB.Models.OperationsConsumption import OperationsConsumption  # -------------------------------------22
        from DB.Models.OperationsConsumptionHasDevice import OperationsConsumptionHasDevice  # -------------------23
        from DB.Models.Page import Page
        from DB.Models.Plan import Plan  # -----------------------------------------------------------------------24
        from DB.Models.ActualNorm import ActualNorm  # ---------------------------------------------------------------------25
        from DB.Models.ActualNormHasDevice import ActualNormHasDevice  # ---------------------------------------------------26
        from DB.Models.Rights import Rights  # -------------------------------------------------------------------27
        from DB.Models.Role import Role  # -----------------------------------------------------------------------28
        from DB.Models.Status import Status  # -------------------------------------------------------------------29
        from DB.Models.ToolLocation import ToolLocation  # -------------------------------------------------------30
        from DB.Models.ToolTypes import ToolTypes
        from DB.Models.Tools import Tools  # ---------------------------------------------------------------------31
        from DB.Models.ToolsHasDevice import ToolsHasDevice  # ---------------------------------------------------32
        from DB.Models.ToolsNorm import ToolsNorm  # ---------------------------------------------------------------33
        from DB.Models.Type import Type  # -----------------------------------------------------------------------34
        from DB.Models.User import User  # -----------------------------------------------------------------------35

        modules = [
            Cell, CellHasDevice, Command, Consumption, Device, Drop, DropOperations, DropOperationsHasDevice,
            Error, ErrorHasDevice, Group, Help, History, Identification, Load, LoadOperations,
            LoadOperationsHasDevice, MassDrop, MassLoad, MassDropHasDevice, MassLoadHasDevice,
            OperationsConsumption, OperationsConsumptionHasDevice, Plan, ActualNorm, ActualNormHasDevice, Rights,
            Role, Status, ToolTypes, ToolLocation, Tools, ToolsHasDevice, ToolsNorm, Type, User, Page
        ]

        engine = create_engine(f'sqlite:///{db_filename}')
        print(Base.metadata.tables.keys())
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)  # Создает все таблицы, описанные в Base
        engine.dispose(True)
        update_progress("Database rebuilt successfully", "rebuild", 100)

    except Exception as e:
        update_progress(f"Rebuild error: {str(e)}", "error", 0)
        raise


def to_serializable(obj):
    import base64

    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def execute():
    try:

        from DB.Engine.CellCRUD import EngineCell
        from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
        from DB.Engine.ConsumptionCRUD import EngineConsumption
        from DB.Engine.DeviceCRUD import EngineDevice
        from DB.Engine.DropCRUD import EngineDrop
        from DB.Engine.DropOperationsCRUD import EngineDropOperations
        from DB.Engine.DropOperationsHasDeviceCRUD import EngineDropOperationsHasDevice
        from DB.Engine.ErrorsCRUD import EngineError
        from DB.Engine.ErrorHasDeviceCRUD import EngineErrorHasDevice
        from DB.Engine.GroupCRUD import EngineGroup
        from DB.Engine.HelpCRUD import EngineHelp
        from DB.Engine.HistoryCRUD import EngineHistory
        from DB.Engine.IdentificationCRUD import EngineIdentification
        from DB.Engine.LoadCRUD import EngineLoad
        from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
        from DB.Engine.LoadOperationsHasDeviceCRUD import EngineLoadOperationsHasDevice
        from DB.Engine.MassDropCRUD import EngineMassDrop
        from DB.Engine.MassLoadCRUD import EngineMassLoad
        from DB.Engine.MassDropHasDeviceCRUD import EngineMassDropHasDevice
        from DB.Engine.MassLoadHasDeviceCRUD import EngineMassLoadHasDevice
        from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption
        from DB.Engine.OperationsConsumptionHasDeviceCRUD import EngineOperationsConsumptionHasDevice
        from DB.Engine.PlanCRUD import EnginePlan
        from DB.Engine.ActualNormCRUD import EngineActualNorm
        from DB.Engine.ActualNormHasDeviceCRUD import EngineActualNormHasDevice
        from DB.Engine.RightsCRUD import EngineRights
        from DB.Engine.RoleCRUD import EngineRole
        from DB.Engine.StatusCRUD import EngineStatus
        from DB.Engine.ToolLocationCRUD import EngineToolLocation
        from DB.Engine.ToolsCRUD import EngineTools
        from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
        from DB.Engine.ToolTypesCRUD import EngineToolTypes
        from DB.Engine.TypeCRUD import EngineType
        from DB.Engine.UserCRUD import EngineUser
        from DB.Engine.PageCRUD import EnginePage

        update_progress("Starting database population", "execute", 0)
        e_cell = EngineCell()
        e_cell_has_device = EngineCellHasDevice()
        # e_command = EngineCommand()
        e_consumption = EngineConsumption()
        e_device = EngineDevice()
        e_drop = EngineDrop()
        e_drop_operations = EngineDropOperations()
        e_drop_operations_has_device = EngineDropOperationsHasDevice()
        e_error = EngineError()
        e_error_has_device = EngineErrorHasDevice()
        e_group = EngineGroup()
        e_help = EngineHelp()
        e_history = EngineHistory()
        e_identification = EngineIdentification()
        e_load = EngineLoad()
        e_load_operations = EngineLoadOperations()
        e_load_operations_has_device = EngineLoadOperationsHasDevice()
        e_mass_drop = EngineMassDrop()
        e_mass_load = EngineMassLoad()
        e_mass_drop_has_device = EngineMassDropHasDevice()
        e_mass_load_has_device = EngineMassLoadHasDevice()
        e_operations_consumption = EngineOperationsConsumption()
        e_operations_consumption_has_device = EngineOperationsConsumptionHasDevice()
        e_plan = EnginePlan()
        e_actual_norm = EngineActualNorm()
        e_actual_norm_has_device = EngineActualNormHasDevice()
        e_rights = EngineRights()
        e_role = EngineRole()
        e_status = EngineStatus()
        e_tool_location = EngineToolLocation()
        e_tools = EngineTools()
        e_tools_has_device = EngineToolsHasDevice()
        e_tool_types = EngineToolTypes()
        e_type = EngineType()
        e_user = EngineUser()
        e_page = EnginePage()

        e_page.delete_all()
        e_cell.delete_all()
        e_cell_has_device.delete_all()
        # e_command.delete_all()
        e_consumption.delete_all()
        e_device.delete_all()
        e_drop.delete_all()
        e_drop_operations.delete_all()
        e_drop_operations_has_device.delete_all()
        e_error.delete_all()
        e_error_has_device.delete_all()
        e_group.delete_all()
        e_help.delete_all()
        e_history.delete_all()
        e_identification.delete_all()
        e_load.delete_all()
        e_load_operations.delete_all()
        e_load_operations_has_device.delete_all()
        e_mass_drop.delete_all()
        e_mass_load.delete_all()
        e_mass_drop_has_device.delete_all()
        e_mass_load_has_device.delete_all()
        e_operations_consumption.delete_all()
        e_operations_consumption_has_device.delete_all()
        e_plan.delete_all()
        e_actual_norm.delete_all()
        e_actual_norm_has_device.delete_all()
        e_rights.delete_all()
        e_role.delete_all()
        e_status.delete_all()
        e_tool_location.delete_all()
        e_tools.delete_all()
        e_tools_has_device.delete_all()
        e_tool_types.delete_all()
        e_type.delete_all()
        e_user.delete_all()

        update_progress("База данных создана!", "complete", 10)

        # определяем папку этого модуля
        BASE_DIR = Path(__file__).parent.parent
        PAGE_DIR = BASE_DIR / "frontend/page"

        # --- Инициализация страниц в БД и регистрация маршрутов ---
        # _pages_dir = os.path.join(os.path.dirname(__file__), "page")
        for file_name in os.listdir(PAGE_DIR):
            if file_name.startswith("screen") and file_name.endswith(".html"):
                # если нет в БД — создаём
                if not e_page.find_page(name=file_name):
                    # parser = HtmlTitleParser(f"../frontend/page/{file_name}")
                    parser = HtmlTitleParser(str(PAGE_DIR / file_name))
                    description = parser.get_title()
                    index = max(e_page.get_all_ids(), default=0) + 1
                    e_page.add_page(index=index, name=file_name, description=description)

        print("Страницы добавлены")
        update_progress("Страницы добавлены!", "complete", 11)

        date_str = '2025-02-18'
        # вариант 1: получить datetime.date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        index = max(e_device.get_all_ids(), default=0) + 1
        device_details = {
            "signature": {
                "serial_number": 1,
                "cells": {
                    "length": 210,
                    "columns": 35,
                    "rows": 6
                }
            },
            "server": {
                "ip": Host,
                "port": port,
                "token": "token11111",
                "secret": "",
                "aes": AES_KEY,
                "sender_timeout": SENDER_TIMEOUT,
                "receiver_timeout": RECEIVER_TIMEOUT
            },
            "network": {
                "ip": "192.168.101.93",
                "port": 8081
            },
            "serial": {
                "port": "COM29",
                "baudrate": "9600"
            },
            "barcode": {
                "port": "COM1",
                "baudrate": "9600"
            },
            "dev": {
                "ttyUSB": "/dev/ttyUSB0",
                "serial": "/dev/serial0"
            },
            "key": {
                "aes": ""
            },
            "locks": {
                "load_locked": 0,
                "drop_locked": 0
            },
            "logs": {
                "critical_errors": []
            }
        }
        details_json = json.dumps(device_details, indent=2, ensure_ascii=False, default=to_serializable)
        # details_json = json.dumps(device_details, indent=2, ensure_ascii=False)
        e_device.add_device(
            index=index,
            number=1,
            name="Основной вендинг",
            description="Главный цех",
            details=details_json,
            create=date_obj,
        )
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

        ids = e_device.get_all_ids()
        for index in ids:
            device = e_device.get_device_by_id(index)
            details = json.loads(device.details)
            signature = details["signature"]
            cells = signature["cells"]
            cell_length = cells["length"]
            number = 1
            for _ in range(0, cell_length):
                cell_id = max(e_cell.get_all_ids(), default=0) + 1
                e_cell.add_cell(
                    index=cell_id,
                    number=number,
                    tools_id=0,
                    status_id=0,
                    groups_id=0,
                    description='Старт',
                )
                e_cell_has_device.add_link(
                    device_id=index,
                    cell_id=cell_id
                )
                number += 1

                persent = ((number / cell_length) * 100)

                update_progress(f"Ячейка {number} из {cell_length} добавлена!", "complete", persent)

        roles_and_pages = {
            'Разработчик': ['Выдача инструмента', 'История операций', 'История ошибок', 'Выгрузка №', 'Выгрузка №', 'История выгрузок', 'Загрузка №', 'Загрузка №', 'История загрузок',
                            'Библиотека инструмента', 'Добавление инструмента', 'Генерация штрихкода', 'Настройка', 'Добавление пользователя', 'Все пользователи', 'Редактирование конфигурации',
                            'Информация', 'Все устройства', 'Добавление устройства', 'Массовая загрузка', 'Массовая выгрузка', 'Управление запасами', 'Списание инструмента', 'История списаний',
                            'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников'],
            'Кладовщик': ["История операций", "История ошибок", "История выгрузок", "История загрузок", "Библиотека инструмента", "Генерация штрих-кода", "Массовая загрузка", "Массовая выгрузка"],
            'Администратор': ['Все устройства', 'Добавление устройства', 'Редактирование конфигурации', 'Настройка', 'Все пользователи', 'Добавление пользователя', 'Информация', 'История ошибок',
                              'История загрузок', 'История выгрузок', 'История операций'],
            'Инженер': ['Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников', 'Все пользователи', 'Библиотека инструмента', 'Добавление инструмента', ],
            'Руководитель': ['Выдача инструмента', 'История операций', 'История ошибок', 'Выгрузка №', 'Выгрузка №', 'История выгрузок', 'Загрузка №', 'Загрузка №', 'История загрузок',
                             'Библиотека инструмента', 'Добавление инструмента', 'Генерация штрихкода', 'Настройка', 'Добавление пользователя', 'Все пользователи', 'Редактирование конфигурации',
                             'Информация', 'Все устройства', 'Добавление устройства', 'Массовая загрузка', 'Массовая выгрузка', 'Управление запасами', 'Списание инструмента', 'История списаний',
                             'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников'],
            'Пользователь': ['Выдача инструмента', 'Управление запасами', 'Списание инструмента', 'История списаний', ]
        }

        test_users = [
            {'barcode': 4850357853783, 'code': 1111, 'first_name': 'Максим', 'second_name': 'Кудрявцев', 'family': 'Single', 'password': 1111, 'role_id': 1},
            {'barcode': 5879166479259, 'code': 2222, 'first_name': 'Платон', 'second_name': 'Пестова', 'family': 'Single', 'password': 2222, 'role_id': 2},
            {'barcode': 4736941559234, 'code': 3333, 'first_name': 'Валерий', 'second_name': 'Комаров', 'family': 'Single', 'password': 3333, 'role_id': 3},
            {'barcode': 4589949233008, 'code': 4444, 'first_name': 'Милица', 'second_name': 'Устинова', 'family': 'Single', 'password': 4444, 'role_id': 4},
            {'barcode': 7185212918381, 'code': 5555, 'first_name': 'Михей', 'second_name': 'Никифорова', 'family': 'Single', 'password': 5555, 'role_id': 5},
            {'barcode': 2586362915568, 'code': 6666, 'first_name': 'Игнатий', 'second_name': 'Фомичев', 'family': 'Single', 'password': 6666, 'role_id': 6}
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

            role_id = max(e_role.get_all_ids(), default=0) + 1

            e_role.add_role(
                index=role_id,
                name=role_name,
                description="",
                parent_role_id=None
            )
            update_progress(f"Роль {role_name} добавлена", "complete", 95)
            page_stockman = roles_and_pages[role_name]

            role_id_max = max(e_role.get_all_ids())
            role = e_role.get_role_by_id(role_id_max)

            stockman_id = role.id
            page_stockman_ids = []

            pages = e_page.get_all_pages()
            for page in pages:
                if page.description in page_stockman:
                    page_stockman_ids.append(page.id)

            for page_id in page_stockman_ids:
                index = max(e_rights.get_all_ids(), default=0) + 1
                e_rights.add_right(
                    index=index,
                    name="разрешено",
                    role_id=stockman_id,
                    page_id=page_id,
                    description="",
                )
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
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)  # убедиться, что папка есть
    with CACHE_PATH.open('w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import winsound

    dbSync.init_db = True
    sqlite_db._engine = None
    rebuild_db()
    execute()
    dbSync.init_db = False
    clear_command_queue_cache()
    winsound.Beep(1000, 500)  # Частота 1000 Гц, длительность 500 мс
