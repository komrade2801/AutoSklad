import datetime
import traceback
from typing import List, Optional, Type
import dbSync
# ----------------------------------- 1
from DB.Engine.HelpCRUD import EngineHelp
# -------------------------------- 2
from DB.Engine.ErrorsCRUD import EngineError
# ----------------------------------- 3
from DB.Engine.RoleCRUD import EngineRole
# ----------------------------------- 4
from DB.Engine.PlanCRUD import EnginePlan
# --------------------------------- 5
from DB.Engine.GroupCRUD import EngineGroup
# ------------------------------- 6
from DB.Engine.RightsCRUD import EngineRights
from DB.Engine.MassDropCRUD import EngineMassDrop  # --------------------------- 7
from DB.Engine.MassLoadCRUD import EngineMassLoad  # --------------------------- 8
# ------------------------------- 9
from DB.Engine.StatusCRUD import EngineStatus
# ----------------------------------- 10
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.IdentificationCRUD import EngineIdentification  # --------------- 11
# --------------------------------- 12
from DB.Engine.ToolsCRUD import EngineTools
# ----------------------------------- 13
from DB.Engine.CellCRUD import EngineCell
# ----------------------------------- 14
from DB.Engine.LoadCRUD import EngineLoad
# ----------------------------------- 15
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.ConsumptionCRUD import EngineConsumption  # --------------------- 16
# ----------------------------- 17
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.DropOperationsCRUD import EngineDropOperations  # --------------- 18
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption  # - 19
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations  # --------------- 20
from DB.Data.db import SessionLocal
from DB.Data.db import engine
import logging
from DB.Models.Cell import Cell
from DB.Models.LoadOperations import LoadOperations
from DB.Models.MassDrop import MassDrop
from DB.Models.OperationsConsumption import OperationsConsumption
from DB.Models.Tools import Tools
from DB.Models.User import User


class MassDropToolPlanIDNoneError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class MassDropPlanIdEQToolsError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class MassDropLenEqCellToolsError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class MassLoadLenEqCellToolsError(Exception):
    """Пользовательское исключение для специфичных ошибок."""

    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class MassLoadToolPlanIDError(Exception):
    """Пользовательское исключение для специфичных ошибок."""

    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class MassLoadToolPlanIDNoneError(Exception):
    """Пользовательское исключение для специфичных ошибок."""

    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class MassLoadPlanIdEQToolsError(Exception):
    """Пользовательское исключение для специфичных ошибок."""

    def __init__(self, message):
        super().__init__(message)

    def logger(self, message):
        logging.error(f"Ошибка: {message}")


class ActionMapper:
    def __init__(self, executor):
        # Определите имя файла базы данных self.db_path
        # Проверьте, существует ли файл
        self.__executor = executor
        # Определяем карту активности, используя лямбда-функции
        self.session_local = SessionLocal(
            engine())  # sessionmaker(bind=engine)
        self.e_help = EngineHelp(session=self.session_local)
        self.e_error = EngineError(session=self.session_local)
        self.e_role = EngineRole(session=self.session_local)
        self.e_plan = EnginePlan(session=self.session_local)
        self.e_group = EngineGroup(session=self.session_local)
        self.e_rights = EngineRights(session=self.session_local)
        self.e_mass_drop = EngineMassDrop(session=self.session_local)
        self.e_mass_load = EngineMassLoad(session=self.session_local)
        self.e_status = EngineStatus(session=self.session_local)
        self.e_user = EngineUser(session=self.session_local)
        self.e_identification = EngineIdentification(
            session=self.session_local)
        self.e_tools = EngineTools(session=self.session_local)
        self.e_cell = EngineCell(session=self.session_local)
        self.e_load = EngineLoad(session=self.session_local)
        self.e_drop = EngineDrop(session=self.session_local)
        self.e_consumption = EngineConsumption(session=self.session_local)
        self.e_history = EngineHistory(session=self.session_local)
        self.e_drop_operations = EngineDropOperations(
            session=self.session_local)
        self.e_operations_consumption = EngineOperationsConsumption(
            session=self.session_local)
        self.e_load_operations = EngineLoadOperations(
            session=self.session_local)
        self.current_user = None
        self.select_tool = None
        self.current_role = None
        self.current_rights = None
        self.select_group = None
        self.select_plans = None
        self.__actions_bad = {
            'write_db_tool_consumption': {'trigger': 'view_err'},
            'read_db_user_from_barcode': {'trigger': 'err_barcode'},
            'read_db_authorization': {'trigger': 'err_authorization'},
            'read_db_username': {'trigger': 'err_authorization'},
            'write_db_rights_by_user_id': {'trigger': 'write_err'},
            'read_db_rights_tool': {'trigger': 'err_rights'},
            'read_db_get_cell': {'trigger': 'err_data'},
            'write_db_plans': {'trigger': 'write_err'},
            'read_db_plan_id': {'trigger': 'err_barcode'},
            'read_db_get_tools': {'trigger': 'err_get_tools_by_plan_id'},
            'write_db_mass_drop_tools_by_plan': {'trigger': 'write_err'},
            'write_db_mass_drop_tools_by_free': {'trigger': 'write_err'},
            'write_db_mass_load_tools_by_plan': {'trigger': 'write_err'},
            'write_db_mass_load_tools_by_free': {'trigger': 'write_err'},
        }
        self.__actions = {
            'write_db_help': lambda message: self.e_help.add_help_entry(message, data=datetime.datetime.now()),
            'read_db_help': lambda index: self.e_help.get_help_by_id(self.e_help.get_all_ids()[index]),
            "count_db_help": lambda: self.e_help.count(),  # Чтение сообщений из таблицы Help
            # "": None,
            'write_db_users': lambda user_data: self.write_db_users(user_data),
            'read_db_user_from_barcode': lambda barcode: self.read_db_user_from_barcode(barcode),
            'read_db_authorization': lambda login, password: self.read_db_authorization(login, password),
            'read_db_username': lambda login, password: self.read_db_username(login),
            'read_db_users': lambda index: self.read_db_users(index),
            # "": None,
            'write_db_rights_by_user_id': lambda user_id, rights_data: self.write_db_rights_by_user_id(user_id, rights_data),
            'read_db_rights_by_user_id': lambda user_id: self.read_db_rights_by_user_id(user_id),
            # 'read_db_rights_tool': lambda tool_id, name: self.read_db_rights_tool(tool_id, name),
            'read_db_rights_tool': lambda tool_id, name: self.read_db_rights_tool(tool_id, name),
            'read_db_get_cell': lambda tool_id, tool_name: self.read_db_get_cell(tool_id, tool_name),
            # "": None,
            'read_db_user_operations': lambda user_id: self.read_db_user_operations(user_id),
            'read_db_plan_operations': lambda plans_id: self.read_db_plan_operations(plans_id),
            'read_db_history': lambda index: self.read_db_history(index),
            'read_db_summary': lambda index: self.read_db_history(index),
            # "": None,
            'write_db_plans': lambda plans_data: self.write_db_plans(plans_data),
            'read_db_plan_id': lambda barcode: self.read_db_plan_id(barcode),
            'read_db_plans': lambda: self.read_db_plans(),
            # "": None,
            'read_db_group_collection': lambda index: self.read_db_group_collection(index),
            'read_db_groups': lambda index: self.read_db_groups(),
            # "": None,
            'write_db_tool_consumption': lambda index=0, *args, trigger='', **kwargs: self.write_db_tool_consumption(index, *args, **kwargs),
            'read_db_get_tools': lambda index, plan_id: self.read_db_tools_by_plans_id(plan_id),
            'read_db_tools_by_group_id': lambda group_id: self.read_db_tools_by_group_id(group_id),
            'read_db_tools_by_plans_id': lambda plan_id: self.read_db_tools_by_plans_id(plan_id),
            'read_db_tools_collection': lambda group_id, group_name: self.read_db_tools_collection(group_id, group_name),
            'read_db_tool_names': lambda group_id, group_name: self.read_db_tool_names(group_id, group_name),
            # "": None,
            'read_db_mass_drop_tools_by_free': lambda: self.read_db_mass_drop_tools_by_free(),
            'read_db_mass_drop_tools_by_plan': lambda plan__id: self.read_db_mass_drop_tools_by_plan(plan__id),
            'read_db_mass_drop_tools': lambda index: self.read_db_mass_drop_tools(index),
            'write_db_drop_tool_groups': lambda index: self.write_db_drop_tool_groups(index),
            'write_db_mass_drop_tools_by_plan': lambda plan__id, tools__data, cells__data: self.write_db_mass_drop_tools_by_plan(plan__id, tools__data, cells__data),
            'write_db_mass_drop_tools_by_free': lambda tools__data, cells__data: self.write_db_mass_drop_tools_by_free(tools__data, cells__data),
            # "": None,
            'write_db_mass_load_tools_by_plan': lambda plan__id, tools__data, cells__data: self.write_db_mass_load_tools_by_plan(plan__id, tools__data, cells__data),
            'write_db_mass_load_tools_by_free': lambda tools__data, cells__data: self.write_db_mass_load_tools_by_free(tools__data, cells__data),
            'write_db_load_tool_groups': lambda index: self.write_db_load_tool_groups(index),
            'read_db_mass_load_tools_by_free': None,  # WEB
            # WEB
            'read_db_mass_load_tools_by_plan': lambda plan_id: self.read_db_mass_load_tools_by_plan(plan_id),
            # mass_load execute
            'read_db_mass_load_tools': lambda index: self.read_db_mass_load_tools(index),
            # "": None,
            'write_db_err_get_tools_by_plan_id': lambda *args, **kwargs: print(),
            'write_db_err_barcode_user': lambda *args, **kwargs: print(),
            'write_db_err_barcode_plan': lambda *args, **kwargs: print(),
            'write_db_err_request': lambda *args, **kwargs: print(),
            'write_db_err_devices': lambda tool_id, tool_name: print(tool_id, tool_name),
            'write_db_err_timeout': lambda *args, **kwargs: print(),
            'write_db_err_rights': lambda *args, **kwargs: self.write_db_err_rights(*args, **kwargs),
            'write_db_err_login': lambda *args, **kwargs: print(),
            'read_db_err_history': lambda *args, **kwargs: self.read_db_err_history(),
            'read_db_err': lambda *args, **kwargs: print(),
        }

    def write_db_err_rights(self, *args, **kwargs):
        # Преобразуем позиционные аргументы в строку
        args_str = ' '.join(map(str, args))
        # Преобразуем именованные аргументы в строку
        kwargs_str = ' '.join(f'{k}={v}' for k, v in kwargs.items())
        # Объединяем все аргументы в одну строку с разделением
        output = ' '.join(filter(None, [args_str, kwargs_str]))
        # Выводим результат
        print(output)

    def read_db_err_history(self):
        """
        Получает историю ошибок из базы данных.

        :return: Список историй ошибок, содержащий данные всех записей.
        """
        # Получаем все идентификаторы записей из истории
        ids = self.e_error.get_all_ids()

        # Извлекаем истории по каждому идентификатору и формируем список
        err_error = [self.e_error.get_error_by_id(index) for index in ids]

        return err_error

    def read_db_get_cell(self, tool_id, tool_name=None):
        """
        Читает номер ячейки (cell.number) по ID инструмента.

        :param tool_id: Уникальный идентификатор инструмента.
        :param tool_name: (опционально) Дополнительный критерий (например, описание).
        :return: Номер ячейки (cell.number) или None, если не найдено.
        """
        # Получаем все ячейки, связанные с данным инструментом
        cells = self.e_cell.get_cells_by_tool(tool_id)

        # Если результат пустой, возвращаем None
        if not cells:
            return {"trigger": "err_data"}

        # Предполагается, что инструмент связан с одной ячейкой
        # Возвращаем номер первой найденной ячейки
        return {"trigger": "send_number", "number": cells[0].number, "tool_name": tool_name} if cells else None

    def read_db_rights_tool(self, tool_id, name):
        self.select_tool = self.e_tools.get_tool_by_id(tool_id)
        return tool_id, name

    def write_db_tool_consumption(self, index, *args, **kwargs):
        """
        Записывает факт расхода инструмента в базу данных.
        user_id: Идентификатор пользователя, который получил инструмент.
        tool_id: Идентификатор инструмента, который был израсходован.
        :return: True, если операция выполнена успешно, иначе False.
        """

        dbSync.init_db = False

        # Проверить наличие инструмента в ячейке
        cells = self.e_cell.get_cells_by_tool(self.select_tool.id)
        cell = None
        if cells != []:
            cell = cells[0]
        if not cell:
            print(
                f"Инструмент с идентификатором {self.select_tool.id} не найдено ни в одной ячейке.")
            return {'trigger': 'view_err'}
        # Очистить ячейку (удалить инструмент из неё)
        cleared = self.e_cell.update_cell(
            id=cell.id,
            number=cell.number,
            description='Старт',
            groups_id=0,
            tools_id=0,
            status_id=0,
        )
        if not cleared:
            print(
                f"Failed to clear tool {self.select_tool.id} from cell {cell.id}.")
            return {'trigger': 'view_err'}

        # Получить статус "расход"
        status = self.e_status.find_by_name("consumption")
        if not status:
            print("Статус «расход» не найден.")
            index = max(self.e_status.get_all_ids(), default=0) + 1
            self.e_status.add(
                index=index,
                stype="consumption",
                description="Инструмент выдан!"
            )
            status = self.e_status.get_status_by_id(status_id=index)
            # return {'trigger': 'view_err'}

        # Добавить запись в таблицу Consumption
        consumption_id = max(self.e_consumption.get_all_ids(), default=0) + 1
        self.e_consumption.add_consumption(
            index=consumption_id,
            cells_id=cell.id,
            tool_id=self.select_tool.id
        )
        if not consumption_id:
            print("Не удалось записать расход инструмента.")
            return {'trigger': 'view_err'}

        # Добавить запись в таблицу History
        history_id = max(self.e_history.get_all_ids(), default=0) + 1
        self.e_history.add_history(
            id=history_id,
            user_id=self.current_user.id,
            role_id=self.e_user.get_user_by_id(self.current_user.id).role_id,
            tools_id=self.select_tool.id,
            datetime_value=datetime.datetime.now(),
            status=status.id,
            description=f"Инструмент {self.select_tool.id} выдано пользователю {self.current_user.id}.",
        )
        if not history_id:
            print("Не удалось записать запись в историю.")
            return {'trigger': 'view_err'}

        operation_id = max(
            self.e_operations_consumption.get_all_ids(), default=0) + 1
        # Добавить запись в таблицу OperationsConsumption
        self.e_operations_consumption.add_operation(
            index=operation_id,
            consumption_id=consumption_id,
            consumption_tools_id=self.select_tool.id,
            status_id=status.id,
            history_id=history_id,
            description=f"Инструмент {self.select_tool.id} потребление зафиксировано.",
        )
        if not operation_id:
            print("Не удалось записать потребление операции.")
            return {'trigger': 'view_err'}

        return {'trigger': 'view_ok'}

    def read_db_tools_collection(self, group_id: int, group_name) -> list[Type[Tools]]:
        """
        Возвращает коллекцию валидных инструментов, связанных с указанной группой,
        включая количество похожих инструментов и их характеристики.

        :param group_id: ID группы, для которой извлекаются инструменты.
        :return: Список инструментов в формате словарей.
        """
        try:
            # Получаем инструменты из указанной группы
            tools = self.e_tools.get_tools_by_group(group_id)
            return tools
        except Exception as e:
            print(
                f"Ошибка при извлечении коллекции инструментов для группы {group_id}: {e}")
            print(traceback.format_exc())
            return []

    def read_db_tools_by_group_id(self, group_id: int) -> list[Tools]:
        """
        Извлекает список инструментов, связанных с указанной группой (group_id), из таблицы Tools.

        :param group_id: ID группы, для которой нужно извлечь инструменты.
        :return: Список объектов Tools, связанных с указанной группой.
        """
        try:
            # Получаем инструменты, связанные с указанным group_id
            tools = self.e_tools.get_tools_by_group(group_id)
            return tools

        except Exception as e:
            print(
                f"Ошибка при извлечении инструментов для группы с ID {group_id}: {e}")
            print(traceback.format_exc())
            return []

    def read_db_tools_by_plans_id(self, plan_id: int):
        """
        Извлекает список инструментов, связанных с указанным планом (plan_id), из таблицы Tools.

        :param plan_id: ID плана, для которого нужно извлечь инструменты.
        :return: Список объектов Tools, связанных с указанным планом.
        """
        if not plan_id:
            return {'trigger': 'err_get_tools_by_plan_id'}
        try:
            result = []
            valid_tools = []

            # Получаем инструменты, связанные с указанным plan_id
            plan = self.e_plan.get_plan_by_id(plan_id)
            tools = self.e_tools.get_tools_by_plan(plan_id)
            result.append(plan)

            for tool in tools:
                # Проверка статуса инструмента в таблице Cell
                cells = self.e_cell.get_cells_by_tool(tool.id)
                cell = None
                if cells != []:
                    cell = cells[0]
                if cell and cell.status_id:
                    status = self.e_status.get_status_by_id(cell.status_id)
                    if status.stype not in ["mass_load_ready", "load_ready"]:
                        continue
                # Проверка операций в таблице DropOperations
                drop_operations = self.e_drop_operations.get_operations_by_tool(
                    tool.id)
                if any(op.status_id for op in drop_operations if self.e_status.get_status_by_id(op.status_id).stype in ["mass_drop_ready", "drop_ready", "mass_drop_init"]):
                    continue
                # Проверка операций в таблице OperationsConsumption
                consumption_operations = self.e_operations_consumption.get_operations_by_tool(
                    tool.id)
                if consumption_operations:
                    continue
                # Проверка операций в таблице LoadOperations
                load_operations = self.e_load_operations.get_operations_by_tool(
                    tool.id)
                if len(load_operations) > 0 and not any(self.e_status.get_status_by_id(op.status_id).stype in ["mass_load_ready", "load_ready"] for op in load_operations):
                    continue

                result.append(tool)
            return result

        except Exception as e:
            print(
                f"Ошибка при извлечении инструментов для плана с ID {plan_id}: {e}")
            print(traceback.format_exc())
            return []

    def read_db_tool_names(self, group_id, group_name):
        """
        Возвращает список инструментов, готовых к выдаче, связанных с указанной группой.
        Учитываются статусы инструментов в таблице Cell и информация из LoadOperations, DropOperations и OperationsConsumption.

        :param group_id: ID группы, для которой извлекаются инструменты.
        :return: Список объектов Tools, готовых к выдаче.
        """

        # Получение всех инструментов, связанных с указанной группой
        tools = self.e_tools.get_tools_by_group(group_id)
        valid_tools = []

        # for tool in tools:
        #     print(" Эталон tool id " + str(tool.id))

        for tool in tools:
            # Проверка статуса инструмента в таблице Cell
            cells = self.e_cell.get_cells_by_tool(tool.id)
            cell = None
            if cells != []:
                cell = cells[0]
            if cell and cell.status_id:
                status = self.e_status.get_status_by_id(cell.status_id)
                if status.stype not in ["mass_load_ready", "load_ready"]:
                    continue
            # Проверка операций в таблице DropOperations
            drop_operations = self.e_drop_operations.get_operations_by_tool(
                tool.id)
            if any(op.status_id for op in drop_operations if self.e_status.get_status_by_id(op.status_id).stype in ["mass_drop_ready", "drop_ready", "mass_drop_init"]):
                continue
            # Проверка операций в таблице OperationsConsumption
            consumption_operations = self.e_operations_consumption.get_operations_by_tool(
                tool.id)
            if consumption_operations:
                continue
            # Проверка операций в таблице LoadOperations
            load_operations = self.e_load_operations.get_operations_by_tool(
                tool.id)
            found = False  # предполагаем, что ни один статус не подходит

            for op in load_operations:
                status = self.e_status.get_status_by_id(
                    op.status_id)  # получаем объект статуса
                if status.stype in ["mass_load_ready", "load_ready"]:  # проверка нужного типа
                    found = True
                    break  # нашли хотя бы один — дальше не надо

            if not found:
                continue
            if len(load_operations) == 0 or load_operations == []:
                continue
            # Если инструмент прошёл все проверки, добавляем его в список
            valid_tools.append(tool)
        return valid_tools, group_name

    def read_db_plan_operations(self, plans_id: int) -> list[dict]:
        """
        Возвращает все операции пользователей с инструментами, связанные с чертежом,
        из таблиц History, LoadOperations, DropOperations и OperationsConsumption.

        :param plans_id: ID чертежа, для которого извлекаются операции.
        :return: Список операций в формате словарей.
        """
        try:
            # Получаем все инструменты, связанные с указанным чертежом
            tools = self.e_tools.get_tools_by_plan(plans_id)
            tools_ids = [tool.id for tool in tools]

            # Получаем все записи из таблицы History, связанные с инструментами чертежа
            history_records = []
            for tool_id in tools_ids:
                stories = self.e_history.get_history_by_tool(tool_id)
                for history in stories:
                    history_records.append(history)

            operations = []

            # Лямбда для создания словаря операции
            def create_operation_dict(history, op, additional_fields): return {
                "datetime": history.datetime,
                "user_name": self.e_user.get_user_by_id(history.user_id).first_name,
                "user_family": self.e_user.get_user_by_id(history.user_id).family,
                "role_name": self.e_role.get_role_by_id(self.e_user.get_user_by_id(history.user_id).role_id).name,
                "history_description": history.description,
                "tools_name": self.e_tools.get_tool_by_id(history.tools_id).name,
                "group_name": self.e_group.get_group_by_id(self.e_tools.get_tool_by_id(history.tools_id).groups_id).name,
                "plan_name": self.e_plan.get_plan_by_id(self.e_tools.get_tool_by_id(history.tools_id).plan_id).name,
                "operation_description": op.description,
                **additional_fields,
            }

            for history in history_records:
                # Добавляем операции из LoadOperations
                load_operations = self.e_load_operations.get_operations_by_history_id(
                    history.id)
                operations.extend([
                    create_operation_dict(history, op, {
                        "load_description": self.e_load.get_load_by_id(op.load_id).description,
                        "cell_number": self.e_cell.get_cell_by_id(self.e_load.get_load_by_id(op.load_id).cell_id).number,
                        "mass_load_description": self.e_mass_load.get_mass_load_by_id(
                            self.e_load.get_load_by_id(op.load_id).mass_load_id
                        ).description,
                        "status_description": self.e_status.get_status_by_id(op.status_id).description,
                    }) for op in load_operations
                ])

                # Добавляем операции из DropOperations
                drop_operations = self.e_drop_operations.get_operations_by_history_id(
                    history.id)
                operations.extend([
                    create_operation_dict(history, op, {
                        "drop_description": self.e_drop.get_drop_by_id(op.drop_id).description,
                        "status_description": self.e_status.get_status_by_id(op.status_id).description,
                    }) for op in drop_operations
                ])

                # Добавляем операции из OperationsConsumption
                consumption_operations = self.e_operations_consumption.get_operations_by_history_id(
                    history.id)
                operations.extend([
                    create_operation_dict(history, op, {
                        "consumption_description": self.e_consumption.get_consumption_by_id(op.consumption_id).description,
                        "status_description": self.e_status.get_status_by_id(op.status_id).description,
                    }) for op in consumption_operations
                ])

            return operations

        except Exception as e:
            print(f"Ошибка при извлечении операций для чертежа: {e}")
            print(traceback.format_exc())
            return []

    def read_db_history(self, index) -> list[dict]:
        print(f"actions_db read_db_history({index})")
        """
        Возвращает все операции пользователей из таблиц History, LoadOperations, DropOperations и OperationsConsumption.

        :return: Список операций в формате словарей, где каждая операция содержит данные из таблицы History и связанных таблиц.
        """

        # Получаем список всех ID пользователей из таблицы Users
        user_ids = self.e_user.get_all_ids()
        operations = []
        try:
            # Лямбда для создания словаря операции
            def create_operation_dict(history, op):

                user = self.e_user.get_user_by_id(history.user_id)
                status = self.e_status.get_status_by_id(op.status_id)
                description = op.description

                if status.stype == "mass_load_init":
                     description = f"Загрузка инструмента в ячейку {add_cell_number(op)}"
                elif status.stype == "consumption":
                     description = f"Выдача инструмента из ячейки {add_cell_number(op)}"
                elif status.stype == "mass_load_ready":
                     description = f"Инструмент помещён в ячейку {add_cell_number(op)}"

                # print(f"history: {history}, op: {op}")

                # print(f"user: {user}, tool: {self.e_tools.get_tool_by_id(history.tools_id)}, op: {add_cell_number(op)}")

                return {
                "datetime": history.datetime,
                "user_name": f"{user.second_name} {user.first_name} {user.family}",
                # "user_name": self.e_user.get_user_by_id(history.user_id).first_name,
                # "user_family": self.e_user.get_user_by_id(history.user_id).family,
                "role_name": self.e_role.get_role_by_id(self.e_user.get_user_by_id(history.user_id).role_id).name,
                # "history_description": history.description,
                "tools_name": self.e_tools.get_tool_by_id(history.tools_id).name,
                "group_name": self.e_group.get_group_by_id(self.e_tools.get_tool_by_id(history.tools_id).groups_id).name,
                # "plan_name": self.e_plan.get_plan_by_id(self.e_tools.get_tool_by_id(history.tools_id).plan_id).name,
                # "operation_description": op.description,
                # "load_description": self.e_load.get_load_by_id(op.load_id).description if hasattr(op, "load_id") else None,
                # "cell_number": add_cell_number(op),
                # "mass_load_description": mass_load_description(op),
                "title": status.description,
                "operation_description": description
            }

            def mass_load_description(op):
                if isinstance(op, OperationsConsumption):
                    consumption = self.e_consumption.get(op.consumption_id)
                    load = self.e_load.find_by_cell_id(consumption.cell_id)
                    mass_load = self.e_mass_load.get_mass_load_by_id(
                        load.mass_load_id)
                    return mass_load.description
                elif isinstance(op, LoadOperations):
                    load = self.e_load.get_load_by_id(op.load_id)
                    mass_load = self.e_mass_load.get_mass_load_by_id(
                        load.mass_load_id)
                    return mass_load.description

            def add_cell_number(op):
                if isinstance(op, OperationsConsumption):
                    consumption = self.e_consumption.get(op.consumption_id)
                    cell_id = consumption.cell_id
                    return cell_id
                elif isinstance(op, LoadOperations):
                    load = self.e_load.get_load_by_id(op.load_id)
                    cell_id = load.cell_id
                    return cell_id

            # Проходим по всем ID пользователей
            for user_id in user_ids:
                # Получаем всю историю операций для пользователя
                user_history = self.e_history.get_history_by_user(user_id)

                for history in user_history:
                    # # Добавляем операции из LoadOperations
                    load_operations = self.e_load_operations.get_operations_by_history_id(history.id)
                    operations.extend([create_operation_dict(history, op) for op in load_operations])
                    #
                    # # Добавляем операции из DropOperations
                    # drop_operations = self.e_drop_operations.get_operations_by_history_id(history.id)
                    # operations.extend([create_operation_dict(history, op) for op in drop_operations])

                    # Добавляем операции из OperationsConsumption
                    consumption_operations = self.e_operations_consumption.get_operations_by_history_id(
                        history.id)
                    operations.extend([create_operation_dict(history, op)
                                      for op in consumption_operations])
            return operations
        except Exception as e:
            print(f"Ошибка при извлечении всех операций: {e}")
            print(traceback.format_exc())
            return []

    def read_db_user_operations(self, user_id: int) -> list[dict]:
        """
        Возвращает все операции пользователя из таблиц History, LoadOperations, DropOperations и OperationsConsumption.

        :param user_id: ID пользователя, для которого извлекаются операции.
        :return: Список операций в формате словарей, где каждая операция содержит данные из таблицы History и связанной таблицы.
        """
        try:
            # Получаем все записи из таблицы History для данного пользователя
            user_history = self.e_history.get_history_by_user(user_id)

            operations = []

            # Лямбда для создания словаря операции
            def create_operation_dict(history, op): return {
                "datetime": history.datetime,
                "user_name": self.e_user.get_user_by_id(history.user_id).first_name,
                "user_family": self.e_user.get_user_by_id(history.user_id).family,
                "role_name": self.e_role.get_role_by_id(self.e_user.get_user_by_id(history.user_id).role_id).name,
                "history_description": history.description,
                "tools_name": self.e_tools.get_tool_by_id(history.tools_id).name,
                "group_name": self.e_group.get_group_by_id(self.e_tools.get_tool_by_id(history.tools_id).groups_id).name,
                "plan_name": self.e_plan.get_plan_by_id(self.e_tools.get_tool_by_id(history.tools_id).plan_id).name,
                "operation_description": op.description,
                "load_description": self.e_load.get_load_by_id(op.load_id).description,
                "cell_number": self.e_cell.get_cell_by_id(self.e_load.get_load_by_id(op.load_id).cell_id).number,
                "mass_load_description": self.e_mass_load.get_mass_load_by_id(self.e_load.get_load_by_id(op.load_id).mass_load_id).description,
                "status_description": self.e_status.get_status_by_id(op.status_id).description,
            }

            for history in user_history:
                # Добавляем операции из LoadOperations
                load_operations = self.e_load_operations.get_operations_by_history_id(
                    history.id)
                operations.extend([create_operation_dict(history, op)
                                  for op in load_operations])

                # Добавляем операции из DropOperations
                drop_operations = self.e_drop_operations.get_operations_by_history_id(
                    history.id)
                operations.extend([create_operation_dict(history, op)
                                  for op in drop_operations])

                # Добавляем операции из OperationsConsumption
                consumption_operations = self.e_operations_consumption.get_operations_by_history_id(
                    history.id)
                operations.extend([create_operation_dict(history, op)
                                  for op in consumption_operations])

            return operations

        except Exception as e:
            print(f"Ошибка при извлечении операций пользователя: {e}")
            print(traceback.format_exc())
            return []

    def read_db_mass_drop_tools(self, index) -> Optional[MassDrop]:
        """
        Возвращает последний добавленный объект из таблицы MassDrop.

        :return: Объект MassDrop с максимальным значением id или None, если таблица пуста.
        """
        # Получить все записи из таблицы MassDrop
        mass_drops = self.e_mass_drop.all()

        if not mass_drops:
            return None  # Если таблица пуста, возвращаем None

        # Найти запись с максимальным id
        latest_mass_drop = max(mass_drops, key=lambda md: md.id)

        return latest_mass_drop

    def read_db_mass_drop_tools_by_plan(self, plan_id: int) -> List[Tools]:
        """
        Возвращает список инструментов, помеченных для массовой выгрузки и связанных с конкретным чертежом.

        :param plan_id: Идентификатор чертежа (Plan), инструменты которого нужно найти.
        :return: Список объектов Tools, связанных с указанным чертежом.
        """
        # 1. Найти все записи массовой выгрузки (MassDrop)
        mass_drops = self.e_mass_drop.all()  # Получить все записи из таблицы MassDrop

        if not mass_drops:
            return []  # Если массовых выгрузок нет, возвращаем пустой список

        # 2. Получить все записи Drop, связанные с MassDrop
        drops = self.e_drop.all()
        mass_drop_ids = {md.id for md in mass_drops}
        mass_drop_drops = [
            drop for drop in drops if drop.mass_drop_id in mass_drop_ids]

        if not mass_drop_drops:
            return []  # Если нет привязанных Drop, возвращаем пустой список

        # 3. Получить инструменты из таблицы Tools, привязанные к Drop и к указанному чертежу (plan_id)
        tools_ids_in_drops = {drop.tools_id for drop in mass_drop_drops}
        tools = self.e_tools.all()
        plan_tools = [
            tool for tool in tools if tool.id in tools_ids_in_drops and tool.plan_id == plan_id]

        if not plan_tools:
            return []  # Если таких инструментов нет, возвращаем пустой список

        # 4. Проверить статус операций в DropOperations
        operations = self.e_drop_operations.all()
        valid_tools = []

        for tool in plan_tools:
            # Проверяем, есть ли операции для этого инструмента
            related_operations = [
                op for op in operations if op.tools_id == tool.id]
            if related_operations:
                valid_tools.append(tool)

        return valid_tools

    def read_db_mass_drop_tools_by_free(self) -> List[Tools]:
        """
        Возвращает список инструментов, помеченных для массовой выгрузки и не связанных с чертежами.

        :return: Список объектов Tools, соответствующих условиям.
        """
        # 1. Найти все записи массовой выгрузки (MassDrop)
        mass_drops = self.e_mass_drop.all()  # Получить все записи из таблицы MassDrop

        if not mass_drops:
            return []  # Если массовых выгрузок нет, возвращаем пустой список

        # 2. Получить все записи Drop, связанные с MassDrop
        drops = self.e_drop.all()
        mass_drop_ids = {md.id for md in mass_drops}
        mass_drop_drops = [
            drop for drop in drops if drop.mass_drop_id in mass_drop_ids]

        if not mass_drop_drops:
            return []  # Если нет привязанных Drop, возвращаем пустой список

        # 3. Получить инструменты из таблицы Tools, привязанные к Drop и не имеющие чертежей (plan_id is None)
        tools_ids_in_drops = {drop.tools_id for drop in mass_drop_drops}
        tools = self.e_tools.all()
        free_tools = [
            tool for tool in tools if tool.id in tools_ids_in_drops and tool.plan_id is None]

        if not free_tools:
            return []  # Если таких инструментов нет, возвращаем пустой список

        # 4. Проверить статус операций в DropOperations
        operations = self.e_drop_operations.all()
        valid_tools = []

        for tool in free_tools:
            # Проверяем, есть ли операции для этого инструмента
            related_operations = [
                op for op in operations if op.tools_id == tool.id]
            if related_operations:
                valid_tools.append(tool)

        return valid_tools

    def write_db_drop_tool_groups(self, _) -> bool:
        """
        Обновляет записи в таблицах DropOperations и Cell для группы инструментов, помечая их как удалённые.

        :return: True, если операция выполнена успешно, иначе False.
        """
        result = True
        try:
            mass_drop_id = max(self.e_mass_drop.get_all_ids())

            drops_by_mass_drop = self.e_drop.get_by_mass_drop_id(mass_drop_id)
            target_operations = []
            for drop in drops_by_mass_drop:
                target_operations.append(
                    self.e_drop_operations.get_operations_by_drop_id(drop.id))

            target_cells = []
            for drop in drops_by_mass_drop:
                target_cells.append(self.e_cell.get(drop.cell_id))

            target_tools = []
            for drop in drops_by_mass_drop:
                target_tools.append(self.e_tools.get(drop.tools_id))

            result = result and self.e_mass_drop.delete(mass_drop_id)

            for drop in drops_by_mass_drop:
                result = result and self.e_drop.delete(drop.id)

            history = []

            for operations in target_operations:
                for operation in operations:
                    history.append(operation.history_id)
                    result = result and self.e_drop_operations.delete(
                        operation.id)

            for target_cell in target_cells:
                # if target_cell:
                result = result and self.e_cell.delete(target_cell.id)

            for target_tool in target_tools:
                result = result and self.e_tools.delete(target_tool.id)

            for story_id in history:
                result = result and self.e_history.delete(story_id)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return False

        return result

    def write_db_load_tool_groups(self, _) -> bool:
        """
        Обновляет записи в таблицах LoadOperations и Cell для группы инструментов, помечая их как готовые для работы.

        :return: True, если операция выполнена успешно, иначе False.
        """
        result = True
        user_id = self.current_user.id
        status = 0
        description = "Готов к выдаче"
        try:
            # Берём последнюю добавленную задачу массовой загрузки.
            mass_load_id = max(self.e_mass_load.get_all_ids())
            # Получаем список загрузок инструментов связанных с последней массовой загрузкой.
            loads_by_mass_load = self.e_load.find_by_mass_load_id(mass_load_id)
            target_operations = []
            for load in loads_by_mass_load:
                # Добавляем
                target_operations.append(
                    self.e_load_operations.get_operations_by_load_id(load.id))

            target_cells = []
            for load in loads_by_mass_load:
                target_cells.append(self.e_cell.get(load.cell_id))

            target_tools = []
            for load in loads_by_mass_load:

                tool = self.e_tools.get(load.tools_id)

                # Если группа не найдена — создаём новую с именем первого слова из tool.name
                group = self.e_group.get(tool.groups_id)
                if group is None:
                    first_word = tool.name.split()[0]
                    new_group_id = max(
                        self.e_group.get_all_ids(), default=0) + 1
                    self.e_group.add(id=new_group_id, name=first_word)
                    tool.groups_id = new_group_id

                target_tools.append(self.e_tools.get(load.tools_id))

            # Получаем статус "ready"
            all_statuses = self.e_status.all()
            ready_status = next(
                (s for s in all_statuses if s.stype == "mass_load_ready"), None)
            if not ready_status:
                index = max(self.e_status.get_all_ids(), default=0) + 1
                self.e_status.add(
                    index=index,
                    stype="mass_load_ready",
                    description="Инструмент готов к выдаче"
                )
                ready_status = self.e_status.get(index)
            ready_status_id = ready_status.id

            for cell in target_cells:
                # cell = self.e_cell.get()
                cell.status_id = ready_status_id
                self.e_cell.update_cell(**(cell.to_dict()))
            # Добавляем запись операций в LoadOperations и ячеек в Cell о готовности к использованию.
            for operations in target_operations:
                access = True
                for operation in operations:
                    status = self.e_status.get_status_by_id(
                        operation.status_id)
                    if 'ready' in status.stype and not access:
                        access = False
                if access:
                    user = self.e_user.get(user_id)
                    history_id = max(self.e_history.get_all_ids()) + 1
                    result = result and self.e_history.add_history(
                        id=history_id,
                        user_id=user.id,
                        role_id=user.role_id,
                        tools_id=operations[0].load_tools_id,
                        datetime_value=datetime.datetime.now(),
                        status=status,
                        description=description,
                    )
                    # Добавляем информацию о разрешении на использование инструмента
                    load_operations_id = max(
                        self.e_load_operations.get_all_ids()) + 1
                    result = result and self.e_load_operations.add_operation(
                        id=load_operations_id,
                        date=datetime.datetime.now(),
                        load_id=operations[0].load_id,
                        load_tools_id=operations[0].load_tools_id,
                        status_id=ready_status_id,
                        history_id=history_id,
                        description=operations[0].description,
                    )
                    # Обновляем статус ячейки
                    load = self.e_load.get(operations[0].load_id)
                    cell = self.e_cell.get(load.cell_id)
                    cell.description = description
                    if cell:
                        result = result and self.e_cell.update_cell(
                            **(cell.to_dict()))
            return result
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return False

    def read_db_groups(self):
        """
        Получает список всех групп из базы данных.

        :return: Список словарей с информацией о группах (id, name, description, status).
        """
        try:
            groups = self.e_group.get_all_groups()
            return groups  # group_list

        except Exception as e:
            print(f"Ошибка при получении списка групп: {e}")
            print(traceback.format_exc())
            return []

    def read_db_group_collection(self, index):
        """
        Получает коллекцию объектов, связанных с группами из базы данных.

        :return: Словарь, где ключи - идентификаторы групп, а значения - связанные объекты (Tools, Cells и т.д.).
        """
        try:
            group_collection = {}

            # Получаем все группы
            groups = self.e_group.get_all_groups()

            if not groups:
                print("Нет доступных групп в базе данных.")
                return group_collection

            for group in groups:
                group_id = group.id

                # Получаем инструменты, связанные с группой
                tools = self.e_group.get_tools_by_group(group_id)

                # Получаем ячейки, связанные с группой
                cells = self.e_group.get_cells_by_group(group_id)

                # Формируем коллекцию для данной группы
                group_collection[group_id] = {
                    "group": group,
                    "tools": tools,
                    "cells": cells
                }

            return group_collection

        except Exception as e:
            print(f"Ошибка при получении коллекции групп: {e}")
            print(traceback.format_exc())
            return {}

    def read_db_users(self, index) -> List[User]:
        print("read_db_users")
        """
        Получает список всех пользователей из базы данных.

        :return: Список объектов User. Пустой список, если пользователей нет.
        """
        try:
            # Получение всех пользователей
            users = self.e_user.get_all_users()
            print(users)
            return users if users else []
        except Exception as e:
            print(f"Ошибка при получении списка пользователей: {e}")
            print(traceback.format_exc())
            return []

    def read_db_username(self, code: int) -> Optional[str]:
        print(f"read_db_username. Input code: {code}")
        """
        Получает имя пользователя (username) по коду.

        :param code: Код пользователя.
        :return: Имя пользователя (username), если найдено, иначе None.
        """
        try:
            # Получение пользователя по коду
            user = self.e_user.get_user_by_code(code)
            if not user:
                return None  # Пользователь не найден

            # Формирование имени пользователя (username)
            username = f"{user.first_name} {user.second_name} {user.family}".strip()
            print(f"read_db_username. Found username: {username}")
            return username if username else None  # Возвращает None, если username пустой

        except Exception as e:
            print(f"Ошибка при получении имени пользователя: {e}")
            print(traceback.format_exc())
            return None

    def read_db_user_from_barcode(self, barcode: int):
        """
        Получает пользователя и связанную с ним роль по штрих-коду.

        :param barcode: Штрих-код пользователя.
        :return: Кортеж (пользователь, роль), если найдено, иначе (None, None).
        """
        try:
            self.current_user = None
            self.select_tool = None
            self.current_role = None
            self.current_rights = None
            self.select_group = None
            self.select_plans = None

            # 1. Получение пользователя по штрих-коду
            user = self.e_user.get_user_by_barcode(barcode)
            if not user:
                return {'trigger': 'err_barcode'}  # Пользователь не найден

            # 2. Получение роли по идентификатору роли пользователя
            role = self.e_role.get_role_by_id(user.role_id)
            self.current_user = user
            self.current_role = role
            return user, role

        except Exception as e:
            print(f"Ошибка при получении пользователя по штрих-коду: {e}")
            print(traceback.format_exc())
            return None, None

    def read_db_authorization(self, login: int, password: int):
        """
        Получает пользователя и связанную с ним роль по логину и паролю.

        :param login: Логин пользователя (Code).
        :param password: Пароль пользователя.
        :return: Кортеж (пользователь, роль), если найдено, иначе (None, None).
        """
        print(f"read_db_authorization. login: {login}, password: {password}")
        if login == '' and password == '':
            # Пользователь не найден или неверный пароль
            return {'trigger': 'err_authorization'}
        try:
            self.current_user = None
            self.select_tool = None
            self.current_role = None
            self.current_rights = None
            self.select_group = None
            self.select_plans = None

            # 1. Получение пользователя по логину (Code)
            user = self.e_user.get_user_by_code(login)
            if not user or user.password != password:
                # Пользователь не найден или неверный пароль
                return {'trigger': 'err_authorization'}

            # 2. Получение роли по идентификатору роли пользователя
            role = self.e_role.get_role_by_id(user.role_id)
            self.current_user = user
            self.current_role = role
            print(f"read_db_authorization. current_user: {user}, current_role: {role}")
            # # Возвращаем явный триггер для роутера по имени роли
            # user_name = (getattr(user, 'first_name', '') or '')
            # role_name = (getattr(role, 'name', '') or '').lower()
            return user, role
            # if role_name in ("admin", "administrator", "developer"):
            #     return {"trigger": "view_type_admin"}
            # elif role_name in ("storekeeper", "stockman", "кладовщик"):
            #     # return {"trigger": "type_storekeeper"}
            #     # return {"user": user_name, "role": role_name}
            #     return user, role
            # else:
            #     return {"trigger": "test_user"}

        except Exception as e:
            print(f"Ошибка при авторизации пользователя: {e}")
            print(traceback.format_exc())
            # Пользователь не найден или неверный пароль
            return {'trigger': 'err_authorization'}

    def write_db_users(self, user_data: dict) -> bool:
        """
        Записывает исчерпывающие данные по пользователю, включая его права и роль.

        :param user_data: Словарь с данными пользователя, содержащий ключи:
            - first_name: Имя пользователя.
            - second_name: Фамилия пользователя.
            - family: Семейное положение пользователя.
            - barcode: Штрих-код пользователя.
            - role: Словарь с данными роли ({'name': str, 'description': Optional[str]}).
            - rights: Список прав ({'name': str, 'description': Optional[str]}).
        :return: True, если данные успешно записаны, иначе False.
        """
        try:
            # 1. Проверка или создание роли
            role_data = user_data.get("role")
            if not role_data:
                raise ValueError("Отсутствует информация о роли пользователя.")

            existing_role = self.e_role.get_all_roles()
            role = None
            for r in existing_role:
                if r.name == role_data.name:
                    role = r
                    break

            if not role:
                role_id = self.e_role.add_role(
                    name=role_data.name,
                    description=role_data.description,
                    parent_role_id=None
                )
                if not role_id:
                    raise ValueError("Не удалось создать новую роль.")
            else:
                role_id = role.id

            # 2. Проверка или создание прав
            rights_data = user_data.get("rights", [])
            if not rights_data:
                raise ValueError(
                    "Отсутствует информация о правах пользователя.")
            if not isinstance(rights_data, list):
                rights_data = [rights_data, ]

            for right in rights_data:
                existing_right = self.e_rights.get_all_rights()
                matching_right = next(
                    (r for r in existing_right if r.name == right.name), None)

                if not matching_right:
                    added = self.e_rights.add_right(
                        index=right.id,
                        name=right.name,  # ["name"],
                        description=right.description,  # .get("description"),
                        role_id=right.role_id  #
                    )
                    if not added:
                        raise ValueError(
                            f"Не удалось создать право: {right.name}.")

            # 3. Проверка или создание пользователя
            user = self.e_user.get_all_users()
            matching_user = next(
                (u for u in user if u.barcode == user_data['user'].barcode), None)
            user = user_data['user']
            if not matching_user:
                user_id = self.e_user.add_user(
                    index=user.id,
                    barcode=user.barcode,
                    code=user.code,
                    first_name=user.first_name,
                    second_name=user.second_name,
                    family=user.family,
                    password=user.password,
                    role_id=user.role_id
                )
                if not user_id:
                    raise ValueError("Не удалось создать пользователя.")

            return True

        except Exception as e:
            print(f"Ошибка при записи данных пользователя: {e}")
            print(traceback.format_exc())
            return False

    def write_db_rights_by_user_id(self, user_id: int, rights_data: list) -> bool:
        """
        Записывает права и роль для пользователя по его идентификатору.

        :param user_id: Уникальный идентификатор пользователя.
        :param rights_data: Список словарей с данными о правах, содержащий ключи:
                            - name: Название права.
                            - description: Описание права (необязательно).
        :return: True, если данные успешно записаны, иначе False.
        """
        try:
            # Получение пользователя по user_id
            user = self.e_user.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"Пользователь с ID {user_id} не найден.")

            # Проверка наличия роли у пользователя
            role_id = user.role_id
            if not role_id:
                raise ValueError(
                    f"У пользователя с ID {user_id} не указана роль.")

            role = self.e_role.get_role_by_id(role_id)
            if not role:
                raise ValueError(f"Роль с ID {role_id} не найдена.")

            # Проверка или добавление прав
            for right_data in rights_data:
                name = right_data.get("name")
                description = right_data.get("description", "")

                # Проверяем, существует ли право с таким именем для роли
                existing_rights = self.e_rights.get_rights_by_role_id(role_id)
                if any(r.name == name for r in existing_rights):
                    continue

                # Добавляем новое право, если его нет
                rights_indx = self.e_rights.get_all_ids()
                rights_indx = max(rights_indx) + 1 if rights_indx else 1
                success = self.e_rights.add_right(
                    index=rights_indx,
                    name=name,
                    description=description,
                    role_id=role_id
                )
                if not success:
                    raise ValueError(
                        f"Не удалось добавить право: {name} для роли с ID {role_id}.")

            return True

        except Exception as e:
            print(
                f"Ошибка при записи прав для пользователя с ID {user_id}: {e}")
            print(traceback.format_exc())
            return False

    def read_db_rights_by_user_id(self, user_id: int) -> list:
        """
        Получает права доступа для пользователя по его идентификатору.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Список объектов Rights, связанных с пользователем, или пустой список, если пользователь или права не найдены.
        """
        try:
            # Получение пользователя по user_id
            user = self.e_user.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"Пользователь с ID {user_id} не найден.")

            # Получение роли пользователя по Role_id
            role_id = user.role_id
            if not role_id:
                raise ValueError(
                    f"У пользователя с ID {user_id} не указана роль.")

            role = self.e_role.get_role_by_id(role_id)
            if not role:
                raise ValueError(f"Роль с ID {role_id} не найдена.")

            # Получение прав доступа, связанных с ролью
            rights = self.e_rights.get_rights_by_role_id(role_id)
            if not rights:
                print(f"Для роли с ID {role_id} не найдены права доступа.")
                return []

            return rights

        except Exception as e:
            print(
                f"Ошибка при получении прав для пользователя с ID {user_id}: {e}")
            print(traceback.format_exc())
            return []

    def read_db_plans(self):
        """
        Читает данные о всех чертежах из таблицы Plan.

        :return: Список словарей, содержащих данные о чертежах,
                 или пустой список, если чертежи отсутствуют.
        """
        try:
            # Получаем список всех чертежей
            plans = self.e_plan.get_all_plans()

            # Формируем список словарей с данными о чертежах
            plans_data = []
            for plan in plans:
                plans_data.append({
                    'id': plan.id,
                    'enterprise': plan.enterprise,
                    'barcode': plan.barcode,
                    'name': plan.name,
                    'description': plan.description,
                    'designation': plan.designation,
                    'list_id': plan.list_id,
                    'list_count': plan.list_count,
                    'parent_plan_id': plan.parent_plan_id
                })

            return plans_data

        except Exception as e:
            print(f"Ошибка при чтении данных чертежей: {e}")
            print(traceback.format_exc())
            return []

    def read_db_plan_id(self, barcode):
        """
        Получает идентификатор чертежа по штрих-коду из базы данных.

        :param barcode: Штрих-код чертежа.
        :return: Идентификатор чертежа (int), если чертеж найден, иначе None.
        """
        try:
            # Получаем чертеж по штрих-коду
            plan = self.e_plan.get_plan_by_barcode(barcode)

            if plan:
                return plan  # Возвращаем идентификатор чертежа
            else:
                print(f"Чертеж с штрих-кодом {barcode} не найден.")
                return None

        except Exception as e:
            print(f"Ошибка при чтении идентификатора чертежа: {e}")
            print(traceback.format_exc())
            return None

    def write_db_plans(self, plans_data):
        """
        Записывает данные о чертежах в таблицу Plan.

        :param plans_data: Список словарей, содержащих данные о чертежах.
                           Пример структуры словаря:
                           {
                               'enterprise': 'Enterprise A',
                               'barcode': '12345',
                               'name': 'Plan Name',
                               'description': 'Plan Description',
                               'designation': 'Purpose',
                               'list_id': 1,
                               'list_count': 10,
                               'parent_plan_id': None
                           }
        :return: True, если данные успешно записаны, иначе False.
        """
        try:
            for plan_data in plans_data:
                # Проверяем, существует ли чертеж с таким штрих-кодом
                existing_plan = self.e_plan.get_plan_by_barcode(
                    plan_data['barcode'])

                if existing_plan:
                    # Обновляем данные, если чертеж уже существует
                    success = self.e_plan.update_plan(
                        existing_plan.id, **plan_data)
                    if not success:
                        raise ValueError(
                            f"Не удалось обновить чертеж с штрих-кодом {plan_data['barcode']}.")
                else:
                    # Добавляем новый чертеж, если его нет в базе
                    success = self.e_plan.add_plan(
                        plan_id=plan_data['plan_id'],
                        enterprise=plan_data['enterprise'],
                        barcode=plan_data['barcode'],
                        name=plan_data['name'],
                        description=plan_data['description'],
                        designation=plan_data['designation'],
                        index_list=plan_data['list_id'],
                        list_count=plan_data['list_count'],
                        parent_plan=0,
                        parent_plan_id=plan_data['parent_plan_id']
                    )
                    if not success:
                        raise ValueError(
                            f"Не удалось добавить новый чертеж с штрих-кодом {plan_data['barcode']}.")

            return True

        except Exception as e:
            print(f"Ошибка при записи данных чертежей: {e}")
            print(traceback.format_exc())
            return False

    def write_db_mass_drop_tools_by_free(self, tools_data: List[Tools], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массового удаления инструментов без привязки к плану.

        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        # Проверка данных
        for tool in tools_data:
            if tool.plan_id is not None:
                raise MassDropToolPlanIDNoneError(
                    "Значение идентификатора чертежа должно быть пустым (None).")
        if len(tools_data) != len(cells_data):
            raise MassDropLenEqCellToolsError(
                f"Значения не могут быть разной длины! tools: {len(tools_data)}, cells: {len(cells_data)}"
            )

        # 1. Найти или создать статус "mass_drop_init"
        all_statuses = self.e_status.all()
        mass_drop_status = next(
            (s for s in all_statuses if s.stype == "mass_drop_init"), None)

        mass_drop_indx = self.e_status.get_all_ids()
        mass_drop_indx = max(mass_drop_indx, default=0) + 1

        if not mass_drop_status:
            mass_drop_status_id = self.e_status.add(
                index=mass_drop_indx,
                stype="mass_drop_init",
                description="Начальный статус для массового удаления"
            )
        else:
            mass_drop_status_id = mass_drop_status.id

        # 2. Создать запись в таблице MassDrop
        mass_drop_id = self.e_mass_drop.get_all_ids()
        mass_drop_id = max(mass_drop_id, default=0) + 1

        mass_drop_description = "Mass drop without a plan"
        self.e_mass_drop.add(
            id=mass_drop_id,
            description=mass_drop_description,
            created_at=datetime.datetime.now()
        )

        if not mass_drop_id:
            raise ValueError("Не удалось создать запись в таблице MassDrop.")

        # 3. Создать записи в таблице Drop
        drop_ids = []
        for tool, cell in zip(tools_data, cells_data):
            drop_id = self.e_drop.add_drop(
                tools_id=tool.id,
                mass_drop_id=mass_drop_id,
                cell_id=cell.id,
                description=f"Drop for tool {tool.name}"
            )
            if drop_id:
                drop_ids.append(max(self.e_drop.get_all_ids()))

        if not drop_ids:
            raise ValueError("Не удалось создать записи в таблице Drop.")

        # 4. Создать записи в таблице DropOperations
        for drop_id in drop_ids:
            drop = self.e_drop.get(drop_id)

            operation_indx = self.e_drop_operations.get_all_ids()
            operation_indx = max(operation_indx, default=0) + 1

            operation_added = self.e_drop_operations.add_operation(
                index=operation_indx,
                drop_id=drop_id,
                tools_id=drop.tools_id,
                status_id=mass_drop_status_id,
                history_id=0,  # Используем значение по умолчанию
                description="Создана операция массового удаления",
            )

            if not operation_added:
                raise ValueError(
                    f"Не удалось создать запись в таблице DropOperations для Drop ID {drop_id}.")

        return True

    def write_db_mass_drop_tools_by_plan(self, plan_id: int, tools_data: List[Tools], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массового удаления инструментов по плану.

        :param plan_id: Идентификатор плана, для которого создаётся массовое удаление.
        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        # Проверка данных
        for tool in tools_data:
            if not tool.plan_id:
                raise MassDropToolPlanIDNoneError(
                    "Значение идентификатора чертежа не может быть пустым (None)")
            if tool.plan_id != plan_id:
                raise MassDropPlanIdEQToolsError(
                    f"Значение идентификатора чертежа в команде записи и "
                    f"наборе данных не могут быть разными: tool.plan_id={tool.plan_id} != plan_id={plan_id}"
                )

        if len(tools_data) != len(cells_data):
            raise MassDropLenEqCellToolsError(
                f"Значения не могут быть разной длины! tools: {len(tools_data)}, cells: {len(cells_data)}"
            )

        # 1. Найти или создать статус "mass_drop_init"
        all_statuses = self.e_status.all()
        mass_drop_status = next(
            (s for s in all_statuses if s.stype == "mass_drop_init"), None)

        mass_drop_indx = self.e_status.get_all_ids()
        mass_drop_indx = max(mass_drop_indx, default=0) + 1

        if not mass_drop_status:
            mass_drop_status_id = self.e_status.add(
                index=mass_drop_indx,
                stype="mass_drop_init",
                description="Начальный статус для массового удаления"
            )
        else:
            mass_drop_status_id = mass_drop_status.id

        # 2. Создать запись в таблице MassDrop
        mass_drop_id = self.e_mass_drop.get_all_ids()
        mass_drop_id = max(mass_drop_id, default=0) + 1

        mass_drop_description = f"Mass drop for plan {plan_id}"
        self.e_mass_drop.add(
            id=mass_drop_id,
            description=mass_drop_description,
            created_at=datetime.datetime.now()
        )

        if not mass_drop_id:
            raise ValueError("Не удалось создать запись в таблице MassDrop.")

        # 3. Создать записи в таблице Drop
        drop_ids = []
        for tool, cell in zip(tools_data, cells_data):
            drop_id = self.e_drop.add_drop(
                tools_id=tool.id,
                mass_drop_id=mass_drop_id,
                cell_id=cell.id,
                description=f"Drop for tool {tool.name}"
            )
            if drop_id:
                drop_ids.append(max(self.e_drop.get_all_ids()))

        if not drop_ids:
            raise ValueError("Не удалось создать записи в таблице Drop.")

        # 4. Создать записи в таблице DropOperations
        for drop_id in drop_ids:
            drop = self.e_drop.get(drop_id)

            operation_indx = self.e_drop_operations.get_all_ids()
            operation_indx = max(operation_indx, default=0) + 1

            operation_added = self.e_drop_operations.add_operation(
                index=operation_indx,
                drop_id=drop_id,
                tools_id=drop.tools_id,
                status_id=mass_drop_status_id,
                history_id=None,
                description="Создана операция массового удаления",
            )

            if not operation_added:
                raise ValueError(
                    f"Не удалось создать запись в таблице DropOperations для Drop ID {drop_id}.")

        return True

    def write_db_mass_load_tools_by_plan(self, plan_id: int, tools_data: List[Tools], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массовой загрузки инструментов по плану.

        :param plan_id: Идентификатор плана, для которого создаётся массовая загрузка.
        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        # try:
        # 1. Найти или создать статус "mass_load_init"
        for tool in tools_data:
            if not tool.plan_id:
                raise MassLoadToolPlanIDNoneError(
                    "Значение идентификатора чертежа не может быть пустым(None)")
            if tool.plan_id != plan_id:
                raise MassLoadPlanIdEQToolsError(
                    f"Значение идентификатора чертежа в команде записи и "
                    f"наборе данных не могут быть разными tool.plan_id{tool.plan_id} != plan_id{plan_id}")
        if len(tools_data) != len(cells_data):
            raise MassLoadLenEqCellToolsError(
                f"Значения не могут быть разной длины! tools: {len(tools_data)} cells: {len(cells_data)}")
        all_statuses = self.e_status.all()
        mass_load_status = next(
            (s for s in all_statuses if s.stype == "mass_load_init"), None)

        mass_load_indx = self.e_status.get_all_ids()

        if mass_load_indx == []:
            mass_load_indx = 1
        else:
            mass_load_indx = max(mass_load_indx) + 1

        if not mass_load_status:
            mass_load_status_id = self.e_status.add(
                index=mass_load_indx,
                stype="mass_load_init",
                description="Начальный статус для массовой нагрузки"
            )
        else:
            mass_load_status_id = mass_load_status.id

        mass_load_id = self.e_mass_load.get_all_ids()
        if mass_load_id == []:
            mass_load_id = 1
        else:
            mass_load_id = max(mass_load_id) + 1

        # 2. Создать запись в таблице MassLoad
        mass_load_description = f"Mass load for plan {plan_id}"
        self.e_mass_load.add(
            id=mass_load_id, description=mass_load_description, created_at=datetime.datetime.now())

        if not mass_load_id:
            raise ValueError("Не удалось создать запись в таблице MassLoad.")

        # 3. Создать записи в таблице Load
        load_ids = []
        for tool in tools_data:
            load_id = self.e_load.add(
                description=f"Load for tool {tool.name}",
                tools_id=tool.id,
                mass_load_id=mass_load_id,
                cell_id=self.e_cell.get_cells_by_tool(tool.id)[0].id
            )
            if load_id:
                load_ids.append(max(self.e_load.get_all_ids()))

        if not load_ids:
            raise ValueError("Не удалось создать записи в таблице Load.")

        # 4. Создать записи в таблице LoadOperations
        for load_id in load_ids:
            load = self.e_load.get(load_id)

            operation_indx = self.e_load_operations.get_all_ids()
            if operation_indx == []:
                operation_indx = 1
            else:
                operation_indx = max(operation_indx) + 1

            operation_added = self.e_load_operations.add_operation(
                id=operation_indx,
                date=datetime.datetime.now(),
                load_id=load_id,
                load_tools_id=load.tools_id,
                status_id=mass_load_status_id,
                history_id=None,
                description="Создана операция массовой загрузки"
            )

            if not operation_added:
                raise ValueError(
                    f"Не удалось создать запись в таблице LoadOperations для Load ID {load_id}.")

        return True

    def read_db_mass_load_tools(self, *args, **kwargs) -> List[int]:
        """
        Извлекает номера ячеек, связанных с последними операциями массовой загрузки инструментов.
        :return: Список номеров ячеек.
        """
        try:
            # 1. Найти статус с типом "mass_load_init"
            status = self.e_status.all()
            status_id = next(
                (s.id for s in status if s.stype == "mass_load_init"), None)

            if not status_id:
                raise ValueError("Статус 'mass_load_init' не найден.")

            mass_load_id = max(self.e_mass_load.get_all_ids())
            loads = self.e_load.find_by_mass_load_id(mass_load_id)
            cells_ids = []
            for load in loads:
                operations = self.e_load_operations.get_operations_by_load_id(
                    load.id)
                # 2. Найти последние операции загрузки, связанные с этим статусом
                # Проверяем, что есть ровно одна операция и ее статус — mass_load_init
                if len(operations) == 1 and operations[0].status_id == status_id:
                    # Если load подходит, добавляем его в список
                    cells_ids.append(load.cell_id)

            # Получение идентификаторов загрузок
            cell_numbers = []
            for _id in cells_ids:
                cell = self.e_cell.get_cell_by_id(_id)
                cell_numbers.append(cell.number)

            return cell_numbers

        except Exception as e:
            print(f"Ошибка при выполнении запроса: {e}")
            print(traceback.format_exc())
            return []

    def write_db_mass_load_tools_by_free(self, tools_data: List[Tools], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массовой загрузки инструментов по плану.

        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        # try:
        # 1. Найти или создать статус "mass_load_init"
        for tool in tools_data:
            if tool.plan_id:
                raise MassLoadToolPlanIDError(
                    "Значение идентификатора чертежа должно быть пустым(None)")
        if len(tools_data) != len(cells_data):
            raise MassLoadLenEqCellToolsError(
                f"Значения не могут быть разной длины! tools: {len(tools_data)} cells: {len(cells_data)}")
        all_statuses = self.e_status.all()
        mass_load_status = next(
            (s for s in all_statuses if s.stype == "mass_load_init"), None)

        mass_load_indx = self.e_status.get_all_ids()

        if mass_load_indx == []:
            mass_load_indx = 1
        else:
            mass_load_indx = max(mass_load_indx) + 1

        if not mass_load_status:
            mass_load_status_id = self.e_status.add(
                index=mass_load_indx,
                stype="mass_load_init",
                description="Начальный статус для массовой нагрузки"
            )
        else:
            mass_load_status_id = mass_load_status.id

        mass_load_id = self.e_mass_load.get_all_ids()
        if mass_load_id == []:
            mass_load_id = 1
        else:
            mass_load_id = max(mass_load_id) + 1

        # 2. Создать запись в таблице MassLoad
        mass_load_description = f"Mass load for free"
        self.e_mass_load.add(
            id=mass_load_id, description=mass_load_description, created_at=datetime.datetime.now())

        if not mass_load_id:
            raise ValueError("Не удалось создать запись в таблице MassLoad.")

        # 3. Создать записи в таблице Load
        load_ids = []
        for tool in tools_data:
            load_id = self.e_load.add(
                description=f"Load for tool {tool.name}",
                tools_id=tool.id,
                mass_load_id=mass_load_id,
                cell_id=self.e_cell.get_cells_by_tool(tool.id)[0].id
            )
            if load_id:
                load_ids.append(max(self.e_load.get_all_ids()))

        if not load_ids:
            raise ValueError("Не удалось создать записи в таблице Load.")

        # 4. Создать записи в таблице LoadOperations
        for load_id in load_ids:
            load = self.e_load.get(load_id)

            operation_indx = self.e_load_operations.get_all_ids()
            if operation_indx == []:
                operation_indx = 1
            else:
                operation_indx = max(operation_indx) + 1

            operation_added = self.e_load_operations.add_operation(
                id=operation_indx,
                date=datetime.datetime.now(),
                load_id=load_id,
                load_tools_id=load.tools_id,
                status_id=mass_load_status_id,
                history_id=None,
                description="Создана операция массовой загрузки"
            )

            if not operation_added:
                raise ValueError(
                    f"Не удалось создать запись в таблице LoadOperations для Load ID {load_id}.")

        return True

    def read_db_mass_load_tools_by_plan(self, plan_id):
        """
        Извлекает данные инструментов, связанных с указанным планом.

        :param plan_id: Уникальный идентификатор плана.
        :return: Список инструментов, связанных с указанным планом.
        """
        try:
            # Проверяем существование плана
            plan = self.e_plan.get_plan_by_id(plan_id)
            if not plan:
                raise ValueError(f"План с ID {plan_id} не найден.")

            # Извлекаем все задачи массовой загрузки, связанные с данным планом
            # Получаем все ID задач массовой загрузки
            mass_loads = self.e_mass_load.get_all_ids()
            if not mass_loads:
                return []

            # Список всех инструментов, связанных с задачами массовой загрузки
            tools = []
            for mass_load_id in mass_loads:
                # Находим записи Load по mass_load_id
                loads = self.e_load.find_by_mass_load_id(mass_load_id)
                for load in loads:
                    # Извлекаем инструмент по tools_id
                    tool = self.e_tools.get(load.tools_id)
                    if tool:
                        tools.append(tool)

            return tools
        except Exception as e:
            # Обработка ошибок
            print(
                f"Ошибка при чтении инструментов для плана {plan_id}: {str(e)}")
            print(traceback.format_exc())
            return []

    def execute(self, act, *args, **kwargs):
        try:
            print("action_db", "execute", act, args, kwargs)
            return self.__actions[act](*args, **kwargs)
        except Exception as e:
            print("action_db", "execute", act, "exception", e)
            print(traceback.format_exc())
            try:
                return self.__actions_bad[act]
            except:
                ...
