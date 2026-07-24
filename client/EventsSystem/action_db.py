import datetime
import traceback
from typing import List, Optional, Type, Any
import dbSync
# ----------------------------------- 1
from DB.Engine.HelpCRUD import EngineHelp
# from DB.Engine.HelpCRUD import EngineHelp
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
# from DB.Models.Tools import Tools
from DB.Models.ToolTypes import ToolTypes
from DB.Models.Group import Group
from DB.Models.User import User
from EventsSystem.hal_coords import format_hal_coords_error, validate_hal_cell_coords
from sphinx.cmd.quickstart import valid_dir

from Core.role_display import get_role_display_name
from DB.Engine.PlanToolTypesCRUD import EnginePlanToolTypes
from DB.Engine.ToolTypesCRUD import EngineToolTypes

logger = logging.getLogger(__name__)


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
        self.e_tool_types = EngineToolTypes(session=self.session_local)
        self.e_plan_tool_types = EnginePlanToolTypes(session=self.session_local)
        self.e_group = EngineGroup(session=self.session_local)
        self.e_rights = EngineRights(session=self.session_local)
        self.e_mass_drop = EngineMassDrop(session=self.session_local)
        self.e_mass_load = EngineMassLoad(session=self.session_local)
        self.e_status = EngineStatus(session=self.session_local)
        self.e_user = EngineUser(session=self.session_local)
        self.e_identification = EngineIdentification(
            session=self.session_local)
        # self.e_tools = EngineTools(session=self.session_local)
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
        self.select_plan = None
        self.plan_cell_list = None
        self.select_cell = None
        self.__actions_bad = {
            'write_db_tool_consumption': {'trigger': 'view_err'},
            'read_db_user_from_barcode': {'trigger': 'err_barcode'},
            'read_db_authorization': {'trigger': 'err_authorization'},
            'read_db_username': {'trigger': 'err_authorization'},
            'write_db_rights_by_user_id': {'trigger': 'write_err'},
            'read_db_rights_tool': {'trigger': 'err_rights'},
            'read_db_get_cell': {'trigger': 'err_data'},
            'read_db_get_cells': {'trigger': 'err_data'},
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
            'read_db_help': lambda index: self.e_help.get_help_by_id(self.e_help.get_all_ids()[index]) if self.e_help.count() > 0 else None,
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
            'read_db_rights_tool': lambda tool_type_id, name, group_name, tool_description: self.read_db_rights_tool(tool_type_id, name, group_name, tool_description),
            'read_db_get_cell': lambda tool_id, tool_name: self.read_db_get_cell(tool_id, tool_name),
            'read_db_get_cells': lambda tool_list, plan_id: self.read_db_get_cells(tool_list),
            'read_db_get_more_cells': lambda cells_list, trigger='': self.read_db_get_more_cells(cells_list),
            # "": None,
            'read_db_user_operations': lambda user_id: self.read_db_user_operations(user_id),
            'read_db_plan_operations': lambda plans_id: self.read_db_plan_operations(plans_id),
            'read_db_history': lambda index: self.read_db_history(index),
            'read_db_summary': lambda index: self.read_db_history(index),
            # "": None,
            'write_db_plans': lambda plans_data: self.write_db_plans(plans_data),
            'read_db_plan_id': lambda barcode: self.read_db_plan_id(barcode),
            'read_db_plans': lambda: self.read_db_plans(1),
            'read_db_plan': lambda index: self.read_db_plans(index),
            'read_db_get_plan_tools': lambda plan_id, plan_designation, plan_name: self.read_db_get_plan_tools(plan_id, plan_designation, plan_name),
            'read_db_plan_complete': lambda tool_list, plan_id: self.read_db_plan_complete(plan_id),
            'write_db_plan_complete': lambda tool_list, plan_id: self.write_db_plan_complete(plan_id),
            # "": None,
            'read_db_group_collection': lambda index: self.read_db_group_collection(index),
            'read_db_groups': lambda *args, **kwargs: self.read_db_groups(),
            # "": None,
            'write_db_tool_consumption': lambda index=0, *args, trigger='', **kwargs: self.write_db_tool_consumption(index, *args, **kwargs),
            'read_db_get_tools': lambda plan_id: self.read_db_tools_by_plans_id(plan_id),
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
            'write_db_err_get_tools_by_plan_id': lambda *args, **kwargs: logger.debug("write_db_err_get_tools_by_plan_id"),
            'write_db_err_barcode_user': lambda *args, **kwargs: logger.debug("write_db_err_barcode_user"),
            'write_db_err_barcode_plan': lambda *args, **kwargs: logger.debug("write_db_err_barcode_plan"),
            'write_db_err_request': lambda *args, **kwargs: logger.debug("write_db_err_request"),
            'write_db_err_devices': lambda *args, **kwargs: self.write_db_err_devices(*args, **kwargs),
            'write_db_err_timeout': lambda *args, **kwargs: self.write_db_err_timeout(*args, **kwargs),
            'write_db_err_rights': lambda *args, **kwargs: self.write_db_err_rights(*args, **kwargs),
            'write_db_err_login': lambda *args, **kwargs: logger.debug("write_db_err_login"),
            'read_db_err_history': lambda *args, **kwargs: self.read_db_err_history(),
            'read_db_err': lambda *args, **kwargs: logger.debug("read_db_err"),
            'read_db_cells_hal_list': lambda *args, **kwargs: self.read_db_cells_hal_list(*args, **kwargs),
            'write_db_cell_hal_coords': lambda *args, **kwargs: self.write_db_cell_hal_coords(*args, **kwargs),
            'read_db_hal_import_validate': lambda *args, **kwargs: self.read_db_hal_import_validate(*args, **kwargs),
            'write_db_hal_import_coords': lambda *args, **kwargs: self.write_db_hal_import_coords(*args, **kwargs),
            'write_db_hal_park_defaults': lambda *args, **kwargs: self.write_db_hal_park_defaults(*args, **kwargs),
            'write_db_hal_sol_s_default': lambda *args, **kwargs: self.write_db_hal_sol_s_default(*args, **kwargs),
            'read_db_engineer_get_cell': lambda *args, **kwargs: self.read_db_engineer_get_cell(*args, **kwargs),
            'read_db_engineer_command_ok': lambda *args, **kwargs: self.read_db_engineer_command_ok(*args, **kwargs),
        }

    def _invalidate_availability_caches(self, log_prefix: str = ""):
        """
        Инвалидирует кэши, влияющие на подсчёт доступных инструментов (экран групп и экран инструментов).
        Вызывать:
        - перед чтением: read_db_groups, read_db_tool_names, read_db_group_collection, read_db_tools_collection, read_db_get_more_cells;
        - после записи: write_db_tool_consumption, write_db_load_tool_groups, write_db_drop_tool_groups,
          write_db_mass_load_tools_by_*, write_db_mass_drop_tools_by_*.
        Подсчёт доступных ведётся по ячейкам Cell с нужным статусом (3, 7) и отсутствию записи выдачи (Consumption без plan_id для свободных инструментов).
        """
        self.e_cell._cache.clear()
        self.e_load._cache.clear()
        self.e_tool_types._cache.clear()
        self.e_group._cache.clear()
        try:
            self.session_local.commit()
            self.session_local.expire_all()
            if log_prefix:
                logger.debug("[%s] Availability caches invalidated, fresh data will be loaded from DB".format( log_prefix))
        except Exception as e:
            logger.warning("[_invalidate_availability_caches] %s".format( e))

    def write_db_err_rights(self, *args, **kwargs):
        # Преобразуем позиционные аргументы в строку
        args_str = ' '.join(map(str, args))
        # Преобразуем именованные аргументы в строку
        kwargs_str = ' '.join(f'{k}={v}' for k, v in kwargs.items())
        # Объединяем все аргументы в одну строку с разделением
        output = ' '.join(filter(None, [args_str, kwargs_str]))
        logger.debug("write_db_err_rights: %s".format( output))

    def _hal_coords_gate(self, cell) -> Optional[dict]:
        """
        Для atmega_hal: блокирует выдачу без валидных hal_x/hal_z (до cmd_send / UART).
        """
        protocol = (self.__executor.controller_protocol or "legacy").strip().lower()
        if protocol != "atmega_hal":
            return None
        ok, reason = validate_hal_cell_coords(cell.hal_x, cell.hal_z)
        if ok:
            return None
        self.__executor.hardware_last_error = format_hal_coords_error(
            reason,
            cell_id=cell.id,
            number=cell.number,
        )
        logger.error("HAL coords gate: %s", self.__executor.hardware_last_error)
        return {"trigger": "err_devices"}

    def write_db_err_devices(self, *args, **kwargs):
        """
        Запись ошибки оборудования и переход на экран аппаратной ошибки.
        """
        args_str = " ".join(map(str, args)).strip()
        kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items()).strip()
        payload = " ".join(filter(None, [args_str, kwargs_str])).strip()

        ctx_reason = getattr(self.__executor, "hardware_last_error", "") or ""
        message = " ".join(filter(None, [ctx_reason, payload])).strip()
        if not message:
            message = "device_error"

        try:
            self.e_error.add_error("Device Error", message[:500])
        except Exception as e:
            logger.exception("write_db_err_devices add_error failed: %s", e)

        logger.error("write_db_err_devices: %s", message)
        return {"trigger": "view_err_hardware"}

    def write_db_err_timeout(self, *args, **kwargs):
        """
        Запись timeout-ошибки контроллера и переход на экран аппаратной ошибки.
        """
        args_str = " ".join(map(str, args)).strip()
        kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items()).strip()
        payload = " ".join(filter(None, [args_str, kwargs_str])).strip()

        ctx_reason = getattr(self.__executor, "hardware_last_error", "") or ""
        message = " ".join(filter(None, [ctx_reason, payload])).strip()
        if not message:
            message = "device_timeout"

        try:
            self.e_error.add_error("Timeout", message[:500])
        except Exception as e:
            logger.exception("write_db_err_timeout add_error failed: %s", e)

        logger.error("write_db_err_timeout: %s", message)
        return {"trigger": "view_err_hardware"}

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
        logger.debug("read_db_get_cell %s %s".format( tool_id, tool_name))
        """
        Читает номер ячейки (cell.number) по ID инструмента.

        :param tool_id: Уникальный идентификатор инструмента.
        :param tool_name: (опционально) Дополнительный критерий (например, описание).
        :return: Номер ячейки (cell.number) или None, если не найдено.
        """
        # Получаем все ячейки, связанные с данным инструментом
        cells = self.e_cell.get_cells_by_tool(tool_id)
        selected_cell = None
        if cells:
            for cell in cells:
                if cell.status_id in [3, 7]:
                    if self.select_plan:
                        selected_cell = cell
                        break
                    # Для свободной выдачи инструмент должен быть загружен без привязки к плану.
                    loads = self.e_load.find_by_cell_id(cell.id)
                    load = max(loads, key=lambda rec: rec.id) if loads else None
                    if load and load.plan_id is None:
                        selected_cell = cell
                        break

        # Если результат пустой, возвращаем None
        if not cells:
            return {"trigger": "err_data"}

        # cell = cells[0]
        self.select_cell = selected_cell

        if not selected_cell:
            return None

        blocked = self._hal_coords_gate(selected_cell)
        if blocked:
            return blocked

        # Предполагается, что инструмент связан с одной ячейкой
        return {
            "trigger": "send_number",
            "number": selected_cell.number,
            "cell_id": selected_cell.id,
            "tool_name": tool_name,
        }

    def read_db_get_cells(self, tool_list):
        logger.debug("read_db_get_cells %s".format( tool_list))
        """
        Читает номер ячеек (cell.number) по ID чертежа.

        :param plan_id: Уникальный идентификатор чертежа.
        :return: Список номеров ячеек (cell.number) или None, если не найдено.
        """
        # Получаем все ячейки, связанные с данным чертежом

        # plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan_id)


        cells_list = []

        needed_tools = 0
        # for plan_tool_type in plan_tool_types:
        for tool_id in tool_list:
            tool_type = self.e_tool_types.get_tool_type_by_id(tool_id)

            needed_tools += tool_list[tool_id]
            # needed_tools += plan_tool_type.tool_types_count

            # tools = self.e_tools.get_tools_by_tool_type_id(tool_type.id)

            # for tool in tools:
            cells = self.e_cell.get_cells_by_tool(tool_type.id)

            # Если ячейка не найдена, возвращаем ошибку
            if not cells:
                continue

            found_tools = 0
            # По очереди проходим ячейки с инструментами этого типа
            # Возвращаем номера ячеек, согласно необходимому количеству
            for cell in cells:
                if cell.status_id in [3, 7]:
                    cells_list.append(cell)
                    found_tools += 1
                    if found_tools == tool_list[tool_id]:
                        break

        # Если результат пустой, возвращаем None
        logger.debug("needed by plan: %s, found: %s".format( needed_tools, len(cells_list)))
        logger.debug("cells_list: %s".format( cells_list))
        if not cells_list or needed_tools > len(cells_list):
            return {"trigger": "err_data"}

        # return {"trigger": "get_more_cells", "cells_list": cells_list} if cells_list else None
        # return {"cells_list": cells_list} if cells_list else None
        self.plan_cell_list = cells_list
        return {"cells_list": cells_list} if cells_list else None

    def read_db_get_more_cells(self, cells_list):
        logger.debug("read_db_get_more_cells %s".format( cells_list))
        logger.debug("self.plan_cell_list %s".format( self.plan_cell_list))
        """
        Читает номер первой ячейки (cell.number) из списка, удаляет из списка, если выдано.

        :param cells_list: список ячеек.
        :return: Номер ячейки (cell.number) или None, если не найдено.
        """

        # если список пустой, то возвращается ок
        if not self.plan_cell_list:
            return {"trigger": "view_ok"}

        # Проверяем ячейки перед выдачей, пропускаем уже выданные (защита от двойной выдачи)
        while self.plan_cell_list:
            candidate_cell = self.plan_cell_list[0]
            self._invalidate_availability_caches("read_db_get_more_cells")
            cell = self.e_cell.get_cell_by_id(candidate_cell.id)
            if not cell:
                self.plan_cell_list.pop(0)
                continue
            # Проверяем, не была ли ячейка уже выдана
            # 1. Проверяем статус ячейки (должен быть 3 или 7)
            if cell.status_id not in [3, 7]:
                logger.debug("[read_db_get_more_cells] Cell %s уже выдана (status_id=%s), пропускаем".format( cell.id, cell.status_id))
                self.plan_cell_list.pop(0)
                continue

            blocked = self._hal_coords_gate(cell)
            if blocked:
                return blocked

            # Ячейка доступна для выдачи
            self.select_cell = self.plan_cell_list.pop(0)

            return {
                "trigger": "send_number",
                "number": self.select_cell.number,
                "cell_id": self.select_cell.id,
                "tool_name": "Инструмент",
            }
        
        # Если все ячейки уже были выданы
        return {"trigger": "view_ok"}

    def read_db_rights_tool(self, tool_type_id, name, group_name, tool_description):
        logger.debug(
            "read_db_rights_tool tool_type_id %s, name %s, group_name %s, tool_description %s".format(
            tool_type_id, name, group_name, tool_description
        ))

        # tools = self.e_tools.get_tools_by_tool_type_id(tool_type_id)
        # print(f"tools {tools}")
        # if tools:
        cells = self.e_cell.get_cells_by_tool(tool_type_id)
        if cells:
            for cell in cells:
                if cell.status_id in [3, 7]:
                    if self.select_plan:
                        self.select_tool = self.e_tool_types.get_tool_type_by_id(tool_type_id)
                        return self.select_tool.id, name, group_name, tool_description
                    # Для свободной выдачи инструмент должен быть загружен без привязки к плану.
                    loads = self.e_load.find_by_cell_id(cell.id)
                    load = max(loads, key=lambda rec: rec.id) if loads else None
                    if load and load.plan_id is None:
                        self.select_tool = self.e_tool_types.get_tool_type_by_id(tool_type_id)
                        return self.select_tool.id, name, group_name, tool_description
            logger.warning("Свободные инструменты \"%s\" не найдены.".format( name))
            return {'trigger': 'err_rights'}
        else:
            logger.warning("Ячейки, содержащие \"%s\" не найдены.".format( name))
            return {'trigger': 'err_rights'}

    def write_db_tool_consumption(self, index, *args, **kwargs):
        logger.debug("write_db_tool_consumption %s, %s, %s, %s, %s, %s".format( index, args, kwargs, self.select_tool, self.select_cell, self.select_plan))
        """
        Записывает факт расхода инструмента в базу данных.
        Перед выдачей инвалидирует кэши и заново читает ячейку из БД, чтобы исключить двойную выдачу
        при медленном обновлении UI/кэша (повторное нажатие или параллельный запрос).
        """
        if not self.select_cell:
            logger.debug("[write_db_tool_consumption] select_cell не задана.")
            return {'trigger': 'view_err'}

        # Инвалидация кэшей и сессии до чтения ячейки — гарантирует актуальное состояние из БД,
        # чтобы при повторном вызове (двойной клик / медленный UI) увидеть уже очищенную ячейку и отклонить выдачу
        self._invalidate_availability_caches("write_db_tool_consumption")

        cell = self.e_cell.get_cell_by_id(self.select_cell.id)
        if not cell:
            logger.warning("[write_db_tool_consumption] Ячейка %s не найдена.", self.select_cell.id)
            return {'trigger': 'view_err'}
        # Проверка по актуальным данным из БД: ячейка должна быть в статусе «готово к выдаче» (3 или 7) и содержать инструмент
        if cell.status_id not in (3, 7):
            logger.warning("[write_db_tool_consumption] Ячейка %s уже выдана или недоступна (status_id=%s).", cell.id, cell.status_id)
            return {'trigger': 'view_err'}
        if not cell.tools_id:
            logger.warning("[write_db_tool_consumption] В ячейке %s не найдено инструментов.", self.select_cell.number)
            return {'trigger': 'view_err'}

        self.select_tool = self.e_tool_types.get_tool_type_by_id(cell.tools_id)

        status = self.e_status.find_by_name("consumption")
        if not status:
            logger.warning("Статус «расход» не найден.")
            idx = max(self.e_status.get_all_ids(), default=0) + 1
            self.e_status.add(
                index=idx,
                stype="consumption",
                description="Инструмент выдан!",
                created_at=datetime.datetime.now()
            )
            status = self.e_status.get_status_by_id(status_id=idx)

        # Очистить ячейку (удалить инструмент из неё)
        cleared = self.e_cell.update_cell(
                cell_id=cell.id,
                number=cell.number,
                description='Старт',
                groups_id=None,
                tools_id=None,
                status_id=1,
            )
        if not cleared:
            logger.warning("Failed to clear tool %s from cell %s.", self.select_tool.id, cell.id)
            return {'trigger': 'view_err'}

        logger.debug("cleared %s".format( cleared))

        # loads = self.e_load.find_by_cell_id(cell.id)
        # load = max(loads, key=lambda rec: rec.id) if loads else None
        #
        # load_dict = load.to_dict()
        # load_dict['status_id'] = status.id
        # self.e_load.update(index=load.id, **load_dict)

        # Добавить запись в таблицу History
        history_id = max(self.e_history.get_all_ids(), default=0) + 1
        self.e_history.add_history(
            id=history_id,
            user_id=self.current_user.id,
            role_id=self.e_user.get_user_by_id(self.current_user.id).role_id,
            tools_id=self.select_tool.id,
            plan_id=self.select_plan.id if self.select_plan else None,
            datetime_value=datetime.datetime.now(),
            status=status.id,
            description=f"Инструмент {self.select_tool.id} выдано пользователю {self.current_user.id}.",
        )
        if not history_id:
            logger.error("Не удалось записать запись в историю.")
            return {'trigger': 'view_err'}

        # Добавить запись в таблицу Consumption
        consumption_id = max(self.e_consumption.get_all_ids(), default=0) + 1
        self.e_consumption.add_consumption(
            index=consumption_id,
            cells_id=cell.id,
            tool_id=self.select_tool.id,
            plan_id=self.select_plan.id if self.select_plan else None,
            history_id=history_id,
            status_id=status.id,
        )
        if not consumption_id:
            logger.error("Не удалось записать расход инструмента.")
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
            self.select_plan = None
            logger.error("Не удалось записать потребление операции.")
            return {'trigger': 'view_err'}

        self._invalidate_availability_caches("write_db_tool_consumption")
        self.e_consumption._cache.clear()

        if not self.plan_cell_list:
            logger.debug("write_db_tool_consumption trigger")
            self.select_plan = None
            return {'trigger': 'view_ok'}
        else:
            logger.debug("write_db_tool_consumption cell_list")
            return {'trigger': 'get_more_cells', 'cells_list': self.plan_cell_list}

    def read_db_tools_collection(self, group_id: int, group_name) -> tuple[list[Any], Any] | Any:
        logger.debug("action_db read_db_tools_collection, %s, %s".format( group_id, group_name))
        """
        Возвращает коллекцию валидных инструментов, связанных с указанной группой,
        включая количество похожих инструментов и их характеристики.

        :param group_id: ID группы, для которой извлекаются инструменты.
        :return: Список инструментов в формате словарей.
        """
        self._invalidate_availability_caches("read_db_tools_collection")
        # Лямбда для создания словаря инструментов
        def create_tool_dict(cell, tool):
            return {
                "group": self.e_group.get_group_by_id(tool.groups_id),
                "tool": tool,
                "cell": cell,
            }

        # TODO: Вынести в утилитарный класс
        def add_all_parent_groups(group_list: list[Group], parent_group_id: int, group: Group, group_id: int):
            if parent_group_id == group_id:
                group_list.append(group)
            elif parent_group_id != 0 :
                parent_group = self.e_group.get_group_by_id(parent_group_id)
                add_all_parent_groups(
                    group_list, parent_group.paren_group_id, group, group_id)

        try:
            group_list = []

            # Получаем все подгруппы указанной группы
            groups = self.e_group.get_all_groups()
            for group in groups:
                if group.id == group_id:
                    group_list.append(group)
                else:
                    add_all_parent_groups(
                    group_list, group.paren_group_id, group, group_id)
            logger.debug("group_list: %s".format( group_list))

            tools = []

            for group in group_list:
                # Получаем инструменты из указанной группы
                # tools.extend(self.e_tools.get_tools_by_group(group.id))
                tools.extend(self.e_tool_types.get_tool_types_by_group(group.id))

            # Filter tools to only those with cells having status_id in {3,7}
            valid_tools = []
            logger.debug(f"tools: {tools}")
            for tool_type in tools:
                cells = self.e_cell.get_cells_by_tool(tool_type.id)
                for cell in cells:
                    if cell.status_id in {3, 7}:
                        valid_tools.append(create_tool_dict(cell, tool_type))

            return valid_tools, group_name
        except Exception as e:
            logger.exception("Ошибка при извлечении коллекции инструментов для группы %s: %s", group_id, e)
            return [], group_name

    def read_db_tools_by_group_id(self, group_id: int) -> list[ToolTypes]:
        """
        Извлекает список инструментов, связанных с указанной группой (group_id), из таблицы Tools.

        :param group_id: ID группы, для которой нужно извлечь инструменты.
        :return: Список объектов Tools, связанных с указанной группой.
        """
        try:
            # Получаем инструменты, связанные с указанным group_id
            # tools = self.e_tools.get_tools_by_group(group_id)
            tool_types = self.e_tool_types.get_tool_types_by_group(group_id)
            return tool_types

        except Exception as e:
            logger.exception("Ошибка при извлечении инструментов для группы с ID %s: %s", group_id, e)
            return []

    def read_db_tools_by_plans_id(self, plan_id: int):
        logger.debug("read_db_tools_by_plans_id. plan_id: %s".format( plan_id))
        """
        Извлекает список инструментов, связанных с указанным планом (plan_id), из таблицы Tools.

        :param plan_id: ID плана, для которого нужно извлечь инструменты.
        :return: Список объектов Tools, связанных с указанным планом.
        """
        if not plan_id:
            return {'trigger': 'err_get_tools_by_plan_id'}
        try:

            plan = self.e_plan.get_plan_by_id(plan_id)
            self.select_plan = plan

            plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan_id)

            plan_tool_list = []

            for plan_tool_type in plan_tool_types:
                tool_object = {}
                tool_type = self.e_tool_types.get_tool_type_by_id(plan_tool_type.tool_types_id)

                tool_object["tool_type"] = tool_type
                tool_object["total_count"] = tool_type.count
                tool_object["plan_count"] = plan_tool_type.tool_types_count

                cells = self.e_cell.get_cells_by_tool(tool_type.id)
                tool_load_count = 0
                for cell in cells:
                    if cell.status_id in [3, 7]:
                        loads = self.e_load.find_by_cell_id(cell.id)
                        load = max(loads, key=lambda rec: rec.id) if loads else None
                        if self.select_plan:
                            if load and load.plan_id == self.select_plan.id:
                                tool_load_count += 1

                tool_object["load_count"] = tool_load_count

                if plan_tool_type.tool_types_count <= tool_load_count:
                    has_tools = True
                else:
                    has_tools = False

                tool_object["has_tools"] = has_tools

                plan_tool_list.append(tool_object)

            return plan_tool_list, plan.designation, plan.name, plan_id


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
            logger.debug(
                f"Ошибка при извлечении инструментов для плана с ID {plan_id}: {e}")
            logger.exception("")
            return []

    def read_db_tool_names(self, group_id, group_name):
        """
        Возвращает список инструментов, готовых к выдаче, связанных с указанной группой.
        Доступное количество считается только по ячейкам Cell со статусом 3 или 7.

        :param group_id: ID группы, для которой извлекаются инструменты.
        :return: Список объектов Tools, готовых к выдаче, с полем count.
        """
        self.select_plan = None
        # Лямбда для создания словаря инструментов
        def create_tool_dict(cell, tool):
            return {
                "group": self.e_group.get_group_by_id(tool.groups_id),
                "tool": tool,
                "cell": cell,
            }

        def create_tool_types_dict(tool_type, count):
            return {
                "group": self.e_group.get_group_by_id(tool_type.groups_id),
                "tool": tool_type,
                "count": count,
            }

        # TODO: Вынести в утилитарный класс
        def add_all_parent_groups(group_list: list[Group], parent_group_id: int, group: Group, group_id: int):
            if parent_group_id == group_id:
                group_list.append(group)
            elif parent_group_id != 0 :
                parent_group = self.e_group.get_group_by_id(parent_group_id)
                add_all_parent_groups(
                    group_list, parent_group.paren_group_id, group, group_id)

        try:
            group_list = []

            # Получаем все подгруппы указанной группы
            groups = self.e_group.get_all_groups()
            for group in groups:
                if group.id == group_id:
                    group_list.append(group)
                else:
                    add_all_parent_groups(
                    group_list, group.paren_group_id, group, group_id)
            logger.debug("group_list: %s".format( group_list))

            # tools = []
            tool_types = []

            for group in group_list:
                # Получаем инструменты из указанной группы
                # tools.extend(self.e_tools.get_tools_by_group(group.id))
                tool_types.extend(self.e_tool_types.get_tool_types_by_group(group.id))
        except Exception as e:
            logger.debug(
                f"Ошибка при извлечении коллекции инструментов для группы {group_id}: {e}")
            logger.exception("")
            # tools = []
            tool_types = []

        valid_tool_types = []

        self._invalidate_availability_caches("read_db_tool_names")

        # for tool in tools:
        #     print(" Эталон tool id " + str(tool.id))

        for tool_type in tool_types:
            # tools = self.e_tools.get_tools_by_tool_type_id(tool_type.id)
            # valid_tools = []
            # for tool in tools:
                # Проверка статуса инструмента в таблице Cell
            valid_tools_count = 0
            cells = self.e_cell.get_cells_by_tool(tool_type.id)
            if cells:
                for cell in cells:
                    if cell and cell.status_id:
                        # status = self.e_status.get_status_by_id(cell.status_id)
                        # if status.stype not in ["mass_load_ready", "load_ready"]:
                        if cell.status_id not in {3, 7}:
                            continue

                        # Проверка операций в таблице DropOperations
                        # drop_operations = self.e_drop_operations.get_operations_by_tool(
                        #     tool_type.id)
                        # if any(op.status_id for op in drop_operations if self.e_status.get_status_by_id(op.status_id).stype in ["mass_drop_ready", "drop_ready", "mass_drop_init"]):
                        #     continue
                        # Проверка операций в таблице OperationsConsumption
                        # consumption_operations = self.e_operations_consumption.get_operations_by_tool(
                        #     tool_type.id)
                        # if consumption_operations:
                        #     continue
                        # Проверка операций в таблице LoadOperations
                        # load_operations = self.e_load_operations.get_operations_by_tool(
                        #     tool_type.id)
                        # found = False  # предполагаем, что ни один статус не подходит
                        #
                        # for op in load_operations:
                        #     status = self.e_status.get_status_by_id(
                        #         op.status_id)  # получаем объект статуса
                        #     if status.stype in ["mass_load_ready", "load_ready"]:  # проверка нужного типа
                        #         found = True
                        #         break  # нашли хотя бы один — дальше не надо
                        #
                        # if not found:
                        #     continue
                        # if len(load_operations) == 0 or load_operations == []:
                        #     continue

                        # Если инструмент прошёл все проверки, добавляем его в список
                        # valid_tools.append(tool)
                        # valid_tools.append(create_tool_dict(cell, tool_type))
                        # Для списка "свободного" инструмента учитываем только загрузки без plan_id.
                        loads = self.e_load.find_by_cell_id(cell.id)
                        load = max(loads, key=lambda rec: rec.id) if loads else None
                        if load and load.plan_id is None:
                            valid_tools_count += 1

            logger.debug(f"tool_type: {tool_type}, valid_tools_count: {valid_tools_count}")

            if valid_tools_count > 0:
                valid_tool_types.append(create_tool_types_dict(tool_type, valid_tools_count))

            logger.debug(f"valid_tool_types: {valid_tool_types}")
        return valid_tool_types, group_name

    def read_db_plan_operations(self, plans_id: int) -> list[dict]:
        """
        Возвращает все операции пользователей с инструментами, связанные с чертежом,
        из таблиц History, LoadOperations, DropOperations и OperationsConsumption.

        :param plans_id: ID чертежа, для которого извлекаются операции.
        :return: Список операций в формате словарей.
        """
        try:
            # Получаем все инструменты, связанные с указанным чертежом
            # tools = self.e_tools.get_tools_by_plan(plans_id)
            # tools_ids = [tool.id for tool in tools]

            # TODO: добавить в History поле plan_id, выполнять поиск по plan_id
            plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plans_id)
            history_records = []
            for plan_tool_type in plan_tool_types:
                # Получаем все записи из таблицы History, связанные с инструментами чертежа
                stories = self.e_history.get_history_by_tool(plan_tool_type.tool_types_id)
                for history in stories:
                    history_records.append(history)

            operations = []

            # Лямбда для создания словаря операции
            def create_operation_dict(history, op, additional_fields): return {
                "datetime": history.datetime,
                "user_name": self.e_user.get_user_by_id(history.user_id).first_name,
                "user_family": self.e_user.get_user_by_id(history.user_id).family,
                "role_name": get_role_display_name(self.e_role.get_role_by_id(self.e_user.get_user_by_id(history.user_id).role_id).name),
                "history_description": history.description,
                "tools_name": self.e_tool_types.get_tool_type_by_id(history.tools_id).name,
                "group_name": self.e_group.get_group_by_id(self.e_tool_types.get_tool_type_by_id(history.tools_id).groups_id).name,
                "plan_name": self.e_plan.get_plan_by_id(self.e_tool_types.get_tool_type_by_id(history.tools_id).plan_id).name,
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
            logger.debug(f"Ошибка при извлечении операций для чертежа: {e}")
            logger.exception("")
            return []

    def read_db_history(self, index) -> list[dict]:
        logger.debug("actions_db read_db_history(%s)".format( index))
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

                # print(f"user: {user}, tool: {self.e_tool_types.get_tool_type_by_id(history.tools_id)}, op: {add_cell_number(op)}")

                return {
                    "datetime": history.datetime,
                    "user_name": f"{user.family} {user.first_name} {user.second_name}",
                    # "user_name": self.e_user.get_user_by_id(history.user_id).first_name,
                    # "user_family": self.e_user.get_user_by_id(history.user_id).family,
                    "role_name": get_role_display_name(self.e_role.get_role_by_id(self.e_user.get_user_by_id(history.user_id).role_id).name),
                    # "history_description": history.description,
                    "tools_name": self.e_tool_types.get_tool_type_by_id(history.tools_id).name,
                    "group_name": self.e_group.get_group_by_id(self.e_tool_types.get_tool_type_by_id(history.tools_id).groups_id).name,
                    # "plan_name": self.e_plan.get_plan_by_id(self.e_tool_types.get_tool_type_by_id(history.tools_id).plan_id).name,
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
                    loads = self.e_load.find_by_cell_id(consumption.cell_id)
                    if loads:
                        load = loads[0]
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
                    load_operations = self.e_load_operations.get_operations_by_history_id(
                        history.id)
                    operations.extend([create_operation_dict(
                        history, op) for op in load_operations])
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
            logger.debug(f"Ошибка при извлечении всех операций: {e}")
            logger.exception("")
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
                "role_name": get_role_display_name(self.e_role.get_role_by_id(self.e_user.get_user_by_id(history.user_id).role_id).name),
                "history_description": history.description,
                "tools_name": self.e_tool_types.get_tool_type_by_id(history.tools_id).name,
                "group_name": self.e_group.get_group_by_id(self.e_tool_types.get_tool_type_by_id(history.tools_id).groups_id).name,
                "plan_name": self.e_plan.get_plan_by_id(self.e_tool_types.get_tool_type_by_id(history.tools_id).plan_id).name,
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
            logger.debug(f"Ошибка при извлечении операций пользователя: {e}")
            logger.exception("")
            return []

    def read_db_mass_drop_tools(self, index) -> List[dict]:
        logger.debug("read_db_mass_drop_tools. index: %s".format( index))
        """
        Возвращает список ячеек по всем ещё не обработанным массовым выгрузкам (все concurrent mass_drop).
        Объединяет инструменты из клиентской и серверной массовых выгрузок в одном меню.
        """
        def create_cell_dict(cell, tool_type):
            # Safe lookups with null checks to prevent AttributeError
            group = self.e_group.get_group_by_id(cell.groups_id) if cell.groups_id else None

            return {
                "group_name": group.name if group else "Без группы",
                "tools_name": tool_type.name if tool_type else "Неизвестный инструмент",
                "cell_number": cell.number,
            }

        try:
            statuses = self.e_status.all()
            status_init_id = next(
                (s.id for s in statuses if s.stype == "mass_drop_init"), None)
            if status_init_id is None:
                return []

            # Все Drop со статусом mass_drop_init из любых MassDrop (клиент, сервер) — одно общее меню
            drops = self.e_drop.all()
            drops_pending = [d for d in drops if d.status_id == status_init_id]
            logger.debug(f"drops pending (all mass_drops): {len(drops_pending)}")

            cells_ids = set()
            cell_list = []
            for drop in drops_pending:
                cell = self.e_cell.get_cell_by_id(drop.cell_id)
                # Проверяем, что Cell существует, уникальна и имеет статус mass_drop_init
                if cell and cell.id not in cells_ids and cell.status_id == status_init_id:
                    cells_ids.add(cell.id)
                    tool_type = self.e_tool_types.get_tool_type_by_id(cell.tools_id) if cell.tools_id else None
                    cell_list.append(create_cell_dict(cell, tool_type))
                elif cell and cell.status_id != status_init_id:
                    logger.debug(f"Cell {cell.id} (number={cell.number}) skipped: status_id={cell.status_id} != mass_drop_init({status_init_id})")

            logger.debug(f"cell_list: {len(cell_list)}")
            return cell_list

        except Exception as e:
            logger.debug(f"Ошибка при выполнении запроса: {e}")
            logger.exception("")
            return []

    def read_db_mass_drop_tools_by_plan(self, plan_id: int) -> List[ToolTypes]:
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
        # tools = self.e_tools.all()
        tool_types = self.e_tool_types.all()
        plan_tools = []
        plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan_id)
        for plan_tool_type in plan_tool_types:
            plan_tools.append(plan_tool_type.tool_types_id)
        # plan_tools = [
        #     tool for tool in tools if tool.id in tools_ids_in_drops and tool.plan_id == plan_id]

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

    def read_db_mass_drop_tools_by_free(self) -> List[ToolTypes]:
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
        # tools = self.e_tools.all()
        tool_types = self.e_tool_types.all()
        free_tools = []
        # free_tools = [
        #     tool for tool in tools if tool.id in tools_ids_in_drops and tool.plan_id is None]

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
        logger.debug("write_db_drop_tool_groups %s".format(_))
        result = True
        user_id = self.current_user.id

        try:

            statuses = self.e_status.all()
            status_init = next(
                (s.id for s in statuses if s.stype == "mass_drop_init"), None)

            # Получить статус "расход"
            status_ready = self.e_status.find_by_name("mass_drop_ready")
            if not status_ready:
                logger.debug("Статус «Инструмент извлечён из аппарата» не найден.")
                index = max(self.e_status.get_all_ids(), default=0) + 1
                self.e_status.add(
                    index=index,
                    stype="mass_drop_ready",
                    description="Инструмент извлечён из аппарата",
                    created_at=datetime.datetime.now()
                )
                status_ready = self.e_status.get_status_by_id(status_id=index)

            target_histories = []
            target_cells = []
            target_tools = []
            target_drops = []  # только обработанные (все concurrent mass_drop с ячейкой в mass_drop_init)

            drops = self.e_drop.all()
            logger.debug(f"drops (all): {len(drops)}")
            for drop in drops:
                cell = self.e_cell.get_cell_by_id(drop.cell_id)
                if cell and cell.status_id == status_init:
                    target_drops.append(drop)
                    history = self.e_history.get_history_by_id(drop.history_id)
                    target_histories.append(history)

                    target_cells.append(self.e_cell.get_cell_by_id(drop.cell_id))
                    tool_type = self.e_tool_types.get(drop.tools_id)

                    # Если группа не найдена — создаём новую с именем первого слова из tool.name
                    group = self.e_group.get_group_by_id(tool_type.groups_id)
                    if group is None:
                        first_word = tool_type.name.split()[0]
                        new_group_id = max(
                            self.e_group.get_all_ids(), default=0) + 1
                        self.e_group.add(id=new_group_id, name=first_word)
                        tool_type.groups_id = new_group_id

                    # target_tools.append(self.e_tools.get(load.tools_id))
                    target_tools.append(self.e_tool_types.get_tool_type_by_id(drop.tools_id))

            for cell in target_cells:
                result = result and self.e_cell.update_cell(
                    cell_id=cell.id,
                    number=cell.number,
                    description='Старт',
                    groups_id=None,
                    tools_id=None,
                    status_id=1,
                )

            for history in target_histories:
                user = self.e_user.get(user_id)
                history_id = max(self.e_history.get_all_ids()) + 1
                result = result and self.e_history.add_history(
                    id=history_id,
                    user_id=user.id,
                    role_id=user.role_id,
                    tools_id=history.tools_id,
                    datetime_value=datetime.datetime.now(),
                    status=status_ready.id,
                    description=status_ready.description,
                    plan_id=history.plan_id,
                )

            for drop in target_drops:
                drop_dict = drop.to_dict()
                drop_dict['status_id'] = status_ready.id
                self.e_drop.update(index=drop.id, **drop_dict)

            self.e_mass_drop._cache.clear()
            self.e_drop._cache.clear()
            self.e_history._cache.clear()
            self._invalidate_availability_caches("write_db_drop_tool_groups")

            return result

        except Exception as e:
            logger.debug(e)
            logger.exception("")
            return False

    def write_db_load_tool_groups(self, _) -> bool:
        """
        Обновляет записи в таблицах LoadOperations и Cell для группы инструментов, помечая их как готовые для работы.

        :return: True, если операция выполнена успешно, иначе False.
        """
        result = True
        user_id = self.current_user.id
        # status = 0
        # description = "Готов к выдаче"
        try:

            statuses = self.e_status.all()
            status_init = next(
                (s.id for s in statuses if s.stype == "mass_load_init"), None)

            # status_ready = next(
            #     (s.id for s in statuses if s.stype == "mass_load_ready"), None)

            # target_operations = []
            target_histories = []
            target_cells = []
            target_tools = []

            loads = self.e_load.all()
            logger.debug(f"loads: {loads}")
            for load in loads:
                cell = self.e_cell.get_cell_by_id(load.cell_id)
                if cell and cell.status_id == status_init:
                    history = self.e_history.get_history_by_id(load.history_id)
                    target_histories.append(history)

                    target_cells.append(self.e_cell.get_cell_by_id(load.cell_id))
                    tool_type = self.e_tool_types.get(load.tools_id)

                    # Если группа не найдена — создаём новую с именем первого слова из tool.name
                    group = self.e_group.get_group_by_id(tool_type.groups_id)
                    if group is None:
                        first_word = tool_type.name.split()[0]
                        new_group_id = max(
                            self.e_group.get_all_ids(), default=0) + 1
                        self.e_group.add(id=new_group_id, name=first_word)
                        tool_type.groups_id = new_group_id

                    # target_tools.append(self.e_tools.get(load.tools_id))
                    target_tools.append(self.e_tool_types.get_tool_type_by_id(load.tools_id))

            # mass_loads = self.e_mass_load.all()
            # for mass_load in mass_loads:
            #     # Получаем список загрузок инструментов связанных с последней массовой загрузкой.
            #     loads_by_mass_load = self.e_load.find_by_mass_load_id(mass_load.id)
            #     for load in loads_by_mass_load:
            #         operations = self.e_load_operations.get_operations_by_load_id(load.id)
            #         if len(operations) == 1 and operations[0].status_id == status_init:
            #             target_operations.append(operations)
            #
            #         target_cells.append(self.e_cell.get(load.cell_id))
            #
            #         tool_type = self.e_tool_types.get(load.tools_id)
            #
            #         # Если группа не найдена — создаём новую с именем первого слова из tool.name
            #         group = self.e_group.get(tool_type.groups_id)
            #         if group is None:
            #             first_word = tool_type.name.split()[0]
            #             new_group_id = max(
            #                 self.e_group.get_all_ids(), default=0) + 1
            #             self.e_group.add(id=new_group_id, name=first_word)
            #             tool_type.groups_id = new_group_id
            #
            #         # target_tools.append(self.e_tools.get(load.tools_id))
            #         target_tools.append(self.e_tool_types.get_tool_type_by_id(load.tools_id))

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

            for cell in target_cells:
                result = result and self.e_cell.update_cell(
                    cell_id=cell.id,
                    number=cell.number,
                    description=ready_status.description,
                    groups_id=cell.groups_id,
                    tools_id=cell.tools_id,
                    status_id=ready_status.id,
                )
            # Добавляем запись операций в LoadOperations и ячеек в Cell о готовности к использованию.
            # for operations in target_operations:
            #     access = True
            #     for operation in operations:
            #         status = self.e_status.get_status_by_id(
            #             operation.status_id)
            #         if 'ready' in status.stype and not access:
            #             access = False
            #     if access:
            #         user = self.e_user.get(user_id)
            #         history_id = max(self.e_history.get_all_ids()) + 1
            #         result = result and self.e_history.add_history(
            #             id=history_id,
            #             user_id=user.id,
            #             role_id=user.role_id,
            #             tools_id=operations[0].load_tools_id,
            #             datetime_value=datetime.datetime.now(),
            #             status=status,
            #             description=description,
            #         )
            #         # Добавляем информацию о разрешении на использование инструмента
            #         load_operations_id = max(
            #             self.e_load_operations.get_all_ids()) + 1
            #         result = result and self.e_load_operations.add_operation(
            #             id=load_operations_id,
            #             date=datetime.datetime.now(),
            #             load_id=operations[0].load_id,
            #             load_tools_id=operations[0].load_tools_id,
            #             status_id=ready_status_id,
            #             history_id=history_id,
            #             description=operations[0].description,
            #         )
            #         # Обновляем статус ячейки
            #         load = self.e_load.get(operations[0].load_id)
            #         cell = self.e_cell.get(load.cell_id)
            #         cell.description = description
            #         if cell:
            #             result = result and self.e_cell.update_cell(
            #                 **(cell.to_dict()))

            # Добавляем новые записи истории
            for history in target_histories:
                user = self.e_user.get(user_id)
                history_id = max(self.e_history.get_all_ids()) + 1
                result = result and self.e_history.add_history(
                    id=history_id,
                    user_id=user.id,
                    role_id=user.role_id,
                    tools_id=history.tools_id,
                    datetime_value=datetime.datetime.now(),
                    status=ready_status.id,
                    description=ready_status.description,
                    plan_id=history.plan_id,
                )
                # # Обновляем статус ячейки
                # cell = self.e_cell.get(load.cell_id)
                # cell.description = description
                # if cell:
                #     result = result and self.e_cell.update_cell(
                #         **(cell.to_dict()))

            for load in loads:
                load_dict = load.to_dict()
                load_dict['status_id'] = ready_status.id
                self.e_load.update(index=load.id, **load_dict)


            self.e_mass_load._cache.clear()
            self._invalidate_availability_caches("write_db_load_tool_groups")
            logging.info("Cache cleared for mass load confirmation")

            return result
        except Exception as e:
            logger.debug(e)
            logger.exception("")
            return False

    def read_db_groups(self):
        """
        Получает список всех групп из базы данных с количеством доступных инструментов по каждой группе.
        Доступное количество считается по ячейкам Cell с статусом 3 или 7, свободной нагрузке (Load.plan_id is None)
        и отсутствию записи выдачи для свободного инструмента (Consumption с plan_id is None).

        :return: Словарь {Group: count} для корневых групп.
        """

        # TODO: Вынести в утилитарный класс
        def sum_parent_count(group_count_dict: dict[Group, int], group: Group, count):
            if group.paren_group_id == 0:
                if group_count_dict.get(group) is not None:
                    group_count_dict[group] += count
                elif count > 0:
                    group_count_dict[group] = count
            else:
                parent_group = self.e_group.get_group_by_id(group.paren_group_id)
                sum_parent_count(
                    group_count_dict, parent_group, count)

        self._invalidate_availability_caches("read_db_groups")

        try:

            group_count_dict = {}

            # Получаем все подгруппы указанной группы
            groups = self.e_group.get_all_groups()
            for group in groups:
                tool_types = self.e_tool_types.get_tool_types_by_group(group.id)
                logger.debug(f"group: {group}")

                count = 0

                for tool_type in tool_types:
                    logger.debug(f"tool_type: {tool_type}")

                    # tools = self.e_tools.get_tools_by_tool_type_id(tool_type.id)
                    # print(f"tools {tools}")
                    # if tools:
                    #     for tool in tools:
                    cells = self.e_cell.get_cells_by_tool(tool_type.id)
                    if cells:
                        for cell in cells:
                            logger.debug(f"cell: {cell}")
                            if cell.status_id in [3, 7]:
                                loads = self.e_load.find_by_cell_id(cell.id)
                                load = max(loads, key=lambda rec: rec.id) if loads else None
                                if not load:
                                    logger.info(
                                        "read_db_groups: ячейка cell_id=%s (number=%s) не в счёте — нет записи Load для ячейки",
                                        cell.id, getattr(cell, 'number', None),
                                    )
                                    continue
                                if load.plan_id is not None:
                                    logger.info(
                                        "read_db_groups: ячейка cell_id=%s (number=%s) не в счёте — Load.plan_id=%s (учёт только свободной выдачи, plan_id должен быть None)",
                                        cell.id, getattr(cell, 'number', None), load.plan_id,
                                    )
                                    continue
                                # Не считаем доступной ячейку, уже выданную как свободный инструмент (есть Consumption без plan_id),
                                # если только после этой выдачи не было новой загрузки (Load новее Consumption — ячейка снова доступна).
                                consumptions = self.e_consumption.get_by_cell_id(cell.id)
                                consumptions_free = [c for c in consumptions if c.plan_id is None]
                                if consumptions_free:
                                    max_consumption_history = max(c.history_id for c in consumptions_free)
                                    if load.history_id <= max_consumption_history:
                                        logger.info(
                                            "read_db_groups: ячейка cell_id=%s (number=%s) не в счёте — уже есть Consumption с plan_id is None и Load не новее (инструмент выдан как свободный)",
                                            cell.id, getattr(cell, 'number', None),
                                        )
                                        continue
                                count += 1

                logger.debug(f"group: {group}, count: {count}")

                sum_parent_count(group_count_dict, group, count)

            logger.debug(f"group_count_dict: {group_count_dict}")

            return group_count_dict

        except Exception as e:
            logger.debug(f"Ошибка при получении списка групп: {e}")
            logger.exception("")
            return []

    def read_db_group_collection(self, index):
        """
        Получает коллекцию объектов, связанных с группами из базы данных.
        Filters to only include root groups that have tools in cells with status_id 3 or 7.

        :return: Словарь, где ключи - идентификаторы групп, а значения - связанные объекты (Tools, Cells и т.д.).
        """
        self._invalidate_availability_caches("read_db_group_collection")
        try:
            group_collection = {}
            valid_root_groups = set()

            # Get all cells with status_id in {3,7}
            cells = self.e_cell.all()
            for cell in cells:
                if cell.status_id in [3, 7] and cell.tools_id:
                    tool = self.e_tool_types.get_tool_type_by_id(cell.tools_id)
                    if tool and tool.groups_id:
                        # Trace to root
                        current_id = tool.groups_id
                        while current_id:
                            group = self.e_group.get_group_by_id(current_id)
                            if not group:
                                break
                            if group.paren_group_id == 0:
                                valid_root_groups.add(group.id)
                                break
                            current_id = group.paren_group_id

            # Populate group_collection only for valid_root_groups
            for group_id in valid_root_groups:
                group = self.e_group.get_group_by_id(group_id)
                if group:
                    # tools = self.e_tools.get_tools_by_group(group_id)
                    tool_types = self.e_tool_types.get_tool_types_by_group(group_id)
                    cells = self.e_cell.get_cells_by_group(group_id)
                    group_collection[group_id] = {
                        "group": group,
                        "tools": tool_types,
                        "cells": cells
                    }

            return group_collection

        except Exception as e:
            logger.debug(f"Ошибка при получении коллекции групп: {e}")
            logger.exception("")
            return {}

    def read_db_users(self, index) -> List[User]:
        logger.debug("read_db_users")
        """
        Получает список всех пользователей из базы данных.

        :return: Список объектов User. Пустой список, если пользователей нет.
        """
        try:
            # Получение всех пользователей
            users = self.e_user.get_all_users()
            logger.debug(users)
            return users if users else []
        except Exception as e:
            logger.debug(f"Ошибка при получении списка пользователей: {e}")
            logger.exception("")
            return []

    def read_db_username(self, code: int) -> Optional[str]:
        logger.debug("read_db_username. Input code: %s".format( code))
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
            username = f"{user.family} {user.first_name} {user.second_name}".strip()
            logger.debug(f"read_db_username. Found username: {username}")
            return username if username else None  # Возвращает None, если username пустой

        except Exception as e:
            logger.debug(f"Ошибка при получении имени пользователя: {e}")
            logger.exception("")
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
            logger.debug(f"Ошибка при получении пользователя по штрих-коду: {e}")
            logger.exception("")
            return {'trigger': 'err_barcode'}

    def read_db_authorization(self, login: int, password: int):
        """
        Получает пользователя и связанную с ним роль по логину и паролю.

        :param login: Логин пользователя (Code).
        :param password: Пароль пользователя.
        :return: Кортеж (пользователь, роль), если найдено, иначе (None, None).
        """
        logger.debug("read_db_authorization. login: %s, password: %s".format( login, password))
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
            logger.debug(
                f"read_db_authorization. current_user: {user}, current_role: {role}")
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
            logger.debug(f"Ошибка при авторизации пользователя: {e}")
            logger.exception("")
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
            logger.debug(f"Ошибка при записи данных пользователя: {e}")
            logger.exception("")
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
            logger.debug(
                f"Ошибка при записи прав для пользователя с ID {user_id}: {e}")
            logger.exception("")
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
                logger.debug(f"Для роли с ID {role_id} не найдены права доступа.")
                return []

            return rights

        except Exception as e:
            logger.debug(
                f"Ошибка при получении прав для пользователя с ID {user_id}: {e}")
            logger.exception("")
            return []

    def read_db_get_plan_tools(self, plan_id, plan_designation, plan_name):
        print(f"read_db_get_plan_tools plan_designation %s, plan_name %s", plan_designation, plan_name)
        logger.debug("read_db_get_plan_tools plan_designation %s, plan_name %s".format(plan_designation, plan_name))

        plan = self.e_plan.get_plan_by_id(plan_id)
        self.select_plan = plan

        plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan_id)

        plan_tool_list = []

        for plan_tool_type in plan_tool_types:
            tool_object = {}
            tool_type = self.e_tool_types.get_tool_type_by_id(plan_tool_type.tool_types_id)

            tool_object["tool_type"] = tool_type
            tool_object["total_count"] = tool_type.count
            tool_object["plan_count"] = plan_tool_type.tool_types_count

            # Доступные для выдачи по плану: только ячейки со статусом 3 или 7 и привязкой Load к чертежу.
            # Ячейки, инициализированные до подтверждения массовой загрузки, не считаются свободными.
            tool_available_count = 0
            cells = self.e_cell.get_cells_by_tool(tool_type.id)
            for cell in cells:
                if cell.status_id not in [3, 7]:
                    continue
                loads = self.e_load.find_by_cell_id(cell.id)
                load = max(loads, key=lambda rec: rec.id) if loads else None
                if self.select_plan and load and load.plan_id == self.select_plan.id:
                    tool_available_count += 1

            tool_object["load_count"] = tool_available_count

            if plan_tool_type.tool_types_count <= tool_available_count:
                has_tools = True
            else:
                has_tools = False

            tool_object["has_tools"] = has_tools

            plan_tool_list.append(tool_object)

        return plan_tool_list, plan_designation, plan_name, plan_id

    def read_db_plan_complete(self, plan_id):
        logger.debug("read_db_plan_complete plan_id %s".format(plan_id))

        plan = self.e_plan.get_plan_by_id(plan_id)
        # self.select_plan = plan

        plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan_id)

        plan_tool_list = []

        for plan_tool_type in plan_tool_types:
            tool_object = {}
            tool_type = self.e_tool_types.get_tool_type_by_id(plan_tool_type.tool_types_id)

            tool_object["tool_type"] = tool_type
            tool_object["total_count"] = tool_type.count
            tool_object["plan_count"] = plan_tool_type.tool_types_count

            # Доступные для выдачи по плану: только ячейки со статусом 3 или 7 и привязкой Load к чертежу (аналогично read_db_get_plan_tools).
            tool_available_count = 0
            cells = self.e_cell.get_cells_by_tool(tool_type.id)
            for cell in cells:
                if cell.status_id not in [3, 7]:
                    continue
                loads = self.e_load.find_by_cell_id(cell.id)
                load = max(loads, key=lambda rec: rec.id) if loads else None
                if plan and load and load.plan_id == plan.id:
                    tool_available_count += 1

            tool_object["load_count"] = tool_available_count

            if plan_tool_type.tool_types_count <= tool_available_count:
                has_tools = True
            else:
                has_tools = False

            tool_object["has_tools"] = has_tools

            plan_tool_list.append(tool_object)

        logger.debug("read_db_plan_complete call view_plan_complete plan_id=%s, designation=%s, tool_list=%s".format( plan_id, plan.designation, plan_tool_list))
        return {'plan_id': plan_id, 'designation': plan.designation, 'tool_list': plan_tool_list}


    def write_db_plan_complete(self, plan_id):
        logger.debug("write_db_plan_complete plan_id %s".format(plan_id))

        result = True
        user_id = self.current_user.id

        plan = self.e_plan.get_plan_by_id(plan_id)
        # self.select_plan = plan

        plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan_id)

        # target_histories = []
        # target_cells = []
        # target_tools = []
        # target_loads = []
        drops = []

        for plan_tool_type in plan_tool_types:
            # tool_type = self.e_tool_types.get_tool_type_by_id(plan_tool_type.tool_types_id)
            # target_tools.append(tool_type)

            cells = self.e_cell.get_cells_by_tool(plan_tool_type.tool_types_id)
            for cell in cells:
                if cell.status_id in [3, 7]:
                    loads = self.e_load.find_by_cell_id(cell.id)
                    load = max(loads, key=lambda rec: rec.id) if loads else None
                    if self.select_plan and load and load.plan_id == self.select_plan.id:
                        history = self.e_history.get_history_by_id(load.history_id)
                        # target_histories.append(history)
                        # target_cells.append(cell)
                        # target_loads.append(load)
                        drops.append({'cell': cell, 'load': load, 'history': history})

        # 1. Найти или создать статус "mass_drop_init"
        all_statuses = self.e_status.all()
        mass_drop_status = next(
            (s for s in all_statuses if s.stype == "mass_drop_init"), None)

        if not mass_drop_status:
            mass_drop_status_id = max(self.e_status.get_all_ids(), default=0) + 1
            self.e_status.add(
                index=mass_drop_status_id,
                stype="mass_drop_init",
                description="Начальный статус для массового удаления"
            )
            mass_drop_status = self.e_status.get(mass_drop_status_id)

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

        for drop in drops:
            logger.debug(f"drop {drop}")
            cell = drop["cell"]
            load = drop["load"]
            history = drop["history"]

            tool_type = self.e_tool_types.get_tool_type_by_id(cell.tools_id)
            logger.debug(f"tool_type {tool_type}")

            result = result and self.e_cell.update_cell(
                cell_id=cell.id,
                number=cell.number,
                description=mass_drop_status.description,
                groups_id=cell.groups_id,
                tools_id=cell.tools_id,
                status_id=mass_drop_status.id,
            )

            # Добавляем новые записи истории
            user = self.e_user.get(user_id)
            history_id = max(self.e_history.get_all_ids()) + 1
            result = result and self.e_history.add_history(
                id=history_id,
                user_id=user.id,
                role_id=user.role_id,
                tools_id=tool_type.id,
                datetime_value=datetime.datetime.now(),
                status=mass_drop_status.id,
                description=mass_drop_status.description,
                plan_id=load.plan_id,
            )

            drop_id = max(self.e_drop.get_all_ids(), default=0) + 1

            # 3. Создать записи в таблице Drop
            result = result and self.e_drop.add_drop(
                index=drop_id,
                tools_id=tool_type.id,
                mass_drop_id=mass_drop_id,
                cell_id=cell.id,
                plan_id=plan_id,
                history_id=history_id,
                status_id=mass_drop_status.id,
                created_at=datetime.datetime.now(),
                description=f"Выгрузка инструмента {tool_type.name} для чертежа {plan.designation}"
            )

            if not result:
                raise ValueError("Не удалось создать записи в таблице Drop.")

            drops_by_cell = self.e_drop.get_by_cell_id(cell.id)
            drops_by_cell.sort(key=lambda rec: rec.id, reverse=True)

            operation_indx = self.e_drop_operations.get_all_ids()
            operation_indx = max(operation_indx, default=0) + 1

            operation_added = self.e_drop_operations.add_operation(
                index=operation_indx,
                drop_id=drops_by_cell[0].id,
                tools_id=tool_type.id,
                status_id=mass_drop_status.id,
                history_id=history_id,
                description="Создана операция массового удаления",
            )

            logger.debug(f"operation_added {operation_added}")

            if not operation_added:
                raise ValueError(
                    f"Не удалось создать запись в таблице DropOperations для Drop ID {drops_by_cell[0]}.")

        plan_dict = plan.to_dict()
        plan_dict['hidden'] = True
        self.e_plan.update(index=plan.id, **plan_dict)

        # Инвалидация кеша после завершения чертежа — чтобы меню массовой выгрузки и выдача по плану видели актуальные данные
        self.e_drop._cache.clear()
        self.e_mass_drop._cache.clear()
        self.e_cell._cache.clear()
        self.e_history._cache.clear()
        self.e_plan._cache.clear()

        return {"trigger": "plan_completed"}

    def read_db_plans(self, index):
        print(f"read_db_plans index %s", index)
        logger.debug("read_db_plans index %s".format(index))
        """
        Читает данные о всех чертежах из таблицы Plan.

        :return: Список словарей, содержащих данные о чертежах,
                 или пустой список, если чертежи отсутствуют.
        """
        self.select_plan = None
        try:
            # Получаем список всех чертежей
            plans = self.e_plan.get_all_plans()
            logger.debug(f"plans {plans}")

            # Статусы подтверждённой загрузки: только по именам
            ready_status_ids = set()
            load_ready = self.e_status.find_by_name("load_ready")
            mass_load_ready = self.e_status.find_by_name("mass_load_ready")
            if load_ready and getattr(load_ready, "id", None) is not None:
                ready_status_ids.add(load_ready.id)
            if mass_load_ready and getattr(mass_load_ready, "id", None) is not None:
                ready_status_ids.add(mass_load_ready.id)

            # Формируем список словарей с данными о чертежах
            plans_data = []
            for plan in plans:
                if plan.hidden:
                    continue

                # Показываем только планы, у которых есть хотя бы один инструмент
                # с подтверждённой загрузкой под этот план.
                has_ready_tools = False
                plan_tool_types = self.e_plan_tool_types.get_plan_tool_types_by_plan_id(plan.id)
                for plan_tool_type in plan_tool_types:
                    cells = self.e_cell.get_cells_by_tool(plan_tool_type.tool_types_id)
                    for cell in cells:
                        if cell.status_id not in ready_status_ids:
                            continue
                        loads = self.e_load.find_by_cell_id(cell.id)
                        load = max(loads, key=lambda rec: rec.id) if loads else None
                        if load and load.plan_id == plan.id:
                            has_ready_tools = True
                            break
                    if has_ready_tools:
                        break

                if not has_ready_tools:
                    continue

                plans_data.append({
                    'id': plan.id,
                    'enterprise': plan.enterprise,
                    'barcode': plan.barcode,
                    'name': plan.name,
                    'description': plan.description,
                    'designation': plan.designation,
                    'index_list': plan.index_list,
                    'list_count': plan.list_count,
                    'parent_plan_id': plan.parent_plan_id
                })
            logger.debug(f"plans_data {plans_data}")

            return plans_data

        except Exception as e:
            logger.debug(f"Ошибка при чтении данных чертежей: {e}")
            logger.exception("")
            return []

    def read_db_plan_id(self, barcode):
        logger.debug("read_db_plan_id. barcode: %s", barcode)
        """
        Получает идентификатор чертежа по штрих-коду из базы данных.
        Парсит строку QR-кода, извлекая designation из первого блока и добавляя блок 4 через дефис.

        :param barcode: Штрих-код чертежа (может быть словарем {'barcode': str} или строкой).
        :return: Идентификатор чертежа (int), если чертеж найден, иначе None.
        """
        try:
            # Извлекаем строку из словаря, если barcode - словарь
            if isinstance(barcode, dict):
                barcode_str = barcode.get('barcode', '')
            else:
                barcode_str = str(barcode)
            
            if not barcode_str:
                logger.debug(f"read_db_plan_id: пустой штрих-код")
                return None
            
            logger.debug(f"read_db_plan_id: парсинг строки: {repr(barcode_str)}")
            
            # Парсим строку: сначала по строкам (LF/CRLF), затем по табуляциям, затем fallback по пробелам
            # Примеры:
            # "5108\t01.11.2025 0:00:00\t12.11.2025 8:50:25\t\t39\t\t6\t\t0"
            # "5108  01.11.2025 0:00:00  12.11.2025 8:50:25  Производство  39  Вал  6  шт  0"
            
            designation = ""
            
            normalized = barcode_str.replace('\r\n', '\n').replace('\r', '\n')

            # Вариант 1: Многострочный QR (блоки разделены LF/CRLF)
            if '\n' in normalized:
                parts = [part.strip() for part in normalized.split('\n') if part.strip()]
                logger.debug(f"read_db_plan_id: разбито по LF, блоков: {len(parts)}")
                for i, part in enumerate(parts):
                    logger.debug(f"  Блок [{i}]: {repr(part)}")

                # Блок 0 (первый) -> designation
                if len(parts) > 0:
                    designation = parts[0]

                # Блок 4 (индекс 4) -> добавляется к designation через дефис
                if len(parts) > 4 and parts[4]:
                    block_4 = parts[4]
                    if designation:
                        designation = f"{designation}-{block_4}"
                    else:
                        designation = block_4
                    logger.debug(f"read_db_plan_id: добавлен блок 4, designation: {repr(designation)}")

            # Вариант 2: Если есть табуляции, разбиваем по ним
            elif '\t' in barcode_str:
                parts = barcode_str.split('\t')
                logger.debug(f"read_db_plan_id: разбито по табуляциям, блоков: {len(parts)}")
                for i, part in enumerate(parts):
                    logger.debug(f"  Блок [{i}]: {repr(part)}")
                
                # Блок 0 (первый) → designation
                if len(parts) > 0:
                    designation = parts[0].strip()
                
                # Блок 4 (индекс 4) → добавляется к designation через дефис
                if len(parts) > 4 and parts[4].strip():
                    block_4 = parts[4].strip()
                    if designation:
                        designation = f"{designation}-{block_4}"
                    else:
                        designation = block_4
                    logger.debug(f"read_db_plan_id: добавлен блок 4, designation: {repr(designation)}")
            else:
                # Вариант 3 (fallback): Разбиваем по пробелам (множественным)
                # Используем split() без аргументов для разбиения по любым пробелам
                parts = barcode_str.split()
                logger.debug(f"read_db_plan_id: разбито по пробелам, блоков: {len(parts)}")
                for i, part in enumerate(parts):
                    logger.debug(f"  Блок [{i}]: {repr(part)}")
                
                # Блок 0 (первый) → designation
                if len(parts) > 0:
                    designation = parts[0]
                
                # Блок 4 (индекс 4) → добавляется к designation через дефис
                if len(parts) > 4 and parts[4]:
                    block_4 = parts[4]
                    if designation:
                        designation = f"{designation}-{block_4}"
                    else:
                        designation = block_4
                    logger.debug(f"read_db_plan_id: добавлен блок 4, designation: {repr(designation)}")
            
            if not designation:
                logger.debug(f"read_db_plan_id: не удалось извлечь designation из строки")
                return None
            
            logger.debug(f"read_db_plan_id: итоговый designation: {repr(designation)}")
            
            # Ищем чертеж по designation
            plan = self.e_plan.get_last_plan_by_designation(designation)

            if plan and not plan.hidden:
                logger.debug(f"read_db_plan_id: найден чертеж с ID: {plan.id}")
                return {'plan_id': plan.id}  # Возвращаем идентификатор чертежа
            else:
                logger.debug(f"read_db_plan_id: чертеж с designation {repr(designation)} не найден.")
                return None

        except Exception as e:
            logger.debug(f"read_db_plan_id: ошибка при обработке штрих-кода: {e}")
            import traceback
            logger.exception("")
            return None

            # TODO: временная заглушка на поиск инструмента вместо чертежа
            """
            1. Выполяется поиск всех инструментов по штрихкоду
            2. Выполяется поиск всех ячеек, где есть эти инструменты, и статус = готов к выдаче
            3. Выбирается первая ячейка
            """
            tools = self.e_tools.get_tools_by_barcode(barcode)
            logger.debug(f"tools: {tools}")

            valid_cells = []
            valid_tool_name = ""
            valid_tool = None

            for tool in tools:
                cells = self.e_cell.get_cells_by_tool(tool.id)
                logger.debug(f"cells: {cells}")
                for cell in cells:
                    if cell.status_id == 3:
                        valid_cells.append(cell)
                        valid_tool = tool

            if not valid_tool:
                return None

            valid_tool_name = valid_tool.name
            self.select_tool = valid_tool

            logger.debug(f"valid_cells: {valid_cells}")

            if len(valid_cells) == 0:
                return None
            else:
                cell_number = valid_cells[0].number
                # Если результат пустой, возвращаем None
                if not cell_number:
                    return {"trigger": "err_data"}

                # Предполагается, что инструмент связан с одной ячейкой
                # Возвращаем номер первой найденной ячейки
                return {"trigger": "send_number", "number": cell_number, "tool_name": valid_tool_name} if cell_number else None

        except Exception as e:
            logger.debug(f"Ошибка при чтении идентификатора чертежа: {e}")
            logger.exception("")
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
                        hidden=plan_data['hidden'],
                        parent_plan=0,
                        parent_plan_id=plan_data['parent_plan_id']
                    )
                    if not success:
                        raise ValueError(
                            f"Не удалось добавить новый чертеж с штрих-кодом {plan_data['barcode']}.")

            return True

        except Exception as e:
            logger.debug(f"Ошибка при записи данных чертежей: {e}")
            logger.exception("")
            return False

    def write_db_mass_drop_tools_by_free(self, tools_data: List[ToolTypes], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массового удаления инструментов без привязки к плану.

        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        logger.debug("write_db_mass_drop_tools_by_free. tools_data: %s, cells_data: %s", tools_data, cells_data)
        # # Проверка данных
        # for tool in tools_data:
        #     if tool.plan_id is not None:
        #         raise MassDropToolPlanIDNoneError(
        #             "Значение идентификатора чертежа должно быть пустым (None).")
        # if len(tools_data) != len(cells_data):
        #     raise MassDropLenEqCellToolsError(
        #         f"Значения не могут быть разной длины! tools: {len(tools_data)}, cells: {len(cells_data)}"
        #     )

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

        self._invalidate_availability_caches("write_db_mass_drop_tools_by_free")
        return True

    def write_db_mass_drop_tools_by_plan(self, plan_id: int, tools_data: List[ToolTypes], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массового удаления инструментов по плану.

        :param plan_id: Идентификатор плана, для которого создаётся массовое удаление.
        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        logger.debug("write_db_mass_drop_tools_by_plan. tools_data: %s, cells_data: %s", tools_data, cells_data)
        # # Проверка данных
        # for tool in tools_data:
        #     if not tool.plan_id:
        #         raise MassDropToolPlanIDNoneError(
        #             "Значение идентификатора чертежа не может быть пустым (None)")
        #     if tool.plan_id != plan_id:
        #         raise MassDropPlanIdEQToolsError(
        #             f"Значение идентификатора чертежа в команде записи и "
        #             f"наборе данных не могут быть разными: tool.plan_id={tool.plan_id} != plan_id={plan_id}"
        #         )

        # if len(tools_data) != len(cells_data):
        #     raise MassDropLenEqCellToolsError(
        #         f"Значения не могут быть разной длины! tools: {len(tools_data)}, cells: {len(cells_data)}"
        #     )

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

        self._invalidate_availability_caches("write_db_mass_drop_tools_by_plan")
        return True

    def write_db_mass_load_tools_by_plan(self, plan_id: int, tools_data: List[ToolTypes], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массовой загрузки инструментов по плану.

        :param plan_id: Идентификатор плана, для которого создаётся массовая загрузка.
        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        logger.debug("write_db_mass_load_tools_by_plan. tools_data: %s, cells_data: %s", tools_data, cells_data)
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

        self._invalidate_availability_caches("write_db_mass_load_tools_by_plan")
        return True

    def read_db_mass_load_tools(self, *args, **kwargs) -> List[dict]:
        logger.debug("read_db_mass_load_tools. args: %s, kwargs: %s", args, kwargs)
        """
        Извлекает номера ячеек, связанных с последними операциями массовой загрузки инструментов.
        :return: Список номеров ячеек.
        """

        # Лямбда для создания словаря ячейки
        def create_cell_dict(cell, tool_type):
            # Safe lookups with null checks to prevent AttributeError
            group = self.e_group.get_group_by_id(cell.groups_id) if cell.groups_id else None

            return {
                "group_name": group.name if group else "Без группы",
                "tools_name": tool_type.name if tool_type else "Неизвестный инструмент",
                "cell_number": cell.number,
            }

        try:
            # 1. Найти статус с типом "mass_load_init"
            status = self.e_status.all()
            status_init_id = next(
                (s.id for s in status if s.stype == "mass_load_init"), None)
            logger.debug(f"status_id: {status_init_id}")

            if not status_init_id:
                raise ValueError("Статус 'mass_load_init' не найден.")

            if self.e_mass_load.count() == 0:
                logger.debug(f"Данные о массовой загрузке отсутствуют")
                return []

            cells_ids = set()
            cell_list = []
            # mass_loads = self.e_mass_load.all()
            loads = self.e_load.find_by_status_id(status_init_id)
            loads.sort(key=lambda rec: rec.id, reverse=True)
            logger.debug(f"loads: {loads}")
            for load in loads:
                cell = self.e_cell.get_cell_by_id(load.cell_id)
                # print(f"cell: {cell}")
                # print(f"cell.status_id {cell.status_id} == status_id {status_id}")
                if cell.status_id == status_init_id and cell.id not in cells_ids:
                    cells_ids.add(cell.id)

                    tool_type = self.e_tool_types.get_tool_type_by_id(cell.tools_id)
                    cell_list.append(create_cell_dict(cell, tool_type))
                # operations = self.e_load_operations.get_operations_by_load_id(
                #     load.id)
                # history = self.e_history.get_history_by_id(load.history_id)
                # print(f"operations: {operations}")
                # 2. Найти последние операции загрузки, связанные с этим статусом
                # Проверяем, что есть ровно одна операция и ее статус — mass_load_init
                # if len(operations) == 1 and operations[0].status_id == status_id:
                #     # Если load подходит, добавляем его в список
                #     cells_ids.append(load.cell_id)

            # # Получение идентификаторов загрузок
            # cell_list = []
            # for _id in cells_ids:
            #     cell = self.e_cell.get_cell_by_id(_id)
            #     # print(f"cell: {cell}")
            #     # print(f"tool: {self.e_tool_types.get_tool_type_by_id(cell.tools_id)}")
            #
            #     tool_type = self.e_tool_types.get_tool_type_by_id(cell.tools_id)
            #
            #     cell_list.append(create_cell_dict(cell, tool_type))

            logger.debug(f"cell_list: {cell_list}")
            return cell_list

        except Exception as e:
            logger.debug(f"Ошибка при выполнении запроса: {e}")
            logger.exception("")
            return []

    def write_db_mass_load_tools_by_free(self, tools_data: List[ToolTypes], cells_data: List[Cell]) -> bool:
        """
        Создаёт записи для массовой загрузки инструментов по плану.

        :param tools_data: Список объектов Tools, содержащих данные инструментов.
        :param cells_data: Список объектов Cell, содержащих данные ячеек.
        :return: True, если операция выполнена успешно, иначе False.
        """
        logger.debug("write_db_mass_load_tools_by_free. tools_data: %s, cells_data: %s".format( tools_data, cells_data))
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

        self._invalidate_availability_caches("write_db_mass_load_tools_by_free")
        return True

    def read_db_mass_load_tools_by_plan(self, plan_id):
        """
        Извлекает данные инструментов, связанных с указанным планом.

        :param plan_id: Уникальный идентификатор плана.
        :return: Список инструментов, связанных с указанным планом.
        """
        logger.debug("read_db_mass_load_tools_by_plan. plan_id: %s".format( plan_id))
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
                    # tool = self.e_tools.get(load.tools_id)
                    tool = self.e_tool_types.get_tool_type_by_id(load.tools_id)
                    if tool:
                        tools.append(tool)

            return tools
        except Exception as e:
            # Обработка ошибок
            logger.debug(
                f"Ошибка при чтении инструментов для плана {plan_id}: {str(e)}")
            logger.exception("")
            return []

    def write_db_hal_park_defaults(self, *args, **kwargs):
        """Сохранение park_m1..park_m5 в HardwareConfig (экран тестовой выдачи)."""
        from DB.Engine.DeviceConfigCRUD import EngineDeviceConfig
        from DB.Engine.HardwareConfigCRUD import EngineHardwareConfig
        from EventsSystem.hal_coords import (
            MOT_STEP_MIN,
            message_for_reason,
            mot_axis_max,
            validate_motor_position_texts,
        )

        texts = []
        for i in range(1, 6):
            key = f"park_m{i}"
            if key in kwargs:
                texts.append(str(kwargs[key]))
            else:
                texts.append("")
        positions, bad_index, reason = validate_motor_position_texts(texts)
        if reason:
            label = f"M{bad_index + 1}" if bad_index is not None else ""
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": message_for_reason(
                    reason,
                    motor_label=label,
                    min_v=MOT_STEP_MIN,
                    max_v=mot_axis_max(bad_index) if bad_index is not None else None,
                ),
            }

        e_device = EngineDeviceConfig(session=self.session_local)
        device_cfg = e_device.get_active()
        if not device_cfg:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Конфигурация устройства не найдена",
            }
        e_hw = EngineHardwareConfig(session=self.session_local)
        hw_cfg = e_hw.get_by_device(device_cfg.id)
        if not hw_cfg:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Профиль железа не найден",
            }
        ok = e_hw.update_park_defaults(
            hw_cfg.id,
            park_m1=positions[0],
            park_m2=positions[1],
            park_m3=positions[2],
            park_m4=positions[3],
            park_m5=positions[4],
        )
        if not ok:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Не удалось сохранить парковку",
            }
        payload = {f"park_m{i}": positions[i - 1] for i in range(1, 6)}
        payload["hal_park_save_ok"] = True
        return {"trigger": "view_hal_dispense", **payload}

    def write_db_hal_sol_s_default(self, *args, **kwargs):
        """Сохранение длительности $SOL (секунды) в HardwareConfig."""
        from DB.Engine.DeviceConfigCRUD import EngineDeviceConfig
        from DB.Engine.HardwareConfigCRUD import EngineHardwareConfig
        from EventsSystem.hal_coords import (
            SOL_S_MIN,
            SOL_S_MAX,
            message_for_reason,
            validate_sol_s_text,
        )

        raw = kwargs.get("sol_s")
        if raw is None:
            raw = kwargs.get("sol_s_default")
        value, reason = validate_sol_s_text("" if raw is None else str(raw))
        if reason:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": message_for_reason(
                    reason,
                    motor_label="SOL",
                    min_v=SOL_S_MIN,
                    max_v=SOL_S_MAX,
                ),
            }

        e_device = EngineDeviceConfig(session=self.session_local)
        device_cfg = e_device.get_active()
        if not device_cfg:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Конфигурация устройства не найдена",
            }
        e_hw = EngineHardwareConfig(session=self.session_local)
        hw_cfg = e_hw.get_by_device(device_cfg.id)
        if not hw_cfg:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Профиль железа не найден",
            }
        ok = e_hw.update_sol_s_default(hw_cfg.id, sol_s=value)
        if not ok:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Не удалось сохранить время SOL",
            }
        return {
            "trigger": "view_hal_dispense",
            "sol_s": value,
            "hal_sol_save_ok": True,
        }

    def read_db_cells_hal_list(self, *args, **kwargs):
        """Список ячеек с hal_x/hal_z для screen_41."""
        try:
            rows = self.e_cell.list_cells_hal_summary()
            return {"trigger": "view_hal_cells_table", "cells": rows}
        except Exception as e:
            logger.exception("read_db_cells_hal_list: %s", e)
            return {"trigger": "view_err"}

    def read_db_hal_import_validate(self, *args, **kwargs):
        """Парсинг и валидация CSV перед подтверждением импорта."""
        from EventsSystem.hal_cells_import import (
            confirm_message,
            default_hal_cells_csv_path,
            parse_hal_cells_csv,
        )

        self.__executor.hal_import_rows = None
        self.__executor.hal_import_message = ""
        try:
            known = {
                int(cell.number)
                for cell in self.e_cell.session.query(Cell).all()
                if cell.number is not None
            }
            result = parse_hal_cells_csv(
                default_hal_cells_csv_path(),
                known_numbers=known,
            )
        except Exception as e:
            logger.exception("read_db_hal_import_validate: %s", e)
            self.__executor.hal_import_message = f"Ошибка чтения файла:\n{e}"
            return {
                "trigger": "view_hal_import_err",
                "message": self.__executor.hal_import_message,
            }

        if not result.ok:
            self.__executor.hal_import_message = result.error or "Ошибка импорта"
            return {
                "trigger": "view_hal_import_err",
                "message": self.__executor.hal_import_message,
            }

        self.__executor.hal_import_rows = list(result.rows)
        self.__executor.hal_import_message = confirm_message(
            result.rows, result.path
        )
        return {
            "trigger": "view_hal_import_confirm",
            "message": self.__executor.hal_import_message,
            "count": len(result.rows),
        }

    def write_db_hal_import_coords(self, *args, **kwargs):
        """Запись validated rows из executor в БД одной транзакцией."""
        from EventsSystem.hal_cells_import import success_message

        rows = getattr(self.__executor, "hal_import_rows", None) or []
        if not rows:
            self.__executor.hal_import_message = (
                "Нет данных для импорта. Повторите загрузку файла."
            )
            return {
                "trigger": "view_hal_import_err",
                "message": self.__executor.hal_import_message,
            }
        try:
            self.e_cell.bulk_update_hal_coords(rows)
            cells = self.e_cell.list_cells_hal_summary()
            count = len(rows)
            self.__executor.hal_import_rows = None
            self.__executor.hal_import_message = success_message(count)
            return {
                "trigger": "view_hal_import_ok",
                "message": self.__executor.hal_import_message,
                "cells": cells,
                "count": count,
            }
        except Exception as e:
            logger.exception("write_db_hal_import_coords: %s", e)
            self.__executor.hal_import_rows = None
            self.__executor.hal_import_message = f"Ошибка записи в БД:\n{e}"
            return {
                "trigger": "view_hal_import_err",
                "message": self.__executor.hal_import_message,
            }

    def write_db_cell_hal_coords(self, *args, **kwargs):
        """Запись hal_x/hal_z из MOT3/M1 (screen_38) в ячейку по номеру."""
        from EventsSystem.hal_coords import (
            message_for_reason,
            validate_cell_number_text,
            validate_hal_cell_coords,
        )

        number = getattr(self.__executor, "engineer_cell_number", None)
        if number is None:
            try:
                number = int(kwargs.get("number") or (args[0] if args else 0))
            except (TypeError, ValueError):
                number = None
        if number is not None:
            _parsed, reason = validate_cell_number_text(str(number))
            if reason:
                number = None
        if number is None:
            logger.warning("write_db_cell_hal_coords: номер ячейки не задан")
            return {
                "trigger": "view_hal_coords",
                "hal_input_error": "Ячейка №: укажите номер ячейки",
            }

        cell = self.e_cell.get_cell_by_number(int(number))
        if not cell:
            logger.warning("write_db_cell_hal_coords: ячейка number=%s не найдена", number)
            return {
                "trigger": "view_hal_coords",
                "hal_input_error": "Ячейка с таким номером не найдена",
            }

        hal_x = kwargs.get("hal_x")
        hal_z = kwargs.get("hal_z")
        if hal_x is None:
            hal_x = getattr(self.__executor, "hal_save_hal_x", None)
        if hal_z is None:
            hal_z = getattr(self.__executor, "hal_save_hal_z", None)
        try:
            hal_x = int(hal_x)
            hal_z = int(hal_z)
        except (TypeError, ValueError):
            return {
                "trigger": "view_hal_coords",
                "hal_input_error": "M1/M3: укажите координаты для сохранения",
            }

        ok_coords, reason = validate_hal_cell_coords(hal_x, hal_z)
        if not ok_coords:
            return {
                "trigger": "view_hal_coords",
                "hal_input_error": message_for_reason(reason or ""),
            }

        ok = self.e_cell.update_cell_hal_profile(cell.id, hal_x=hal_x, hal_z=hal_z)
        if not ok:
            logger.warning("write_db_cell_hal_coords: update failed cell_id=%s", cell.id)
            return {
                "trigger": "view_hal_coords",
                "hal_input_error": "Не удалось сохранить координаты",
            }
        return {"trigger": "view_hal_coords", "hal_save_ok": True}

    def read_db_engineer_get_cell(self, *args, **kwargs):
        """Поиск ячейки по номеру для тестовой выдачи (без списания)."""
        number = getattr(self.__executor, "engineer_cell_number", None)
        if number is None:
            try:
                number = int(kwargs.get("number") or (args[0] if args else 0))
            except (TypeError, ValueError):
                number = None
        if number is None:
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Ячейка №: укажите номер ячейки",
            }

        cell = self.e_cell.get_cell_by_number(int(number))
        if not cell:
            logger.warning("read_db_engineer_get_cell: ячейка number=%s не найдена", number)
            return {
                "trigger": "view_hal_dispense",
                "hal_input_error": "Ячейка с таким номером не найдена",
            }

        blocked = self._hal_coords_gate(cell)
        if blocked:
            return blocked

        self.__executor.engineer_wait_context = "dispense"
        tool_name = ""
        if cell.tools_id:
            tool = self.e_tool_types.get_tool_type_by_id(cell.tools_id)
            if tool:
                tool_name = getattr(tool, "name", "") or ""
        return {
            "trigger": "send_number",
            "number": cell.number,
            "cell_id": cell.id,
            "tool_name": tool_name,
        }

    def read_db_engineer_command_ok(self, *args, **kwargs):
        """Маршрут после command_ok_engineer с screen_32_wait."""
        ctx = getattr(self.__executor, "engineer_wait_context", None)
        self.__executor.engineer_wait_context = None
        self.__executor.wait_screen_message = ""
        if ctx == "dispense":
            return {"trigger": "view_hal_dispense"}
        return {"trigger": "view_hal_coords"}

    def execute(self, act, *args, **kwargs):
        try:
            logger.debug(("action_db", "execute", act, args, kwargs))
            return self.__actions[act](*args, **kwargs)
        except Exception as e:
            logger.debug(("action_db", "execute", act, "exception", e))
            logger.exception("")
            try:
                return self.__actions_bad[act]
            except:
                ...
