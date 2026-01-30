import traceback

from Core.app_logging import get_logger
from DB.Models.Help import Help  # ----------------------------------- 1

logger = get_logger(__name__)
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

from DB.Engine.HelpCRUD import EngineHelp  # ----------------------------------- 1
from DB.Engine.ErrorsCRUD import EngineError  # -------------------------------- 2
from DB.Engine.RoleCRUD import EngineRole  # ----------------------------------- 3
from DB.Engine.PlanCRUD import EnginePlan  # ----------------------------------- 4
from DB.Engine.GroupCRUD import EngineGroup  # --------------------------------- 5
from DB.Engine.RightsCRUD import EngineRights  # ------------------------------- 6
from DB.Engine.MassDropCRUD import EngineMassDrop  # --------------------------- 7
from DB.Engine.MassLoadCRUD import EngineMassLoad  # --------------------------- 8
from DB.Engine.StatusCRUD import EngineStatus  # ------------------------------- 9
from DB.Engine.UserCRUD import EngineUser  # ----------------------------------- 10
from DB.Engine.IdentificationCRUD import EngineIdentification  # --------------- 11
from DB.Engine.ToolsCRUD import EngineTools  # --------------------------------- 12
from DB.Engine.CellCRUD import EngineCell  # ----------------------------------- 13
from DB.Engine.LoadCRUD import EngineLoad  # ----------------------------------- 14
from DB.Engine.DropCRUD import EngineDrop  # ----------------------------------- 15
from DB.Engine.ConsumptionCRUD import EngineConsumption  # --------------------- 16
from DB.Engine.HistoryCRUD import EngineHistory  # ----------------------------- 17
from DB.Engine.DropOperationsCRUD import EngineDropOperations  # --------------- 18
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption  # - 19
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations  # --------------- 20

from DB.Data.db import engine as engine_1
from DB.Data.db import SessionLocal as SessionLocal_1
from DB.Data.base import Base as Base_1
from DB.Data.db_depends import get_db as get_db_1
from DB.Data.db_depends import SessionLocal as SessionLocal_2
from DB.Data.mysql_db import SessionLocal as SessionLocal_3
from DB.Data.mysql_db import engine as engine_2
from DB.Data.sqlite_db import engine as engine_3
from DB.Data.sqlite_db import SessionLocal as SessionLocal_4

# from DB.action_map import ActionMapper
from DB.Create_db import rebuild_db
# from DB.config import

import inspect
import os


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
        logger.exception("documenter get_docstrings: %s", e)

    return {"docstrings": "\n".join(docstrings), "total": _total}


# Пример использования функции
if __name__ == "__main__":

    modules = [
        # Help,
        # Error,
        # Role,
        # Plan,
        # Group,
        # Rights,
        # MassDrop,
        # MassLoad,
        # Status,
        # User,
        # Identification,
        # Tools,
        # Cell,
        # Load,
        # Drop,
        # Consumption,
        # History,
        # DropOperations,
        # OperationsConsumption,
        # LoadOperations
    ]

    engines = [
        # EnginePlan,
        # EngineMassLoad,
        # EngineLoad,
        # EngineTools,

        # EngineHelp,
        # EngineError,
        # EngineRole,
        # EngineGroup,
        # EngineRights,
        # EngineMassDrop,
        # EngineStatus,
        # EngineUser,
        # EngineIdentification,
        EngineCell,
        # EngineDrop,
        # EngineConsumption,
        # EngineHistory,
        # EngineDropOperations,
        # EngineOperationsConsumption,
        # EngineLoadOperations
    ]

    # cores = [CHelp, Errors, MassTools, CPlan, CTools, CUser]
    # dates = [engine_1, SessionLocal_1, Base_1, get_db_1, SessionLocal_2, SessionLocal_3, engine_2, engine_3,
    #          SessionLocal_4]
    # main_db = [ActionMapper, rebuild_db, DataEngine]
    total = 0
    help_docstrings = {}
    documenters = [
        # modules,
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
