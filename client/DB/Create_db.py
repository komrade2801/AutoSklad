# import logging
# import pkgutil
# from sqlalchemy import create_engine
# import importlib
# import os
# from sqlalchemy.orm import sessionmaker
# from DB.Models.Tables import Error
# from DB.Models.Tables import Help
# from DB.Models.Tables import Role
# from DB.Models.Tables import Rights
# from DB.Models.Tables import User
# from DB.Models.Tables import Identification
# from DB.Models.Tables import Plan
# from DB.Models.Tables import Group
# from DB.Models.Tables import Tools
# from DB.Models.Tables import History
# from DB.Models.Tables import Cell
# from DB.Models.Tables import MassLoad
# from DB.Models.Tables import MassDrop
# from DB.Models.Tables import LoadOperations
# from DB.Models.Tables import OperationsConsumption
# from DB.Models.Tables import Drop
# from DB.Models.Tables import Status
# from DB.Models.Tables import Load
# from DB.Models.Tables import DropOperations
# from DB.Models.Tables import Consumption
# Определите имя файла, который хотите удалить
# # Проверьте, существует ли файл
# if os.path.exists(db_path):
#     try:
#         os.remove(db_path)
#         print(f"Файл '{db_path}' был успешно удален.")
#     except Exception as e:
#         print(f"Ошибка при удалении файла: {e}")
# else:
#     print(f"Файл '{db_path}' не найден.")
#
# # Создаем файл и записываем в него пример данных
# try:
#     with open(db_path, 'w') as file:
#         # Вы можете записывать строки в файл, используя метод write()
#         file.write('')
#     print(f"Файл '{db_path}' был успешно создан.")
# except Exception as e:
#     print(f"Ошибка при создании файла: {e}")
import json
import traceback

import dbSync
from DB.Data.sqlite_db import SessionLocal, engine
# from Core.Parser import HtmlTitleParser
from DB.Engine.CellCRUD import EngineCell
# from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
# from dbSync.Engines.CRUD import EngineCommand
from DB.Engine.ConsumptionCRUD import EngineConsumption
# from DB.Engine.DeviceCRUD import EngineDevice
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.DropOperationsCRUD import EngineDropOperations
# from DB.Engine.DropOperationsHasDeviceCRUD import EngineDropOperationsHasDevice
from DB.Engine.ErrorsCRUD import EngineError
# from DB.Engine.ErrorHasDeviceCRUD import EngineErrorHasDevice
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.HelpCRUD import EngineHelp
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.IdentificationCRUD import EngineIdentification
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
# from DB.Engine.LoadOperationsHasDeviceCRUD import EngineLoadOperationsHasDevice
from DB.Engine.MassDropCRUD import EngineMassDrop
from DB.Engine.MassLoadCRUD import EngineMassLoad
# from DB.Engine.MassDropHasDeviceCRUD import EngineMassDropHasDevice
# from DB.Engine.MassLoadHasDeviceCRUD import EngineMassLoadHasDevice
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption
# from DB.Engine.OperationsConsumptionHasDeviceCRUD import EngineOperationsConsumptionHasDevice
from DB.Engine.PlanCRUD import EnginePlan
# from DB.Engine.ActualNormCRUD import EngineActualNorm
# from DB.Engine.ActualNormHasDeviceCRUD import EngineActualNormHasDevice
from DB.Engine.RightsCRUD import EngineRights
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.StatusCRUD import EngineStatus
# from DB.Engine.ToolLocationCRUD import EngineToolLocation
from DB.Engine.ToolsCRUD import EngineTools
# from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice
# from DB.Engine.ToolTypesCRUD import EngineToolTypes
# from DB.Engine.TypeCRUD import EngineType
from DB.Engine.UserCRUD import EngineUser
# from DB.Engine.PageCRUD import EnginePage

# Включение логирования SQLAlchemy
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# modules = [Cell, Error, Group, Help, History, Identification, Plan, Rights, Role, Tools, User, MassLoad, MassDrop,
#            LoadOperations, OperationsConsumption, Drop, Status, Load, DropOperations, Consumption]
#
# # Создание базы данных и таблиц
# engine = create_engine(f'sqlite:///{db_path}')
# print(Base.metadata.tables.keys())
# Base.metadata.create_all(engine)  # Создает все таблицы, описанные в Base

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
from sqlalchemy import create_engine
from DB.Data.base import Base
import os
# from config import config_path
from datetime import datetime
from pathlib import Path
from threading import RLock

from config import config_path, db_path

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
    modules = [Help, Error, Role, Plan, Group, Rights, MassDrop, MassLoad, Status, User, Identification, Tools, Cell,
               Load, Drop, Consumption, History, DropOperations, OperationsConsumption, LoadOperations]
    # modules = [Cell, Error, Group, Help, History, Identification, Plan, Rights, Role, Tools, User, MassLoad, MassDrop,
    #            LoadOperations, OperationsConsumption, Drop, Status, Load, DropOperations, Consumption]

    # Получаем текущую директорию
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Определяем путь к родительской директории  os.path.dirname()
    parent_dir = current_dir + "\\" + "Data"
    # Формируем полный путь к базе данных в родительской директории
    db_filename = os.path.join(parent_dir, db_path)

    # Определите имя файла, который хотите удалить
    # Проверьте, существует ли файл
    if os.path.exists(db_filename):
        try:
            os.remove(db_filename)
            print(f"Файл '{db_filename}' был успешно удален.")
        except Exception as e:
            print(f"Ошибка при удалении файла: {e}")
            print(traceback.format_exc())

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
        print(traceback.format_exc())

    # Создание базы данных и таблиц
    engine = create_engine(f'sqlite:///{db_filename}')
    print(Base.metadata.tables.keys())
    Base.metadata.create_all(engine)  # Создает все таблицы, описанные в Base


def execute():
    try:

        update_progress("Starting database population", "execute", 0)
        e_cell = EngineCell(SessionLocal(engine()))
        # e_cell_has_device = EngineCellHasDevice(SessionLocal(engine()))
        # e_command = EngineCommand(SessionLocal(engine()))
        e_consumption = EngineConsumption(SessionLocal(engine()))
        # e_device = EngineDevice(SessionLocal(engine()))
        e_drop = EngineDrop(SessionLocal(engine()))
        e_drop_operations = EngineDropOperations(SessionLocal(engine()))
        # e_drop_operations_has_device = EngineDropOperationsHasDevice(SessionLocal(engine()))
        e_error = EngineError(SessionLocal(engine()))
        # e_error_has_device = EngineErrorHasDevice(SessionLocal(engine()))
        e_group = EngineGroup(SessionLocal(engine()))
        e_help = EngineHelp(SessionLocal(engine()))
        e_history = EngineHistory(SessionLocal(engine()))
        e_identification = EngineIdentification(SessionLocal(engine()))
        e_load = EngineLoad(SessionLocal(engine()))
        e_load_operations = EngineLoadOperations(SessionLocal(engine()))
        # e_load_operations_has_device = EngineLoadOperationsHasDevice(SessionLocal(engine()))
        e_mass_drop = EngineMassDrop(SessionLocal(engine()))
        e_mass_load = EngineMassLoad(SessionLocal(engine()))
        # e_mass_drop_has_device = EngineMassDropHasDevice(SessionLocal(engine()))
        # e_mass_load_has_device = EngineMassLoadHasDevice(SessionLocal(engine()))
        e_operations_consumption = EngineOperationsConsumption(SessionLocal(engine()))
        # e_operations_consumption_has_device = EngineOperationsConsumptionHasDevice(SessionLocal(engine()))
        e_plan = EnginePlan(SessionLocal(engine()))
        # e_actual_norm = EngineActualNorm(SessionLocal(engine()))
        # e_actual_norm_has_device = EngineActualNormHasDevice(SessionLocal(engine()))
        e_rights = EngineRights(SessionLocal(engine()))
        e_role = EngineRole(SessionLocal(engine()))
        e_status = EngineStatus(SessionLocal(engine()))
        # e_tool_location = EngineToolLocation(SessionLocal(engine()))
        e_tools = EngineTools(SessionLocal(engine()))
        # e_tools_has_device = EngineToolsHasDevice(SessionLocal(engine()))
        # e_tool_types = EngineToolTypes(SessionLocal(engine()))
        # e_type = EngineType(SessionLocal(engine()))
        e_user = EngineUser(SessionLocal(engine()))
        # e_page = EnginePage(SessionLocal(engine()))

        # e_page.delete_all()
        e_cell.delete_all()
        # e_cell_has_device.delete_all()
        # e_command.delete_all()
        e_consumption.delete_all()
        # e_device.delete_all()
        e_drop.delete_all()
        e_drop_operations.delete_all()
        # e_drop_operations_has_device.delete_all()
        e_error.delete_all()
        # e_error_has_device.delete_all()
        e_group.delete_all()
        e_help.delete_all()
        e_history.delete_all()
        e_identification.delete_all()
        e_load.delete_all()
        e_load_operations.delete_all()
        # e_load_operations_has_device.delete_all()
        e_mass_drop.delete_all()
        e_mass_load.delete_all()
        # e_mass_drop_has_device.delete_all()
        # e_mass_load_has_device.delete_all()
        e_operations_consumption.delete_all()
        # e_operations_consumption_has_device.delete_all()
        e_plan.delete_all()
        # e_actual_norm.delete_all()
        # e_actual_norm_has_device.delete_all()
        e_rights.delete_all()
        e_role.delete_all()
        e_status.delete_all()
        # e_tool_location.delete_all()
        e_tools.delete_all()
        # e_tools_has_device.delete_all()
        # e_tool_types.delete_all()
        # e_type.delete_all()
        e_user.delete_all()

        update_progress("База данных создана!", "complete", 10)

        # определяем папку этого модуля
        BASE_DIR = Path(__file__).parent.parent
        PAGE_DIR = BASE_DIR / "frontend/page"

        # --- Инициализация страниц в БД и регистрация маршрутов ---
        # _pages_dir = os.path.join(os.path.dirname(__file__), "page")
        # for file_name in os.listdir(PAGE_DIR):
        #     if file_name.startswith("screen") and file_name.endswith(".html"):
        #         # если нет в БД — создаём
        #         if not e_page.find_page(name=file_name):
        #             # parser = HtmlTitleParser(f"../frontend/page/{file_name}")
        #             parser = HtmlTitleParser(str(PAGE_DIR / file_name))
        #             description = parser.get_title()
        #             e_page.add_page(name=file_name, description=description)

        #  print("Страницы добавлены")
        update_progress("Страницы добавлены!", "complete", 11)
        """
            id	    number	    name	                description	        details	                        create
            1	    1	        Основной вендинг	    Главный цех	        {                               2025-02-18                
                                                                              "signature": {
                                                                                "serial_number": 1,
                                                                                "cells": {
                                                                                  "length": 150,
                                                                                  "columns": 10,
                                                                                  "rows": 15
                                                                                }
                                                                              },
                                                                              "server":{
                                                                                "ip": "192.168.5.70",
                                                                                "port": 80,
                                                                                "token": "token11111",
                                                                                "secret": "g\\xa8\\xc9\\x04H\\xf0F\\xe1\\xfb\\xb6J\\xbc\\xae\\xfaP\\xec'\\x08\\xcb\\xa1\\xfc\\xbe\\xea\\x96'",
                                                                                "aes": "16byteslongkey!!",
                                                                                "sender_timeout": "30",
                                                                                "receiver_timeout": "60"
                                                                              },
                                                                              "network": {
                                                                                "ip": "192.168.5.70",
                                                                                "port": 81
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
                                                                                "key":{
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
        """
        date_str = '2025-02-18'
        # вариант 1: получить datetime.date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # e_device.add_device(
        #     number=1,
        #     name="Основной вендинг",
        #     description="Главный цех",
        #     details='''{
        #       "signature": {
        #         "serial_number": 1,
        #         "cells": {
        #           "length": 1024,
        #           "columns": 32,
        #           "rows": 32
        #         }
        #       },
        #       "network": {
        #         "ip": "192.168.0.10",
        #         "port": 8080
        #       },
        #       "serial": {
        #         "port": "COM1",
        #         "baudrate": 9600
        #       },
        #       "barcode": {
        #         "port": "COM1",
        #         "baudrate": 9600
        #       },
        #       "locks": {
        #         "load_locked": 0,
        #         "drop_locked": 0
        #       },
        #       "logs": {
        #         "critical_errors": []
        #       }
        #     }''',
        #     create=date_obj,
        # )
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
            "Инициализирована массовая загрузка",
            "Инициализирована массовая выгрузка",
            "Инструмент по массовой загрузке загружен в аппарат",
            "Инструмент по массовой выгрузки извлечён из аппарата",
            "Инструмент по массовой загрузке загружен в аппарат",
            "Инструмент по массовой выгрузки извлечён из аппарата",
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
                # e_cell_has_device.add_link(
                #     device_id=index,
                #     cell_id=index
                # )
                number += 1

                persent = ((number/cell_length) * 100)

                update_progress(f"Ячейка {number} из {cell_length} добавлена!", "complete", persent)

        roles_and_pages = {
            'Developer':[ 'Выдача инструмента', 'История операций', 'История ошибок', 'Выгрузка №', 'Выгрузка №', 'История выгрузок', 'Загрузка №', 'Загрузка №', 'История загрузок', 'Библиотека инструмента', 'Добавление инструмента', 'Генерация штрихкода', 'Настройка', 'Добавление пользователя', 'Все пользователи', 'Редактирование конфигурации', 'Информация', 'Все устройства', 'Добавление устройства', 'Массовая загрузка', 'Массовая выгрузка', 'Управление запасами', 'Списание инструмента', 'История списаний', 'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников'],
            'Stockman': [ "История операций", "История ошибок", "История выгрузок", "История загрузок", "Библиотека инструмента", "Генерация штрих-кода", "Массовая загрузка", "Массовая выгрузка" ],
            'Admin': [ 'Все устройства', 'Добавление устройства', 'Редактирование конфигурации', 'Настройка', 'Все пользователи', 'Добавление пользователя', 'Информация', 'История ошибок', 'История загрузок', 'История выгрузок', 'История операций'],
            'Engineer': [ 'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников', 'Все пользователи', 'Библиотека инструмента', 'Добавление инструмента', ],
            'Manager': [ 'Выдача инструмента', 'История операций', 'История ошибок', 'Выгрузка №', 'Выгрузка №', 'История выгрузок', 'Загрузка №', 'Загрузка №', 'История загрузок', 'Библиотека инструмента', 'Добавление инструмента', 'Генерация штрихкода', 'Настройка', 'Добавление пользователя', 'Все пользователи', 'Редактирование конфигурации', 'Информация', 'Все устройства', 'Добавление устройства', 'Массовая загрузка', 'Массовая выгрузка', 'Управление запасами', 'Списание инструмента', 'История списаний', 'Все чертежи', 'Добавление чертежа', 'Добавление нормы', 'Актуальные нормы сотрудников'],
            'User': [ 'Выдача инструмента','Управление запасами', 'Списание инструмента', 'История списаний',]
        }

        test_users = [
            {'barcode': 4850357853783, 'code': 1111, 'first_name': 'Максим', 'second_name': 'Кудрявцев',  'family': 'Single',  'password': 1111, 'role_id': 1},
            {'barcode': 5879166479259, 'code': 2222, 'first_name': 'Платон', 'second_name': 'Пестова',    'family': 'Single',  'password': 2222, 'role_id': 2},
            {'barcode': 4736941559234, 'code': 3333, 'first_name': 'Валерий','second_name': 'Комаров',    'family': 'Single',  'password': 3333, 'role_id': 3},
            {'barcode': 4589949233008, 'code': 4444, 'first_name': 'Милица', 'second_name': 'Устинова',   'family': 'Single',  'password': 4444, 'role_id': 4},
            {'barcode': 7185212918381, 'code': 5555, 'first_name': 'Михей',  'second_name': 'Никифорова', 'family': 'Single',  'password': 5555, 'role_id': 5},
            {'barcode': 2586362915568, 'code': 6666, 'first_name': 'Игнатий','second_name': 'Фомичев',    'family': 'Single',  'password': 6666, 'role_id': 6}
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

            # stockman_id = role.id
            # page_stockman_ids = []
            #
            # pages = e_page.get_all_pages()
            # for page in pages:
            #     if page.description in page_stockman:
            #         page_stockman_ids.append(page.id)

            # for index in page_stockman_ids:
            #     e_rights.add_right(
            #         name="разрешено",
            #         role_id=stockman_id,
            #         page_id=index,
            #         description="",
            #     )

            update_progress("Database populated", "execute", 100)

    except Exception as e:
        update_progress(f"Population error: {str(e)}", "error", 0)
        raise


if __name__ == "__main__":
    dbSync.init_db = True
    rebuild_db()
    execute()
    dbSync.init_db = False
