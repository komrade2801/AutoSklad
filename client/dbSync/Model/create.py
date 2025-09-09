import logging
import threading
from datetime import datetime

from dbSync.Engines.CommandEngine import CommandCRUD
from dbSync.Engines.CommandStatusEngine import CommandStatusCRUD
from dbSync.Engines.SyncConfigEngine import SyncConfigCRUD
from dbSync.Model.sync_sqlite import SyncSession
from dbSync.sync_db import init_sync_db


from DB.Models.Cell import Cell
# from DB.Models.CellHasDevice import CellHasDevice
# from DB.Models.Command import Command
from DB.Models.Consumption import Consumption
# from DB.Models.Device import Device
from DB.Models.Drop import Drop
from DB.Models.DropOperations import DropOperations
# from DB.Models.DropOperationsHasDevice import DropOperationsHasDevice
from DB.Models.Error import Error
# from DB.Models.ErrorHasDevice import ErrorHasDevice
from DB.Models.Group import Group
from DB.Models.Help import Help
from DB.Models.History import History
from DB.Models.Identification import Identification
from DB.Models.Load import Load
from DB.Models.LoadOperations import LoadOperations
# from DB.Models.LoadOperationsHasDevice import LoadOperationsHasDevice
from DB.Models.MassDrop import MassDrop
from DB.Models.MassLoad import MassLoad
# from DB.Models.MassDropHasDevice import MassDropHasDevice
# from DB.Models.MassLoadHasDevice import MassLoadHasDevice
from DB.Models.OperationsConsumption import OperationsConsumption
# from DB.Models.OperationsConsumptionHasDevice import OperationsConsumptionHasDevice
# from DB.Models.Page import Page
from DB.Models.Plan import Plan
# from DB.Models.ActualNorm import ActualNorm
# from DB.Models.ActualNormHasDevice import ActualNormHasDevice
from DB.Models.Rights import Rights
from DB.Models.Role import Role
from DB.Models.Status import Status
# from DB.Models.ToolLocation import ToolLocation
# from DB.Models.ToolTypes import ToolTypes
from DB.Models.Tools import Tools
# from DB.Models.ToolsHasDevice import ToolsHasDevice
# from DB.Models.ToolsNorm import ToolsNorm
# from DB.Models.Type import Type
from DB.Models.User import User

logger = logging.getLogger(__name__)

_PRIMARY_MODELS = [
    Cell, Consumption, Drop, DropOperations,
    Error, Group, Help, History,
    Identification, Load, LoadOperations, MassDrop,
    MassLoad, OperationsConsumption, Plan,
    Rights, Role, Status, Tools, User
]

def demo_status_lifecycle(command_id: int, crud: CommandStatusCRUD):
    """Демонстрация полного жизненного цикла статусов команды"""
    try:
        print(f"\nДемонстрация для команды {command_id}:")

        # Добавляем все возможные статусы по очереди
        statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]

        for status in statuses:
            crud.add_status(command_id, status)
            latest = crud.get_latest_for_command(command_id)
            print(f"Добавлен статус: {latest.status} ({latest.updated_at})")

    except ValueError as e:
        print(f"Ошибка добавления статуса: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")

def populate_sync_config() -> None:
    """
    Заполняет таблицу SyncConfig по умолчанию:
    создаёт запись для каждой таблицы основной БД из списка _PRIMARY_MODELS.
    Если запись уже есть — пропускает (чтобы не перезаписывать вручную выключенные флаги).
    """
    session = SyncSession()
    crud = SyncConfigCRUD(session=session)

    for model in _PRIMARY_MODELS:
        table = model.__tablename__
        current = crud.get_status(table)
        if current is None:
            # если в SyncConfig ещё нет этой таблицы — создаём запись enabled=True
            crud.enable_sync(table)
            print(f"[ПОТОК][{threading.current_thread().name}][create.py][populate_sync_config] Добавили таблицу: {table} [{datetime.now()}]")


if __name__ == "__main__":
    init_sync_db(force_recreate=True)
    # Создание CRUD-объекта INSERT INTO "main"."SyncConfig" ("table_name") VALUES ('Identification');
    status_crud = CommandStatusCRUD()
    # Создадим тестовые команды (предположим, что CommandCRUD существует)
    command_crud = CommandCRUD()
    test_command_id = command_crud.add(
        table_name="products",
        operation="UPDATE",
        device_number=5
    )
    id_command = max(command_crud.get_all_ids(), default=0)
    command = command_crud.get(id_command)
    demo_status_lifecycle(command.id, status_crud)
    populate_sync_config()

