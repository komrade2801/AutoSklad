import random
import pytest
import datetime
from faker import Faker
from DB.Data.db import SessionLocal
from DB.Data.db import engine
from DB.Engine.ConsumptionCRUD import EngineConsumption
from DB.Engine.DropOperationsCRUD import EngineDropOperations
from DB.Engine.LoadOperationsCRUD import EngineLoadOperations
from DB.Engine.OperationsConsumptionCRUD import EngineOperationsConsumption
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.CellCRUD import EngineCell
from DB.Engine.DropCRUD import EngineDrop
from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.HistoryCRUD import EngineHistory
from DB.Engine.LoadCRUD import EngineLoad
from DB.Engine.MassLoadCRUD import EngineMassLoad
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.StatusCRUD import EngineStatus
from DB.Engine.ToolsCRUD import EngineTools



# Фикстура для настройки тестовой базы данных
@pytest.fixture(scope="module")
def test_engine():
    """
    Создает тестовый движок базы данных (в памяти).
    """
    return engine()


# Фикстура для создания тестовой сессии
@pytest.fixture(scope="module")
def test_session(test_engine):
    """
    Создает тестовую сессию SQLAlchemy.
    """
    return SessionLocal(test_engine)


# Фикстура для экземпляра EngineMassLoad
@pytest.fixture
def engine_mass_load(test_session):
    """
    Создает экземпляр EngineMassLoad с тестовой сессией.
    """
    return EngineMassLoad(session=test_session)


# Фикстура для экземпляра EngineCell
@pytest.fixture
def engine_cell(test_session):
    """
    Создаёт экземпляр EngineCell с тестовой сессией.
    """
    return EngineCell(session=test_session)


# Фикстура для создания экземпляра EngineTools
@pytest.fixture
def engine_tools(test_session):
    """
    Создает экземпляр EngineTools с тестовой сессией.
    """
    return EngineTools(test_session)


# Фикстура для создания экземпляра EngineGroup
@pytest.fixture
def engine_group(test_session):
    """
    Создает экземпляр EngineGroup с тестовой сессией.
    """
    return EngineGroup(session=test_session)


# Фикстура для экземпляра EnginePlan
@pytest.fixture
def engine_plan(test_session):
    """
    Создает экземпляр EnginePlan с тестовой сессией.
    """
    return EnginePlan(session=test_session)


@pytest.fixture
def engine_load(test_session):
    """
    Создает экземпляр EngineLoad с тестовой сессией.
    """
    return EngineLoad(session=test_session)


# Фикстура для экземпляра EngineDrop
@pytest.fixture
def engine_drop(test_session):
    """
    Создает экземпляр EngineDrop с тестовой сессией.
    """
    return EngineDrop(session=test_session)


# Фикстура для создания экземпляра EngineHistory
@pytest.fixture
def engine_history(test_session):
    """
    Создает экземпляр EngineHistory с тестовой сессией.
    """
    return EngineHistory(session=test_session)


# Фикстура для экземпляра EngineStatus
@pytest.fixture
def engine_status(test_session):
    """
    Создает экземпляр EngineStatus с тестовой сессией.
    """
    return EngineStatus(session=test_session)


@pytest.fixture
def fake_data():
    fake = Faker("Ru")
    return fake


# Фикстура для экземпляра EngineUser
@pytest.fixture
def engine_user(test_session):
    """
    Создает экземпляр EngineUser с тестовой сессией.
    """
    return EngineUser(session=test_session)


# Экземпляр класса EngineRole для тестирования
@pytest.fixture
def engine_role(test_session):
    """
    Создаёт экземпляр EngineRole с тестовой сессией.
    """
    return EngineRole(test_session)


# Фикстура для экземпляра EngineConsumption
@pytest.fixture
def engine_consumption(test_session):
    """
    Создает экземпляр EngineConsumption с тестовой сессией.
    """
    return EngineConsumption(session=test_session)


# Фикстура для экземпляра EngineLoadOperations
@pytest.fixture
def engine_load_operations(test_session):
    """
    Создает экземпляр EngineLoadOperations с тестовой сессией.
    """
    return EngineLoadOperations(session=test_session)


# Фикстура для экземпляра EngineOperationsConsumption
@pytest.fixture
def engine_operations_consumption(test_session):
    """
    Создает экземпляр EngineOperationsConsumption с тестовой сессией.
    """
    return EngineOperationsConsumption(session=test_session)


# Фикстура для экземпляра EngineDropOperations
@pytest.fixture
def engine_drop_operations(test_session):
    """
    Создает экземпляр EngineDropOperations с тестовой сессией.
    """
    return EngineDropOperations(session=test_session)


@pytest.fixture
def setup_data(test_session, engine_tools, engine_group, engine_plan, engine_status, engine_load, engine_cell, engine_history, engine_user, engine_role, engine_load_operations):
    """
    Создает тестовые данные для инструментов, планов и групп.
    """

    names = {
        "HME435-010030-050-S04": "Фреза концевая",
        "HME435-015040-050-S04": "Фреза концевая",
        "HME435-020060-050-S04": "Фреза концевая",
        "HME435-025070-050-S04": "Фреза концевая",
        "HME435-030090-050-S04": "Фреза концевая",
        "HME435-040110-050-S04": "Фреза концевая",
        "HME435-050130-050-S06": "Фреза концевая",
        "HME435-060160-050-S06": "Фреза концевая",
        "HME435-080200-060-S08": "Фреза концевая",
        "HME435-100250-075-S10": "Фреза концевая",
        "HMEL235-050200-100-S06": "Фреза концевая",
        "HMEL235-060180-075-S06": "Фреза концевая",
        "HMEL235-060240-100-S06": "Фреза концевая",
        "HMEL235-080240-075-S08": "Фреза концевая",
        "HMEL435-100400-100-S10": "Фреза концевая",
        "HMR430-010R0,2-050-S04": "Фреза концевая с R кромки",
        "HMR430-020R0,2-050-S04": "Фреза концевая с R кромки",
        "HMR430-030R0,2-050-S04": "Фреза концевая с R кромки",
        "HMR430-030R0,5-050-S04": "Фреза концевая с R кромки",
        "HMR430-060R0,2-050-S06": "Фреза концевая с R кромки",
        "HMR430-080R0,5-050-S08": "Фреза концевая с R кромки",
        "HMR430-100R0,5-075-S10": "Фреза концевая с R кромки",
        "HMR435-010R0,2-050-S04": "Фреза концевая с R кромки",
        "HMR435-020R0,2-050-S04": "Фреза концевая с R кромки",
        "HMR435-030R0,2-050-S04": "Фреза концевая с R кромки",
        "HMR435-030R0,5-050-S04": "Фреза концевая с R кромки",
        "HMR435-060R0,2-050-S06": "Фреза концевая с R кромки",
        "HMR435-060R0,5-050-S06": "Фреза концевая с R кромки",
        "HMR435-060R1,0-050-S06": "Фреза концевая с R кромки",
        "HMR435-080R0,5-060-S08": "Фреза концевая с R кромки",
        "HMR435-100R0,5-075-S10": "Фреза концевая с R кромки",
        "HMR435-100R1,0-050-S10": "Фреза концевая с R кромки",
        "HRE430-015160-050-S04": "Фреза концевая с шейкой",
        "HRE430-015200-050-S04": "Фреза концевая с шейкой",
        "HRE430-020160-050-S04": "Фреза концевая с шейкой",
        "HRE430-020200-050-S04": "Фреза концевая с шейкой",
        "HRE430-030200-050-S04": "Фреза концевая с шейкой",
        "HRE430-030300-050-S04": "Фреза концевая с шейкой",
        "HMB230-010020-050 04": "Фреза сферическая",
        "HMB230-015030-050 04": "Фреза сферическая",
        "HMB230-020040-050 04": "Фреза сферическая",
        "HMB230-030060-050 04": "Фреза сферическая",
        "HMB230-040080-050 04": "Фреза сферическая",
        "HMB230-050100-050 06": "Фреза сферическая",
        "HMB230-060120-050 06": "Фреза сферическая",
        "HMB230-080160-60-S08": "Фреза сферическая",
        "HMB230-100200-075-S10": "Фреза сферическая",
        "90° 04*90 2F": "Фреза фасочная",
        "90° 04*90 3F": "Фреза фасочная",
        "90° 06*90 3F": "Фреза фасочная",
        "90° 08*90 2F": "Фреза фасочная",
        "90° 08*90 3F": "Фреза фасочная",
        "90° 10*90 3F": "Фреза фасочная",
        "90° 04*90": "Фреза фасочная",
        "90° 06*90": "Фреза фасочная",
        "90° 08*90": "Фреза фасочная",
        "90° 06*90 2F": "Фреза фасочная",
        "90° 10*90 2F": "Фреза фасочная",
        "KAA 20×0,3×6×24T": "Дисковая фреза",
        "KAA 20×0,3×6×32T": "Дисковая фреза",
        "KAA 25×0,3×8×24T": "Дисковая фреза",
        "KAA 20×0,4×6×24T": "Дисковая фреза",
        "KAA 20×0,4×6×32T": "Дисковая фреза",
        "KAA 25×0,4×8×32T": "Дисковая фреза",
        "KAA 32×0,5×8×48T": "Дисковая фреза",
        "KAA 20×0,5×6×32T": "Дисковая фреза",
        "KAA 32×0,5×8×32T": "Дисковая фреза",
        "KAA 20×0,6×6×32T": "Дисковая фреза",
        "KAA 32×0,6×8×48T": "Дисковая фреза",
        "KAA 20×0,7×6×32T": "Дисковая фреза",
        "KAA 32×0,7×8×48T": "Дисковая фреза",
        "KAA 20×0,8×6×32T": "Дисковая фреза",
        "KAA 32×0,8×8×48T": "Дисковая фреза",
        "KAA 20×1,0×6×32T": "Дисковая фреза",
        "KAA 20×1,0×6×48T": "Дисковая фреза",
        "KAA 32×1,0×6×32T": "Дисковая фреза",
        "KAA 32×1,0×8×24T-R0,5": "Дисковая фреза",
        "KAA 32×1,0×8×48T": "Дисковая фреза",
        "KAA 20×1,1×6×32T": "Дисковая фреза",
        "KAA 20×1,1×6×48T": "Дисковая фреза",
        "KAA 25×1,1×8×32T": "Дисковая фреза",
        "KAA 32×1,1×8×48T": "Дисковая фреза",
        "KAA 20×1,2×6×40T": "Дисковая фреза",
        "KAA 20×1,2×6×48T": "Дисковая фреза",
        "KAA 25×1,2×8×32T": "Дисковая фреза",
        "KAA 32×1,2×8×48T": "Дисковая фреза",
        "KAA 32×1,3×6×48T": "Дисковая фреза",
        "KAA 32×1,3×8×48T": "Дисковая фреза",
        "KAA 20×1,4×6×48T": "Дисковая фреза",
        "KAA 32×1,4×8×48T": "Дисковая фреза",
        "KAA 20×1,6×6×48T": "Дисковая фреза",
        "KAA 32×1,6×8×48T": "Дисковая фреза",
        "KAAD 25×2,0×6×50T": "Дисковая фреза",
        "KAA 32*0,5*6*32T": "Дисковая фреза",
        "KAA 32*0,6*6*32T": "Дисковая фреза",
        "KAA 32*0,7*8*48T": "Дисковая фреза",
        "KAA 32*0,8*6*32T": "Дисковая фреза",
        "KAA 32*1,0*6*32T": "Дисковая фреза",
        "KAA 32*1,0*8*48T": "Дисковая фреза",
        "KAA 32*1,3*6*48T": "Дисковая фреза",
        "KAA 25*1,5*8*32T": "Дисковая фреза",
        "KAA 25*2,0*6*50T": "Дисковая фреза",
    }
    description_group = {
        "HME435-010030-050-S04": "Поставщик: KOVES (Китай)",
        "HME435-015040-050-S04": "Поставщик: KOVES (Китай)",
        "HME435-020060-050-S04": "Поставщик: KOVES (Китай)",
        "HME435-025070-050-S04": "Поставщик: KOVES (Китай)",
        "HME435-030090-050-S04": "Поставщик: KOVES (Китай)",
        "HME435-040110-050-S04": "Поставщик: KOVES (Китай)",
        "HME435-050130-050-S06": "Поставщик: KOVES (Китай)",
        "HME435-060160-050-S06": "Поставщик: KOVES (Китай)",
        "HME435-080200-060-S08": "Поставщик: KOVES (Китай)",
        "HME435-100250-075-S10": "Поставщик: KOVES (Китай)",
        "HMEL235-050200-100-S06": "Поставщик: KOVES (Китай)",
        "HMEL235-060180-075-S06": "Поставщик: KOVES (Китай)",
        "HMEL235-060240-100-S06": "Поставщик: KOVES (Китай)",
        "HMEL235-080240-075-S08": "Поставщик: KOVES (Китай)",
        "HMEL435-100400-100-S10": "Поставщик: KOVES (Китай)",
        "HMR430-010R0,2-050-S04": "Поставщик: KOVES (Китай)",
        "HMR430-020R0,2-050-S04": "Поставщик: KOVES (Китай)",
        "HMR430-030R0,2-050-S04": "Поставщик: KOVES (Китай)",
        "HMR430-030R0,5-050-S04": "Поставщик: KOVES (Китай)",
        "HMR430-060R0,2-050-S06": "Поставщик: KOVES (Китай)",
        "HMR430-080R0,5-050-S08": "Поставщик: KOVES (Китай)",
        "HMR430-100R0,5-075-S10": "Поставщик: KOVES (Китай)",
        "HMR435-010R0,2-050-S04": "Поставщик: KOVES (Китай)",
        "HMR435-020R0,2-050-S04": "Поставщик: KOVES (Китай)",
        "HMR435-030R0,2-050-S04": "Поставщик: KOVES (Китай)",
        "HMR435-030R0,5-050-S04": "Поставщик: KOVES (Китай)",
        "HMR435-060R0,2-050-S06": "Поставщик: KOVES (Китай)",
        "HMR435-060R0,5-050-S06": "Поставщик: KOVES (Китай)",
        "HMR435-060R1,0-050-S06": "Поставщик: KOVES (Китай)",
        "HMR435-080R0,5-060-S08": "Поставщик: KOVES (Китай)",
        "HMR435-100R0,5-075-S10": "Поставщик: KOVES (Китай)",
        "HMR435-100R1,0-050-S10": "Поставщик: KOVES (Китай)",
        "HRE430-015160-050-S04": "Поставщик: KOVES (Китай)",
        "HRE430-015200-050-S04": "Поставщик: KOVES (Китай)",
        "HRE430-020160-050-S04": "Поставщик: KOVES (Китай)",
        "HRE430-020200-050-S04": "Поставщик: KOVES (Китай)",
        "HRE430-030200-050-S04": "Поставщик: KOVES (Китай)",
        "HRE430-030300-050-S04": "Поставщик: KOVES (Китай)",
        "HMB230-010020-050-S04": "Поставщик: KOVES (Китай)",
        "HMB230-015030-050-S04": "Поставщик: KOVES (Китай)",
        "HMB230-020040-050-S04": "Поставщик: KOVES (Китай)",
        "HMB230-030060-050-S04": "Поставщик: KOVES (Китай)",
        "HMB230-040080-050-S04": "Поставщик: KOVES (Китай)",
        "HMB230-050100-050-S06": "Поставщик: KOVES (Китай)",
        "HMB230-060120-050-S06": "Поставщик: KOVES (Китай)",
        "HMB230-080160-60-S08": "Поставщик: KOVES (Китай)",
        "HMB230-100200-075-S10": "Поставщик: KOVES (Китай)",
        "04*90 2F": "",
        "04*90 3F": "",
        "06*90 3F": "",
        "08*90 2F": "",
        "08*90 3F": "",
        "10*90 3F": "",
        "04*90 ": "",
        "06*90 ": "",
        "08*90 ": "",
        "06*90 2F": "",
        "10*90 2F ": "",
        "KAA 20×0,3×6×24T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,3×6×32T": "",
        "KAA 25×0,3×8×24T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,4×6×24T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,4×6×32T": "",
        "KAA 25×0,4×8×32T": "Поставщик: KOVES (Китай)",
        "KAA 32×0,5×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,5×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 32×0,5×8×32T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,6×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 32×0,6×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,7×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 32×0,7×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×0,8×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 32×0,8×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,0×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,0×6×48T": "Поставщик: KOVES (Китай)",
        "KAA 32×1,0×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 32×1,0×8×24T-R0,5": "",
        "KAA 32×1,0×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,1×6×32T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,1×6×48T": "Поставщик: KOVES (Китай)",
        "KAA 25×1,1×8×32T": "",
        "KAA 32×1,1×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,2×6×40T": "",
        "KAA 20×1,2×6×48T": "Поставщик: KOVES (Китай)",
        "KAA 25×1,2×8×32T": "",
        "KAA 32×1,2×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 32×1,3×6×48T": "Поставщик: KOVES (Китай)",
        "KAA 32×1,3×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,4×6×48T": "Поставщик: KOVES (Китай)",
        "KAA 32×1,4×8×48T": "Поставщик: KOVES (Китай)",
        "KAA 20×1,6×6×48T": "Поставщик: KOVES (Китай)",
        "KAA 32×1,6×8×48T": "Поставщик: KOVES (Китай)",
        "KAAD 25×2,0×6×50T": "",
        "KAA 32*0,5*6*32T": "",
        "KAA 32*0,6*6*32T": "",
        "KAA 32*0,7*8*48T": "",
        "KAA 32*0,8*6*32T": "",
        "KAA 32*1,0*6*32T": "",
        "KAA 32*1,0*8*48T": "",
        "KAA 32*1,3*6*48T": "",
        "KAA 25*1,5*8*32T": "",
    }
    description_tools = {
        "HME435-010030-050-S04": "Ø4",
        "HME435-015040-050-S04": "Ø4",
        "HME435-020060-050-S04": "Ø4",
        "HME435-025070-050-S04": "Ø4",
        "HME435-030090-050-S04": "Ø4",
        "HME435-040110-050-S04": "Ø4",
        "HME435-050130-050-S06": "Ø6",
        "HME435-060160-050-S06": "Ø6",
        "HME435-080200-060-S08": "Ø8",
        "HME435-100250-075-S10": "Ø10",
        "HMEL235-050200-100-S06": "Ø6",
        "HMEL235-060180-075-S06": "Ø6",
        "HMEL235-060240-100-S06": "Ø6",
        "HMEL235-080240-075-S08": "Ø8",
        "HMEL435-100400-100-S10": "Ø10",
        "HMR430-010R0,2-050-S04": "Ø1",
        "HMR430-020R0,2-050-S04": "Ø2",
        "HMR430-030R0,2-050-S04": "Ø3",
        "HMR430-030R0,5-050-S04": "Ø3",
        "HMR430-060R0,2-050-S06": "Ø6",
        "HMR430-080R0,5-050-S08": "Ø8",
        "HMR430-100R0,5-075-S10": "Ø10",
        "HMR435-010R0,2-050-S04": "Ø1",
        "HMR435-020R0,2-050-S04": "Ø2",
        "HMR435-030R0,2-050-S04": "Ø3",
        "HMR435-030R0,5-050-S04": "Ø3",
        "HMR435-060R0,2-050-S06": "Ø6",
        "HMR435-060R0,5-050-S06": "Ø6",
        "HMR435-060R1,0-050-S06": "Ø6",
        "HMR435-080R0,5-060-S08": "Ø8",
        "HMR435-100R0,5-075-S10": "Ø10",
        "HMR435-100R1,0-050-S10": "Ø10",
        "HRE430-015160-050-S04": "Ø1,5",
        "HRE430-015200-050-S04": "Ø1,5",
        "HRE430-020160-050-S04": "Ø2",
        "HRE430-020200-050-S04": "Ø2",
        "HRE430-030200-050-S04": "Ø3",
        "HRE430-030300-050-S04": "Ø3",
        "HMB230-010020-050-S04": "R0,5",
        "HMB230-015030-050-S04": "R0,75",
        "HMB230-020040-050-S04": "R1",
        "HMB230-030060-050-S04": "R1,5",
        "HMB230-040080-050-S04": "R2",
        "HMB230-050100-050-S06": "R2,5",
        "HMB230-060120-050-S06": "R3",
        "HMB230-080160-60-S08": "R4",
        "HMB230-100200-075-S10": "R5",
        "04*90 2F": "Ø4",
        "04*90 3F": "Ø4",
        "06*90 3F": "Ø6",
        "08*90 2F": "Ø8",
        "08*90 3F": "Ø8",
        "10*90 3F": "Ø10",
        "04*90 ": "Ø4",
        "06*90 ": "Ø6",
        "08*90 ": "Ø8",
        "06*90 2F": "Ø6",
        "10*90 2F ": "Ø10",
        "KAA 20×0,3×6×24T": "",
        "KAA 20×0,3×6×32T": "",
        "KAA 25×0,3×8×24T": "",
        "KAA 20×0,4×6×24T": "",
        "KAA 20×0,4×6×32T": "",
        "KAA 25×0,4×8×32T": "",
        "KAA 32×0,5×8×48T": "",
        "KAA 20×0,5×6×32T": "",
        "KAA 32×0,5×8×32T": "",
        "KAA 20×0,6×6×32T": "",
        "KAA 32×0,6×8×48T": "",
        "KAA 20×0,7×6×32T": "",
        "KAA 32×0,7×8×48T": "",
        "KAA 20×0,8×6×32T": "",
        "KAA 32×0,8×8×48T": "",
        "KAA 20×1,0×6×32T": "",
        "KAA 20×1,0×6×48T": "",
        "KAA 32×1,0×6×32T": "",
        "KAA 32×1,0×8×24T-R0,5": "",
        "KAA 32×1,0×8×48T": "",
        "KAA 20×1,1×6×32T": "",
        "KAA 20×1,1×6×48T": "",
        "KAA 25×1,1×8×32T": "",
        "KAA 32×1,1×8×48T": "",
        "KAA 20×1,2×6×40T": "",
        "KAA 20×1,2×6×48T": "",
        "KAA 25×1,2×8×32T": "",
        "KAA 32×1,2×8×48T": "",
        "KAA 32×1,3×6×48T": "",
        "KAA 32×1,3×8×48T": "",
        "KAA 20×1,4×6×48T": "",
        "KAA 32×1,4×8×48T": "",
        "KAA 20×1,6×6×48T": "",
        "KAA 32×1,6×8×48T": "",
        "KAAD 25×2,0×6×50T": "",
        "KAA 32*0,5*6*32T": "",
        "KAA 32*0,6*6*32T": "",
        "KAA 32*0,7*8*48T": "",
        "KAA 32*0,8*6*32T": "",
        "KAA 32*1,0*6*32T": "",
        "KAA 32*1,0*8*48T": "",
        "KAA 32*1,3*6*48T": "",
        "KAA 25*1,5*8*32T": "",
    }
    return {
        "names": names,
        "description_group": description_group,
        "description_tools": description_tools,
    }


# def test_add_status(engine_status, setup_data, engine_load_operations, engine_load, engine_tools, engine_cell, engine_history, engine_group, engine_plan, engine_drop, engine_drop_operations,
#                     engine_consumption, engine_operations_consumption):
#     """
#     Тест успешного добавления статуса.
#     """
#     # engine_status.delete_all()
#     # engine_group.delete_all()
#     # engine_plan.delete_all()
#     # engine_tools.delete_all()
#     # engine_cell.delete_all()
#     # engine_history.delete_all()
#     # engine_load.delete_all()
#     # engine_load_operations.delete_all()
#     # engine_drop.delete_all()
#     # engine_drop_operations.delete_all()
#     # engine_consumption.delete_all()
#     # engine_operations_consumption.delete_all()
#
#     result_init = None
#     status_init = engine_status.find_by_name("mass_load_init")
#     if not status_init:
#         ids = engine_status.get_all_ids()
#         index = max(ids, default=0) + 1
#         result_init = engine_status.add(
#             index=index,
#             stype="mass_drop_init",
#             description="Объявлена массовая выгрузка"
#         )
#     result_ready = None
#
#     status_ready = engine_status.find_by_name("mass_load_ready")
#     if not status_ready:
#         ids = engine_status.get_all_ids()
#         index = max(ids, default=0) + 1
#         result_ready = engine_status.add(
#             index=index,
#             stype="mass_drop_ready",
#             description="Инструмент недоступен"
#         )
#
#     status_init = engine_status.find_by_name("mass_load_init")
#     if not status_init:
#         ids = engine_status.get_all_ids()
#         index = max(ids, default=0) + 1
#         result_init = engine_status.add(
#             index=index,
#             stype="mass_load_init",
#             description="Объявлена массовая загрузка"
#         )
#     result_ready = None
#
#     status_ready = engine_status.find_by_name("mass_load_ready")
#     if not status_ready:
#         ids = engine_status.get_all_ids()
#         index = max(ids, default=0) + 1
#         result_ready = engine_status.add(
#             index=index,
#             stype="mass_load_ready",
#             description="Инструмент готов к выдачи"
#         )
#     result_finish = None
#     result_finish = engine_status.find_by_name("consumption")
#     if not result_finish:
#         ids = engine_status.get_all_ids()
#         index = max(ids, default=0) + 1
#         result_finish = engine_status.add(
#             index=index,
#             stype="consumption",
#             description="Инструмент выдан пользователю"
#         )
#     assert result_init and result_ready is True, "Статус не был добавлен"


def test_add_plan(engine_plan, setup_data, fake_data):
    """
    Тест успешного добавления чертежа.
    """

    description_group = setup_data["description_group"]
    length = int(len(description_group))

    for key in range(0, length):
        barcode = str(random.randint(111111111, 999999999))
        index = max(engine_plan.get_all_ids(), default=0) + 1
        result = engine_plan.add_plan(
            plan_id=index,
            plan_enterprise=fake_data.company_prefix() + " " + fake_data.company(),
            plan_barcode=barcode,
            plan_name=fake_data.last_name_male(),
            plan_description=fake_data.sentence(nb_words=5),
            plan_designation=fake_data.job_male(),
            plan_index_list=random.randint(1, 999),
            plan_list_count=random.randint(1, 999),
            plan_parent_plan=None,
            plan_parent_plan_id=None,
        )
        plan = engine_plan.get(index)
        assert result is True, "Чертеж не был добавлен"
        assert plan is not None, "Чертеж не был добавлен"
    pass


def test_add_tool(engine_tools, engine_group, engine_plan, setup_data, engine_status):
    """
    Тест успешного добавления инструмента.
    """
    names = setup_data["names"]
    description_group = setup_data["description_group"]
    description_tools = setup_data["description_tools"]

    groups = set()
    group = None
    result = None
    plans_ids = engine_plan.get_all_ids()
    for _, key in enumerate(names):
        name = names[key]
        img = name + ".png"
        if name not in groups:
            groups.add(name)
            index = max(engine_group.get_all_ids(), default=0) + 1
            description = ""
            try:
                description = description_group[key]
            except Exception:...
            engine_group.add_group(
                index = index,
                name = name,
                description = description,
                status = 0,
            )
            group = engine_group.get(index)
        plan_id = None
        try:
            plan_id = random.choice(plans_ids)
        except Exception:...

        description = ""
        try:
            description = description_tools[key]
        except Exception:...

        barcode = str(random.randint(11111, 99999))
        result = engine_tools.add_tool(
            id = max(engine_tools.get_all_ids(), default=0) + 1,
            barcode = barcode,
            name = key,
            description = description,
            img = img,
            plan_id = plan_id,
            groups_id = group.id
        )

        assert result is True, "Инструмент не был добавлен"


def test_add_cell(engine_cell, setup_data, engine_tools, engine_status):
    """
    Тест успешного добавления ячейки.
    """

    tools_ids = engine_tools.get_all_ids()
    for tool_id in tools_ids:
        tool = engine_tools.get(tool_id)
        status = engine_status.find_by_name("mass_load_init")
        if not status:
            index = max(engine_status.get_all_ids(), default=0) + 1
            engine_status.add(
                index=index,
                stype="mass_load_init",
                description="Объявлена массовая загрузка"
            )
        cell_id = max(engine_cell.get_all_ids(), default=0) + 1

        result = engine_cell.add_cell(
            index = cell_id,
            number = cell_id,
            groups_id = tool.groups_id,
            tools_id = tool_id,
            status_id = status.id,
            description = tool.name
        )

        assert result is True, "Ячейка не была добавлена"
    pass


def test_add_load(engine_load, setup_data, engine_tools, engine_cell, engine_mass_load):
    """
    Тест добавления записи Load.
    """
    mass_load_id = max(engine_mass_load.get_all_ids(), default=0) + 1
    description = f"Массовая загрузка {mass_load_id}"
    engine_mass_load.add_mass_load(
        index=mass_load_id,
        description=description
    )

    mass_load = engine_mass_load.get_mass_load_by_id(mass_load_id)
    tools_ids = engine_tools.get_all_ids()
    for tool_id in tools_ids:
        tool = engine_tools.get(tool_id)
        cell = engine_cell.get(tool.id)
        load_id = max(engine_load.get_all_ids(), default=0) + 1
        engine_load.add_load(
            id=load_id,
            tools_id=tool.id,
            mass_load_id=mass_load.id,
            cell_id=cell.id,
            description=f"Загрузка инструмента {tool.name} в ячейку №{cell.number}"
        )

        added_load = engine_load.get_load_by_id(load_id)
        assert added_load is not None, "Загруженная запись не найдена в базе данных"
        assert added_load.description == f"Загрузка инструмента {tool.name} в ячейку №{cell.number}"
    pass


def test_add_load_operation(engine_load_operations, setup_data,
                            engine_status, engine_load, engine_tools,
                            engine_cell, engine_history, engine_user, engine_role):
    """
    Тест успешного добавления операции.
    """
    # Данные для добавления операции
    loads_ids = engine_load.get_all_ids()
    for load_id in loads_ids:
        load = engine_load.get(load_id)
        tool = engine_tools.get_tool_by_id(load.tools_id)
        load_operations_id = max(engine_load_operations.get_all_ids(), default=0) + 1

        status_init = engine_status.find_by_name("mass_load_init")
        if not status_init:
            index = max(engine_status.get_all_ids(), default=0) + 1
            engine_status.add(
                index=index,
                stype="mass_load_init",
                description="Объявлена массовая загрузка"
            )
        user_id = max(engine_user.get_all_ids())
        user = engine_user.get(user_id)
        stories_id = max(engine_history.get_all_ids(), default=0) + 1
        engine_history.add_history(
            id=stories_id,
            user_id=user.id,
            role_id=user.role_id,
            tools_id=tool.id,
            datetime_value=datetime.datetime.now(),
            status=0,
            description=status_init.description,
        )
        history_init = engine_history.get(stories_id)
        result_init = engine_load_operations.add_operation(
            id=load_operations_id,
            date=datetime.datetime.now(),
            description=load.description,
            load_id=load.id,
            load_tools_id=tool.id,
            status_id=status_init.id,
            history_id=history_init.id
        )

        status_ready = engine_status.find_by_name("mass_load_ready")
        if not status_ready:
            index = max(engine_status.get_all_ids(), default=0) + 1
            engine_status.add(
                index = index,
                stype = "mass_load_ready",
                description = "Инструмент готов к выдачи"
            )
        stories_id = max(engine_history.get_all_ids(), default=0) + 1
        engine_history.add_history(
            id=stories_id,
            user_id=user.id,
            role_id=user.role_id,
            tools_id=tool.id,
            datetime_value=datetime.datetime.now(),
            status=0,
            description=status_ready.description,
        )
        history_ready = engine_history.get(stories_id)

        engine_cell.update(load.cell_id, description=status_ready.description,  status_id=status_ready.id)
        load_operations_id = max(engine_load_operations.get_all_ids(), default=0) + 1
        result_ready = engine_load_operations.add_operation(
            id=load_operations_id,
            date=datetime.datetime.now(),
            load_id=load.id,
            load_tools_id=tool.id,
            status_id=status_ready.id,
            history_id=history_ready.id,
            description=f"Инструмент в ячейке {load.cell_id} готов к выдачи",
        )

        assert result_init and result_ready is True, "Операция не была добавлена"
    pass
