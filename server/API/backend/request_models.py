from typing import Optional  # , Union
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel
from typing import List



# Pydantic модели для запросов
# Модели для работы с инструментами в автомате
class ToolEntry(BaseModel):
    tools: str
    sum: str  # Если значение должно быть числовым, можно изменить на int

class ToolTypesModel(BaseModel):
    id: int
    name: str
    description: str
    count: int
    amount: int

class AllToolTypesResponse(BaseModel):
    tools: Dict[int, ToolTypesModel]

class SubGroupModel(BaseModel):
    SGName: str
    # Здесь мы ожидаем, что каждый элемент словаря value соответствует модели ToolEntry.
    value: Dict[str, ToolEntry]


class GroupModel(BaseModel):
    name: str
    subgroup: Dict[str, SubGroupModel]

class AllGroupOnlyModel(BaseModel):
    id: int
    name: str
    parent: int

class AllGroupsOnlyResponse(BaseModel):
    groups: Dict[str, AllGroupOnlyModel]

class AllGroupsResponse(BaseModel):
    groups: Dict[str, GroupModel]


# class ToolEntry(BaseModel):
#     tools: str
#     cell: str

class GroupRequest(BaseModel):
    name: str
    tools: List[ToolEntry]


class PlanRequest(BaseModel):
    name: str
    groups: List[GroupRequest]


class ToolsInVendingUpdate(BaseModel):
    plans: Dict[str, PlanRequest]


class GroupEntry(BaseModel):
    name: str
    value: Dict[str, ToolEntry]


class PlanEntry(BaseModel):
    name: str
    groups: Dict[str, GroupEntry]


class ToolsInVendingResponse(BaseModel):
    plans: Dict[str, PlanEntry]


# Модели для норм инструментов
class ToolNorm(BaseModel):
    tool_id: int
    sum: float
    sum_of_periods: int
    type_periods: str
    sum_of_use: Optional[str] = None
    start_date: str


class ActualNorm(BaseModel):
    id: int
    barcode: str
    name: str
    description: str
    group: str
    status: str


class ActualNormResponse(BaseModel):
    norms: List[ToolNorm]


class ActualNormCreate(BaseModel):
    barcode: str
    name: str
    description: str
    group: str
    status: str


class ActualNormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group: Optional[str] = None
    status: Optional[str] = None


# Модель для записи справочной информации
class WriteHelpRequest(BaseModel):
    text: str
    date: Optional[datetime] = None


# Модель для записи справочной информации
class PatchHelpRequest(BaseModel):
    text: str


# Модель для записи справочной информации
class PutHelpRequest(BaseModel):
    text: str
    date: Optional[datetime] = None


# Общая модель для остальных write_* запросов
class WriteRequest(BaseModel):
    index: Optional[int] = None


# Модели для конфигурации устройства
class Signature(BaseModel):
    serial_number: int
    cells: dict


class ConfigRequest(BaseModel):
    signature: Signature
    network: dict
    serial: dict
    barcode: dict
    locks: dict
    logs: dict


class DeviceConfig(BaseModel):
    signature: Dict[str, Any]
    network: Dict[str, Any]
    serial: Dict[str, Any]
    barcode: Dict[str, Any]
    locks: Dict[str, Any]
    logs: Dict[str, Any]


# Модель для массового удаления
class MassDropRequest(BaseModel):
    user_id: int
    device_id: int
    plan_id: Optional[int] = None
    tool_ids: Optional[List[int]] = None
    task_id: Optional[int] = None


from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


# Модели для инвентаризации
class InventoryResponse(BaseModel):
    items: List[Dict[str, Any]]


# Модели для ячеек
class CellsResponse(BaseModel):
    cells: List[Dict[str, Any]]


class Cell(BaseModel):
    id: int
    number: int
    description: Optional[str]
    groups_id: Optional[int]
    tools_id: Optional[int]
    status_id: int


class CellCreate(BaseModel):
    number: int
    description: Optional[str]
    groups_id: Optional[int]
    tools_id: Optional[int]
    status_id: int


class CellUpdate(BaseModel):
    number: Optional[int]
    description: Optional[str]
    groups_id: Optional[int]
    tools_id: Optional[int]
    status_id: Optional[int]

class GroupsCreate(BaseModel):
    group_name: str
    parent_group: int
    description: str
    img: str
    group_id: Optional[int] = None  # Для обновления существующей группы

# Модель ответа для добавления групп
class GroupsAddResponse(BaseModel):
    status: int
    message: str

# Модель ответа для добавления чертежей
class PlanAddResponse(BaseModel):
    status: int
    message: str

class ToolsCreate(BaseModel):
    group_id: int
    tool_name: str
    description: str
    count: int
    img: str
    tools: Dict[str, Any]
    tool_type_id: Optional[int] = None  # Для обновления существующего инструмента


# Модель ответа для добавления инструментов
class ToolsAddResponse(BaseModel):
    status: int
    message: str

class ToolsImportResponse(BaseModel):
    processed: int
    errors: Any
    field_map: Any

# Модели для библиотеки инструментов
class ToolLibraryResponse(BaseModel):
    tools: Dict[str, Any]


class ToolLibrary(BaseModel):
    id: int
    name: str
    description: Optional[str]
    group_id: int


class ToolLibraryCreate(BaseModel):
    index: int
    name: str
    description: Optional[str]
    img: Optional[str]
    plan_id: Optional[int]
    groups_id: Optional[int]
    inventory_number: Optional[str]


class ToolLibraryUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    group_id: Optional[int]


# Модели для истории загрузки
class HistoryRandomLoadResponse(BaseModel):
    operations: Dict[str, Any]


class HistoryRandomLoad(BaseModel):
    id: int
    tool_id: int
    timestamp: datetime


class HistoryRandomLoadCreate(BaseModel):
    tool_id: int
    timestamp: datetime


class HistoryRandomLoadUpdate(BaseModel):
    tool_id: Optional[int]
    timestamp: Optional[datetime]


# Модели для загрузки
class HistoryLoadResponse(BaseModel):
    operations: Dict[str, Any]


class HistoryLoad(BaseModel):
    id: int
    tool_id: int
    timestamp: datetime


class HistoryLoadCreate(BaseModel):
    tool_id: int
    timestamp: datetime


class HistoryLoadUpdate(BaseModel):
    tool_id: Optional[int]
    timestamp: Optional[datetime]

class HistoryOperationEntry(BaseModel):
    id: int
    name_operation: str
    date: str
    tool: str
    plan: str
    user: str
    device: str

# Модели для операций
class HistoryOperationResponse(BaseModel):
    # operation: Dict[str, Any]
    operation: List[Any]


class HistoryOperation(BaseModel):
    id: int
    operation_type: str
    timestamp: datetime
    tool_id: int


class HistoryOperationCreate(BaseModel):
    operation_type: str
    timestamp: datetime
    tool_id: int


class HistoryOperationUpdate(BaseModel):
    operation_type: Optional[str]
    timestamp: Optional[datetime]
    tool_id: Optional[int]


# Модели для истории
class HistoryResponse(BaseModel):
    operation: Dict[str, Any]


class History(BaseModel):
    id: int
    timestamp: datetime
    tool_id: int


class HistoryCreate(BaseModel):
    timestamp: datetime
    tool_id: int


class HistoryUpdate(BaseModel):
    timestamp: Optional[datetime]
    tool_id: Optional[int]


# Модели для списания
class HistoryWriteOffResponse(BaseModel):
    operations: Dict[str, Any]


class HistoryWriteOff(BaseModel):
    id: int
    tool_id: int
    reason: str
    timestamp: datetime


class HistoryWriteOffCreate(BaseModel):
    tool_id: int
    reason: str
    timestamp: datetime


class HistoryWriteOffUpdate(BaseModel):
    tool_id: Optional[int]
    reason: Optional[str]
    timestamp: Optional[datetime]



class Tool(BaseModel):
    id: int
    barcode: str
    name: str
    description: str
    img: str
    plan_id: int
    groups_id: int


# Модели для чертежей
class PlanResponse(BaseModel):
    plans: List[Dict[str, Any]]


class RoleResponse(BaseModel):
    index: int
    name: Optional[str] = None
    description: Optional[str] = None
    parent_role_id: Optional[str] = None


class UserCredentialsInput(BaseModel):
    first_name: str
    patronymic: str
    last_name: str
    barcode: str


class UserCredentialsResponse(BaseModel):
    login: str
    password: str


class UserResponse(BaseModel):
    index: int
    barcode: int
    code: int
    first_name: str
    password: str
    second_name: str
    family: str
    role: str


class AllUserResponse(BaseModel):
    users: List[UserResponse]


class UserUpdate(BaseModel):
    index: int
    barcode: int
    code: int
    first_name: str
    password: str
    second_name: str
    family: str
    role_id: int


class RoleCreate(BaseModel):
    id: int
    Name: Optional[str] = None
    Description: Optional[str] = None
    ParentRole_id: int


class RoleUpdate(BaseModel):
    id: int
    Name: str
    Description: str
    ParentRole_id: int


class RightsUpdate(BaseModel):
    id: int
    Name: str
    Description: str
    Role_id: int


class RightsCreate(BaseModel):
    # id: int
    Name: Optional[str] = None
    Description: Optional[str] = None
    Role_id: int
    page_id: int
    status: int


class RightsResponse(BaseModel):
    id: int
    Name: str
    Description: Optional[str] = None
    Role_id: int


class UserPartialUpdate(BaseModel):
    index: int
    barcode: int
    code: int
    first_name: str
    password: str
    second_name: str
    family: str
    role_id: int


class UserCreate(BaseModel):
    index: int
    barcode: int
    code: int
    first_name: str
    password: str
    second_name: str
    family: str
    role_id: int


class Plan(BaseModel):
    id: int
    enterprise: str
    barcode: str
    name: str
    description: str
    designation: str
    index_list: int
    list_count: int
    parent_plan_id: Optional[int]
    parent_plan: Optional[str]
    # tools: List[Tool]


class PlanCreate(BaseModel):
    id: int
    enterprise: str
    barcode: str
    name: str
    description: str
    designation: str
    index_list: int
    list_count: int
    parent_plan_id: Optional[int] = None
    parent_plan: Optional[Any] = None
    tools: List[Dict[str, Any]]

    #
    # enterprise: str
    # barcode: str
    # name: str
    # description: Optional[str]

class PlanCreateRequest(BaseModel):
    plan: PlanCreate
    create_mass_load: bool

# class PlanCreate(BaseModel):
#     enterprise: str
#     barcode: str
#     name: str
#     description: Optional[str]

class PlanUpdate(BaseModel):
    enterprise: Optional[str]
    barcode: Optional[str]
    name: Optional[str]
    description: Optional[str]


class NormDataResponse(BaseModel):
    id: int
    tools_id: int
    actual_norm_id: int
    summa: Optional[int] = None
    summa_of_periods: Optional[int] = None
    type_periods: Optional[str] = None
    summa_of_use: Optional[str] = None
    start_date: Optional[datetime] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class NormDataCreate(BaseModel):
    tools_id: int
    actual_norm_id: int
    summa: Optional[int] = None
    summa_of_periods: Optional[int] = None
    type_periods: Optional[str] = None
    summa_of_use: Optional[str] = None
    start_date: Optional[datetime] = None
    description: Optional[str] = None


class NormDataUpdate(BaseModel):
    summa: Optional[int] = None
    summa_of_periods: Optional[int] = None
    type_periods: Optional[str] = None
    summa_of_use: Optional[str] = None
    start_date: Optional[datetime] = None
    description: Optional[str] = None


class AuthResponse(BaseModel):
    token: str
    redirect_url: str
    user: Dict[str, Any]  # Можно заменить на конкретную модель, например, UserResponse

class StatusResponse(BaseModel):
    id: int
    stype: str
    description: str
