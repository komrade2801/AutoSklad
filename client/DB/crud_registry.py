# DB/crud_registry.py
from DB.Engine.CellCRUD import EngineCell
# from DB.Engine.CellHasDeviceCRUD import EngineCellHasDevice
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
import re


class NormalizedLookup:
    def __init__(self, original_dict):
        self.original_dict = original_dict
        self.normalized_map = {}

        for key in original_dict:
            nkey = self._normalize(key)
            if nkey in self.normalized_map:
                raise KeyError(f"Key collision: {key} and {self.normalized_map[nkey]} normalize to same value")
            self.normalized_map[nkey] = key

    def _normalize(self, key):
        """Приводит ключ к нижнему регистру и удаляет все не-алфавитно-цифровые символы"""
        return re.sub(r'[^a-z0-9]', '', key.lower())

    def get(self, key, default=None):
        nkey = self._normalize(key)
        original_key = self.normalized_map.get(nkey)
        return self.original_dict.get(original_key, default) if original_key else default


crud_source = {
    "Cell": EngineCell,
    # "CellHasDevice": EngineCellHasDevice,
    "Consumption": EngineConsumption,
    # "Device": EngineDevice,
    "Drop": EngineDrop,
    "DropOperations": EngineDropOperations,
    # "DropOperationsHasDevice": EngineDropOperationsHasDevice,
    "Error": EngineError,
    # "ErrorHasDevice": EngineErrorHasDevice,
    "Group": EngineGroup,
    "Help": EngineHelp,
    "History": EngineHistory,
    "Identification": EngineIdentification,
    "Load": EngineLoad,
    "LoadOperations": EngineLoadOperations,
    # "LoadOperationsHasDevice": EngineLoadOperationsHasDevice,
    "MassDrop": EngineMassDrop,
    "MassLoad": EngineMassLoad,
    # "MassDropHasDevice": EngineMassDropHasDevice,
    # "MassLoadHasDevice": EngineMassLoadHasDevice,
    "OperationsConsumption": EngineOperationsConsumption,
    # "OperationsConsumptionHasDevice": EngineOperationsConsumptionHasDevice,
    "Plan": EnginePlan,
    # "ActualNorm": EngineActualNorm,
    # "ActualNormHasDevice": EngineActualNormHasDevice,
    "Rights": EngineRights,
    "Role": EngineRole,
    "Status": EngineStatus,
    # "ToolLocation": EngineToolLocation,
    "Tools": EngineTools,
    # "ToolsHasDevice": EngineToolsHasDevice,
    # "ToolTypes": EngineToolTypes,
    # "Type": EngineType,
    "User": EngineUser,
    # "Page": EnginePage,
}


def camel_to_snake(name: str) -> str:
    """
    Переводит строку из CamelCase (или PascalCase) в snake_case.
    Пример:
      "MassLoad"  -> "mass_load"
      "XMLParser" -> "xml_parser"
    """
    s1 = re.sub(r'(?<!^)(?=[A-Z])', '_', name)
    return s1.lower()


def normalize_to_snake(s: str) -> str:
    """
    Если строка уже содержит '_', то считаем, что она уже в snake_case, возвращаем lower().
    Иначе — приводим CamelCase → snake_case.
    """
    if "_" in s:
        return s.lower()
    return camel_to_snake(s)


class CrudRegistry(dict):
    """
    Наследник dict, который при инициализации берёт исходный словарь
    с CamelCase-ключами и добавляет к каждому ключу его snake_case-версию.
    """

    def __init__(self, base_dict: dict):
        """
        base_dict: исходный словарь вида {"MassLoad": EngineMassLoad, ...}
        """
        super().__init__()
        self.normalized_lookup = NormalizedLookup(base_dict)

        # 1) Кладём «как есть» все пары из base_dict
        for camel_key, cls in base_dict.items():
            self[camel_key] = cls

        # 2) Для каждого ключа в CamelCase пробуем сгенерировать snake_case
        #    и, если его ещё нет, добавить как дополнительный ключ
        for camel_key, cls in list(base_dict.items()):
            snake_key = normalize_to_snake(camel_key)
            if snake_key not in self:
                self[snake_key] = cls


    def get(self, key, default=None):
        # Попробовать оригинальный ключ напрямую
        if key in self:
            return super().get(key, default)

        # Попробовать snake_case
        snake_key = normalize_to_snake(key)
        if snake_key in self:
            return super().get(snake_key, default)

        # Попробовать через NormalizedLookup
        found = self.normalized_lookup.get(key)
        if found:
            return found

        return default
    # Поскольку мы наследуем dict, все методы (get, __getitem__, keys, items и т. д.)
    # уже «работают» с этим объединённым набором ключей.


# --------------------------------------------------------------------------------
# Исходный словарь crud_registry
# --------------------------------------------------------------------------------
crud_registry = CrudRegistry(crud_source)
# crud_registry = NormalizedLookup(original_dict)