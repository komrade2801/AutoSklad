import logging
from DB.Models.Cell import Cell
from DB.Models.CellHasDevice import CellHasDevice as Cell_has_Device

logger = logging.getLogger(__name__)
from DB.Models.Command import Command
from DB.Models.Consumption import Consumption
from DB.Models.Device import Device
from DB.Models.Drop import Drop
from DB.Models.DropOperations import DropOperations
from DB.Models.DropOperationsHasDevice import DropOperationsHasDevice as dropOperations_has_Device
from DB.Models.Error import Error
from DB.Models.ErrorHasDevice import ErrorHasDevice as Error_has_Device
from DB.Models.Group import Group
from DB.Models.Help import Help
from DB.Models.History import History
from DB.Models.Identification import Identification
from DB.Models.Load import Load
from DB.Models.LoadOperations import LoadOperations
from DB.Models.LoadOperationsHasDevice import LoadOperationsHasDevice as loadOperations_has_Device
from DB.Models.MassDrop import MassDrop
from DB.Models.MassLoad import MassLoad
from DB.Models.MassDropHasDevice import MassDropHasDevice as mass_drop_has_Device
from DB.Models.MassLoadHasDevice import MassLoadHasDevice as mass_load_has_Device
from DB.Models.OperationsConsumption import OperationsConsumption
from DB.Models.OperationsConsumptionHasDevice import OperationsConsumptionHasDevice as OperationsConsumption_has_Device
from DB.Models.Plan import Plan
from DB.Models.ActualNorm import ActualNorm
from DB.Models.ActualNormHasDevice import ActualNormHasDevice as Quota_has_Device
from DB.Models.Rights import Rights
from DB.Models.Role import Role
from DB.Models.Status import Status
from DB.Models.ToolLocation import ToolLocation as ToolLocation
from DB.Models.Tools import Tools
from DB.Models.ToolsHasDevice import ToolsHasDevice as Tools_has_Device
from DB.Models.Type import Type
from DB.Models.User import User

from DB.Engine.CellCRUD import EngineCell
from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
# from docs.docs import CommandCRUD
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

import inspect

from dbSync.Engines.CommandEngine import CommandCRUD


def get_docstrings(cls, _total=0):
    """
    Собирает docstring из класса и его методов, добавляет зависимости и количество строк.

    Args:
        cls (type): Класс, из которого нужно собрать docstring.

    Returns:
        str: Структурированный docstring, включая зависимости и количество строк.
        :param cls:
        :param _total:
    """
    docstrings = []

    # Добавляем docstring класса с проверкой на None
    class_doc = cls.__doc__.strip() if cls.__doc__ else "Нет описания."
    docstrings.append(f"class: {cls.__name__}\n{class_doc}\n")

    # Проходим по всем методам класса
    for method_name in dir(cls):
        if '__' in method_name and '__init__' not in method_name:
            continue
        method = getattr(cls, method_name)
        if callable(method) and method.__doc__:
            method_doc = method.__doc__.strip()
            docstrings.append(f"{method_name}:\n{method_doc}\n")

    # Получаем путь к файлу с исходным кодом класса
    try:
        source_file = inspect.getfile(cls)
        # docstrings.append(f"Source file: {source_file}\n")

        # Подсчитываем количество строк в файле
        with open(source_file, 'r', encoding='utf-8') as f:
            total_lines = len(f.readlines())
        # docstrings.append(f"Total lines of code: {total_lines}\n")
        _total += total_lines
        # Извлекаем зависимости из файла
        with open(source_file, 'r', encoding='utf-8') as f:
            imports = [line.strip() for line in f if
                       line.strip().startswith("import") or line.strip().startswith("from")]
        dependencies = '\n'.join(imports) if imports else 'No dependencies found.'
        # docstrings.append(f"Dependencies:\n{dependencies}\n")

    except Exception as e:
        docstrings.append(f"Error processing file: {e}\n")

    return {"docstrings": "\n".join(docstrings), "total": _total}


# Пример использования функции
if __name__ == "__main__":

    modules = [
        Cell,
        Cell_has_Device,
        Command,
        Consumption,
        Device,
        Drop,
        DropOperations,
        dropOperations_has_Device,
        Error,
        Error_has_Device,
        Group,
        Help,
        History,
        Identification,
        Load,
        LoadOperations,
        loadOperations_has_Device,
        MassDrop,
        MassLoad,
        mass_drop_has_Device,
        mass_load_has_Device,
        OperationsConsumption,
        OperationsConsumption_has_Device,
        Plan,
        ActualNorm,
        Quota_has_Device,
        Rights,
        Role,
        Status,
        ToolLocation,
        Tools,
        Tools_has_Device,
        ActualNorm,
        Type,
        User
    ]

    engines = [
        EngineCell,
        EngineCellHasDevice,
        CommandCRUD,
        EngineConsumption,
        EngineDevice,
        EngineDrop,
        EngineDropOperations,
        EngineDropOperationsHasDevice,
        EngineError,
        EngineErrorHasDevice,
        EngineGroup,
        EngineHelp,
        EngineHistory,
        EngineIdentification,
        EngineLoad,
        EngineLoadOperations,
        EngineLoadOperationsHasDevice,
        EngineMassDrop,
        EngineMassLoad,
        EngineMassDropHasDevice,
        EngineMassLoadHasDevice,
        EngineOperationsConsumption,
        EngineOperationsConsumptionHasDevice,
        EnginePlan,
        EngineActualNorm,
        EngineActualNormHasDevice,
        EngineRights,
        EngineRole,
        EngineStatus,
        EngineToolLocation,
        EngineTools,
        EngineToolsHasDevice,
        EngineToolTypes,
        EngineType,
        EngineUser
    ]

    # cores = [CHelp, Errors, MassTools, CPlan, CTools, CUser]
    # dates = [engine_1, SessionLocal_1, Base_1, get_db_1, SessionLocal_2, SessionLocal_3, engine_2, engine_3,
    #          SessionLocal_4]
    # main_db = [ActionMapper, rebuild_db, DataEngine]
    total = 0
    help_docstrings = {}
    documenters = [
        modules,
        engines,
        # cores,
        # dates,
        # main_db
    ]

    for documenter in documenters:
        for documents in documenter:
            help_docstrings = get_docstrings(cls=documents, _total=0)
            logger.debug("%s", help_docstrings["docstrings"])
            total += help_docstrings["total"]

    logger.info("total lines: %s", total)
