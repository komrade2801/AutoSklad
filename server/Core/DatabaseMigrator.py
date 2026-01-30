import logging
from DB.Data.base import Base
from DB.Models.Cell import Cell #------------------------------------------------------------------------1

logger = logging.getLogger(__name__)
from DB.Models.CellHasDevice import CellHasDevice #------------------------------------------------------2
from DB.Models.Command import Command #------------------------------------------------------------------3
from DB.Models.Consumption import Consumption #----------------------------------------------------------4
from DB.Models.Device import Device #--------------------------------------------------------------------5
from DB.Models.Drop import Drop #------------------------------------------------------------------------6
from DB.Models.DropOperations import DropOperations #----------------------------------------------------7
from DB.Models.DropOperationsHasDevice import DropOperationsHasDevice #----------------------------------8
from DB.Models.Error import Error #----------------------------------------------------------------------9
from DB.Models.ErrorHasDevice import ErrorHasDevice #---------------------------------------------------10
from DB.Models.Group import Group #---------------------------------------------------------------------11
from DB.Models.Help import Help #-----------------------------------------------------------------------12
from DB.Models.History import History #-----------------------------------------------------------------13
from DB.Models.Identification import Identification #---------------------------------------------------14
from DB.Models.Load import Load #-----------------------------------------------------------------------15
from DB.Models.LoadOperations import LoadOperations #---------------------------------------------------16
from DB.Models.LoadOperationsHasDevice import LoadOperationsHasDevice #---------------------------------17
from DB.Models.MassDrop import MassDrop #---------------------------------------------------------------18
from DB.Models.MassLoad import MassLoad #---------------------------------------------------------------19
from DB.Models.MassDropHasDevice import MassDropHasDevice #---------------------------------------------20
from DB.Models.MassLoadHasDevice import MassLoadHasDevice #---------------------------------------------21
from DB.Models.OperationsConsumption import OperationsConsumption #-------------------------------------22
from DB.Models.OperationsConsumptionHasDevice import OperationsConsumptionHasDevice #-------------------23
from DB.Models.Plan import Plan #-----------------------------------------------------------------------24
from DB.Models.ActualNorm import ActualNorm #---------------------------------------------------------------------25
from DB.Models.ActualNormHasDevice import ActualNormHasDevice #---------------------------------------------------26
from DB.Models.Rights import Rights #-------------------------------------------------------------------27
from DB.Models.Role import Role #-----------------------------------------------------------------------28
from DB.Models.Status import Status #-------------------------------------------------------------------29
from DB.Models.ToolLocation import ToolLocation #-------------------------------------------------------30
from DB.Models.ToolTypes import ToolTypes
from DB.Models.Tools import Tools #---------------------------------------------------------------------31
from DB.Models.ToolsHasDevice import ToolsHasDevice #---------------------------------------------------32
from DB.Models.ToolsNorm import ToolsNorm #---------------------------------------------------------------33
from DB.Models.Type import Type #-----------------------------------------------------------------------34
from DB.Models.User import User #-----------------------------------------------------------------------35


from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import AddConstraint, DropConstraint, CreateTable, DropTable
from sqlalchemy.sql import text
import json
import os
from contextlib import contextmanager
from datetime import datetime

from options import db_path


class DatabaseMigrator:
    def __init__(self, base, models, db_url=f'sqlite:///{db_path}'):
        self.engine = create_engine(db_url)
        self.base = base
        self.models = models
        self.inspector = inspect(self.engine)
        self.backup_dir = "db_backups"

    @contextmanager
    def transaction(self):
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            yield connection
            transaction.commit()
        except Exception as e:
            transaction.rollback()
            raise e
        finally:
            connection.close()

    def create_backup(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        backup_data = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.json")

        with self.transaction() as conn:
            for table in self.base.metadata.tables.values():
                data = conn.execute(table.select()).fetchall()
                backup_data[table.name] = [dict(row) for row in data]

            with open(backup_file, 'w') as f:
                json.dump(backup_data, f)

        return backup_file

    def restore_backup(self, backup_file):
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)

        with self.transaction() as conn:
            for table_name, records in backup_data.items():
                if table_name in self.base.metadata.tables:
                    table = self.base.metadata.tables[table_name]
                    conn.execute(table.delete())
                    if records:
                        conn.execute(table.insert(), records)

    def safe_rebuild(self):
        backup_file = self.create_backup()

        try:
            with self.transaction() as conn:
                self._apply_schema_changes(conn)
            logger.info("Миграция успешно завершена")
        except Exception as e:
            logger.exception("Ошибка миграции: %s. Восстанавливаем backup...", e)
            self.restore_backup(backup_file)
            raise

    def _apply_schema_changes(self, connection):
        current_tables = set(self.inspector.get_table_names())
        metadata_tables = set(self.base.metadata.tables.keys())

        # Удаление устаревших таблиц
        for table_name in current_tables - metadata_tables:
            self._safe_drop_table(connection, table_name)

        # Создание новых таблиц
        for table in self.base.metadata.sorted_tables:
            if table.name not in current_tables:
                connection.execute(CreateTable(table))

        # Изменение существующих таблиц
        for table in self.base.metadata.sorted_tables:
            if table.name in current_tables:
                self._alter_existing_table(connection, table)

        # Применение ограничений
        self._apply_constraints(connection)

    def _safe_drop_table(self, connection, table_name):
        # Дополнительные проверки перед удалением
        if table_name.startswith('sqlite_'):
            return
        connection.execute(text(f'DROP TABLE IF EXISTS {table_name}'))

    def _alter_existing_table(self, connection, table):
        existing_columns = {col['name']: col for col
                            in self.inspector.get_columns(table.name)}

        # Добавление новых столбцов
        for column in table.columns:
            if column.name not in existing_columns:
                self._add_column(connection, table.name, column)

        # Удаление устаревших столбцов (только для не-SQLite)
        if 'sqlite' not in self.engine.url.drivername:
            for column_name in existing_columns:
                if column_name not in table.c:
                    self._drop_column(connection, table.name, column_name)

    def _add_column(self, connection, table_name, column):
        column_type = column.type.compile(self.engine.dialect)
        default = column.default.arg if column.default else ''
        nullable = 'NULL' if column.nullable else 'NOT NULL'

        query = text(
            f'ALTER TABLE {table_name} '
            f'ADD COLUMN {column.name} {column_type} {nullable} {default}'
        )
        connection.execute(query)

    def _apply_constraints(self, connection):
        # Реализация для ограничений (внешние ключи, индексы и т.д.)
        pass

    def _drop_column(self, connection, name, column_name):
        raise # TODO: Реализовать метод


def rebuild_db():
    modules = [
        # Ваши модели здесь
        Cell, CellHasDevice, Command, Consumption, Device, Drop,
        DropOperations, DropOperationsHasDevice, Error, ErrorHasDevice,
        Group, Help, History, Identification, Load, LoadOperations,
        LoadOperationsHasDevice, MassDrop, MassLoad, MassDropHasDevice,
        MassLoadHasDevice, OperationsConsumption,
        OperationsConsumptionHasDevice, Plan, ActualNorm, ActualNormHasDevice,
        Rights, Role, Status, ToolTypes, ToolLocation, Tools, ToolsHasDevice,
        ToolsNorm, Type, User
    ]

    migrator = DatabaseMigrator(Base, modules)

    try:
        migrator.safe_rebuild()
    except Exception as e:
        logger.exception("Критическая ошибка: %s", e)
        # Дополнительные действия при ошибке