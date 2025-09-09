import random
from typing import Tuple

import faker
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from DB.Engine.GroupCRUD import EngineGroup
from DB.Engine.PlanCRUD import EnginePlan
from DB.Engine.ToolsCRUD import EngineTools
from DB.Models.Tools import Tools
from DB.Models.Plan import Plan
from DB.Models.Group import Group
from DB.Models.History import History
from datetime import datetime
from DB.Data.db import SessionLocal
from DB.Data.db import engine


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
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return SessionLocal(test_engine)


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
def setup_data(test_session, engine_tools, engine_group, engine_plan):
    """
    Создает тестовые данные для инструментов, планов и групп.
    """
    # engine_group.delete_all()
    # engine_plan.delete_all()
    # engine_tools.delete_all()
    plan = Plan(
        id=max(engine_plan.get_all_ids(), default=0)+1,
        enterprise="TestEnterprise",
        barcode=str(random.randint(111111111111, 999999999999)),
        name="Test Plan",
        description="Test Description",
        designation="Design 1",
        index_list=1,
        list_count=5
    )
    group = Group(id=max(engine_group.get_all_ids(), default=0)+1, name="Old Group", description="Old Description", status=0)
    test_session.add(plan)
    test_session.add(group)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    return plan, group


def test_add_tool_success(engine_tools, engine_group, engine_plan, test_session):
    """
    Тест успешного добавления инструмента.
    """
    engine_group.delete_all()
    engine_plan.delete_all()
    engine_tools.delete_all()
    fake = faker.Faker("ru_RU")
    # plan, group = setup_data
    name = "tool"
    description = "Универсальный молоток"
    img = "hammer.png"
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
    "HME435-010030-050-S04":"Поставщик: KOVES (Китай)",
    "HME435-015040-050-S04":"Поставщик: KOVES (Китай)",
    "HME435-020060-050-S04":"Поставщик: KOVES (Китай)",
    "HME435-025070-050-S04":"Поставщик: KOVES (Китай)",
    "HME435-030090-050-S04":"Поставщик: KOVES (Китай)",
    "HME435-040110-050-S04":"Поставщик: KOVES (Китай)",
    "HME435-050130-050-S06":"Поставщик: KOVES (Китай)",
    "HME435-060160-050-S06":"Поставщик: KOVES (Китай)",
    "HME435-080200-060-S08":"Поставщик: KOVES (Китай)",
    "HME435-100250-075-S10":"Поставщик: KOVES (Китай)",
    "HMEL235-050200-100-S06":"Поставщик: KOVES (Китай)",
    "HMEL235-060180-075-S06":"Поставщик: KOVES (Китай)",
    "HMEL235-060240-100-S06":"Поставщик: KOVES (Китай)",
    "HMEL235-080240-075-S08":"Поставщик: KOVES (Китай)",
    "HMEL435-100400-100-S10":"Поставщик: KOVES (Китай)",
    "HMR430-010R0,2-050-S04":"Поставщик: KOVES (Китай)",
    "HMR430-020R0,2-050-S04":"Поставщик: KOVES (Китай)",
    "HMR430-030R0,2-050-S04":"Поставщик: KOVES (Китай)",
    "HMR430-030R0,5-050-S04":"Поставщик: KOVES (Китай)",
    "HMR430-060R0,2-050-S06":"Поставщик: KOVES (Китай)",
    "HMR430-080R0,5-050-S08":"Поставщик: KOVES (Китай)",
    "HMR430-100R0,5-075-S10":"Поставщик: KOVES (Китай)",
    "HMR435-010R0,2-050-S04":"Поставщик: KOVES (Китай)",
    "HMR435-020R0,2-050-S04":"Поставщик: KOVES (Китай)",
    "HMR435-030R0,2-050-S04":"Поставщик: KOVES (Китай)",
    "HMR435-030R0,5-050-S04":"Поставщик: KOVES (Китай)",
    "HMR435-060R0,2-050-S06":"Поставщик: KOVES (Китай)",
    "HMR435-060R0,5-050-S06":"Поставщик: KOVES (Китай)",
    "HMR435-060R1,0-050-S06":"Поставщик: KOVES (Китай)",
    "HMR435-080R0,5-060-S08":"Поставщик: KOVES (Китай)",
    "HMR435-100R0,5-075-S10":"Поставщик: KOVES (Китай)",
    "HMR435-100R1,0-050-S10":"Поставщик: KOVES (Китай)",
    "HRE430-015160-050-S04":"Поставщик: KOVES (Китай)",
    "HRE430-015200-050-S04":"Поставщик: KOVES (Китай)",
    "HRE430-020160-050-S04":"Поставщик: KOVES (Китай)",
    "HRE430-020200-050-S04":"Поставщик: KOVES (Китай)",
    "HRE430-030200-050-S04":"Поставщик: KOVES (Китай)",
    "HRE430-030300-050-S04":"Поставщик: KOVES (Китай)",
    "HMB230-010020-050-S04":"Поставщик: KOVES (Китай)",
    "HMB230-015030-050-S04":"Поставщик: KOVES (Китай)",
    "HMB230-020040-050-S04":"Поставщик: KOVES (Китай)",
    "HMB230-030060-050-S04":"Поставщик: KOVES (Китай)",
    "HMB230-040080-050-S04":"Поставщик: KOVES (Китай)",
    "HMB230-050100-050-S06":"Поставщик: KOVES (Китай)",
    "HMB230-060120-050-S06":"Поставщик: KOVES (Китай)",
    "HMB230-080160-60-S08":"Поставщик: KOVES (Китай)",
    "HMB230-100200-075-S10":"Поставщик: KOVES (Китай)",
    "04*90 2F":"",
    "04*90 3F":"",
    "06*90 3F":"",
    "08*90 2F":"",
    "08*90 3F":"",
    "10*90 3F":"",
    "04*90 ":"",
    "06*90 ":"",
    "08*90 ":"",
    "06*90 2F":"",
    "10*90 2F ":"",
    "KAA 20×0,3×6×24T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,3×6×32T":"",
    "KAA 25×0,3×8×24T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,4×6×24T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,4×6×32T":"",
    "KAA 25×0,4×8×32T":"Поставщик: KOVES (Китай)",
    "KAA 32×0,5×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,5×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 32×0,5×8×32T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,6×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 32×0,6×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,7×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 32×0,7×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×0,8×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 32×0,8×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,0×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,0×6×48T":"Поставщик: KOVES (Китай)",
    "KAA 32×1,0×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 32×1,0×8×24T-R0,5":"",
    "KAA 32×1,0×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,1×6×32T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,1×6×48T":"Поставщик: KOVES (Китай)",
    "KAA 25×1,1×8×32T":"",
    "KAA 32×1,1×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,2×6×40T":"",
    "KAA 20×1,2×6×48T":"Поставщик: KOVES (Китай)",
    "KAA 25×1,2×8×32T":"",
    "KAA 32×1,2×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 32×1,3×6×48T":"Поставщик: KOVES (Китай)",
    "KAA 32×1,3×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,4×6×48T":"Поставщик: KOVES (Китай)",
    "KAA 32×1,4×8×48T":"Поставщик: KOVES (Китай)",
    "KAA 20×1,6×6×48T":"Поставщик: KOVES (Китай)",
    "KAA 32×1,6×8×48T":"Поставщик: KOVES (Китай)",
    "KAAD 25×2,0×6×50T":"",
    "KAA 32*0,5*6*32T":"",
    "KAA 32*0,6*6*32T":"",
    "KAA 32*0,7*8*48T":"",
    "KAA 32*0,8*6*32T":"",
    "KAA 32*1,0*6*32T":"",
    "KAA 32*1,0*8*48T":"",
    "KAA 32*1,3*6*48T":"",
    "KAA 25*1,5*8*32T":"",
    }
    description_tools = {
    "HME435-010030-050-S04":"Ø4",
    "HME435-015040-050-S04":"Ø4",
    "HME435-020060-050-S04":"Ø4",
    "HME435-025070-050-S04":"Ø4",
    "HME435-030090-050-S04":"Ø4",
    "HME435-040110-050-S04":"Ø4",
    "HME435-050130-050-S06":"Ø6",
    "HME435-060160-050-S06":"Ø6",
    "HME435-080200-060-S08":"Ø8",
    "HME435-100250-075-S10":"Ø10",
    "HMEL235-050200-100-S06":"Ø6",
    "HMEL235-060180-075-S06":"Ø6",
    "HMEL235-060240-100-S06":"Ø6",
    "HMEL235-080240-075-S08":"Ø8",
    "HMEL435-100400-100-S10":"Ø10",
    "HMR430-010R0,2-050-S04":"Ø1",
    "HMR430-020R0,2-050-S04":"Ø2",
    "HMR430-030R0,2-050-S04":"Ø3",
    "HMR430-030R0,5-050-S04":"Ø3",
    "HMR430-060R0,2-050-S06":"Ø6",
    "HMR430-080R0,5-050-S08":"Ø8",
    "HMR430-100R0,5-075-S10":"Ø10",
    "HMR435-010R0,2-050-S04":"Ø1",
    "HMR435-020R0,2-050-S04":"Ø2",
    "HMR435-030R0,2-050-S04":"Ø3",
    "HMR435-030R0,5-050-S04":"Ø3",
    "HMR435-060R0,2-050-S06":"Ø6",
    "HMR435-060R0,5-050-S06":"Ø6",
    "HMR435-060R1,0-050-S06":"Ø6",
    "HMR435-080R0,5-060-S08":"Ø8",
    "HMR435-100R0,5-075-S10":"Ø10",
    "HMR435-100R1,0-050-S10":"Ø10",
    "HRE430-015160-050-S04":"Ø1,5",
    "HRE430-015200-050-S04":"Ø1,5",
    "HRE430-020160-050-S04":"Ø2",
    "HRE430-020200-050-S04":"Ø2",
    "HRE430-030200-050-S04":"Ø3",
    "HRE430-030300-050-S04":"Ø3",
    "HMB230-010020-050-S04":"R0,5",
    "HMB230-015030-050-S04":"R0,75",
    "HMB230-020040-050-S04":"R1",
    "HMB230-030060-050-S04":"R1,5",
    "HMB230-040080-050-S04":"R2",
    "HMB230-050100-050-S06":"R2,5",
    "HMB230-060120-050-S06":"R3",
    "HMB230-080160-60-S08":"R4",
    "HMB230-100200-075-S10":"R5",
    "04*90 2F":"Ø4",
    "04*90 3F":"Ø4",
    "06*90 3F":"Ø6",
    "08*90 2F":"Ø8",
    "08*90 3F":"Ø8",
    "10*90 3F":"Ø10",
    "04*90 ":"Ø4",
    "06*90 ":"Ø6",
    "08*90 ":"Ø8",
    "06*90 2F":"Ø6",
    "10*90 2F ":"Ø10",
    "KAA 20×0,3×6×24T":"",
    "KAA 20×0,3×6×32T":"",
    "KAA 25×0,3×8×24T":"",
    "KAA 20×0,4×6×24T":"",
    "KAA 20×0,4×6×32T":"",
    "KAA 25×0,4×8×32T":"",
    "KAA 32×0,5×8×48T":"",
    "KAA 20×0,5×6×32T":"",
    "KAA 32×0,5×8×32T":"",
    "KAA 20×0,6×6×32T":"",
    "KAA 32×0,6×8×48T":"",
    "KAA 20×0,7×6×32T":"",
    "KAA 32×0,7×8×48T":"",
    "KAA 20×0,8×6×32T":"",
    "KAA 32×0,8×8×48T":"",
    "KAA 20×1,0×6×32T":"",
    "KAA 20×1,0×6×48T":"",
    "KAA 32×1,0×6×32T":"",
    "KAA 32×1,0×8×24T-R0,5":"",
    "KAA 32×1,0×8×48T":"",
    "KAA 20×1,1×6×32T":"",
    "KAA 20×1,1×6×48T":"",
    "KAA 25×1,1×8×32T":"",
    "KAA 32×1,1×8×48T":"",
    "KAA 20×1,2×6×40T":"",
    "KAA 20×1,2×6×48T":"",
    "KAA 25×1,2×8×32T":"",
    "KAA 32×1,2×8×48T":"",
    "KAA 32×1,3×6×48T":"",
    "KAA 32×1,3×8×48T":"",
    "KAA 20×1,4×6×48T":"",
    "KAA 32×1,4×8×48T":"",
    "KAA 20×1,6×6×48T":"",
    "KAA 32×1,6×8×48T":"",
    "KAAD 25×2,0×6×50T":"",
    "KAA 32*0,5*6*32T":"",
    "KAA 32*0,6*6*32T":"",
    "KAA 32*0,7*8*48T":"",
    "KAA 32*0,8*6*32T":"",
    "KAA 32*1,0*6*32T":"",
    "KAA 32*1,0*8*48T":"",
    "KAA 32*1,3*6*48T":"",
    "KAA 25*1,5*8*32T":"",
    }
    groups = set()
    group = None
    result = None
    plans_ids = engine_plan.get_all_ids()
    for _, key in enumerate(names):
        name = names[key]
        if name not in groups:
            groups.add(name)
            index = max(engine_group.get_all_ids(), default=0) + 1
            description = ""
            try:
                description = description_group[key]
            except:...
            engine_group.add_group(
                index=index,
                name=name,
                description=description,
                status=0,
            )
            group = engine_group.get(index)
        plan_id = random.choice(plans_ids)
        description = ""
        try:
            description = description_tools[key]
        except:...
        barcode=str(random.randint(11111, 99999))
        result = engine_tools.add_tool(
            id=max(engine_tools.get_all_ids(), default=0)+1,
            barcode=barcode,
            name=name+" "+key,
            description=description,
            img=img,
            plan_id=plan_id,
            groups_id=group.id
        )

        assert result is True, "Инструмент не был добавлен"

        added_tool = test_session.query(Tools).filter_by(barcode=barcode).first()
        assert added_tool is not None, "Инструмент не найден в базе данных"
        assert added_tool.name == name
        assert added_tool.description == description
        assert added_tool.img == img
        assert added_tool.plan_id == plan_id
        assert added_tool.groups_id == group.id


def test_get_tool_by_id(engine_tools, setup_data, test_session):
    """
    Тест получения инструмента по ID.
    """
    plan, group = setup_data
    new_tool = Tools(
        id=random.randint(1, 9999),
        barcode=str(random.randint(11111, 99999)),
        name="Отвертка",
        description="Плоская отвертка",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(new_tool)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_tools.get_tool_by_id(new_tool.id)
    assert result is not None, "Инструмент по ID не найден"
    assert result.name == "Отвертка"
    assert result.description == "Плоская отвертка"


def test_update_tool_success(engine_tools, setup_data, test_session):
    """
    Тест успешного обновления инструмента.
    """
    plan, group = setup_data
    new_tool = Tools(
        id=random.randint(1, 9999),
        barcode=str(random.randint(11111, 99999)),
        name="Отвертка",
        description="Плоская отвертка",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(new_tool)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    updated_name = "Крестовая отвертка"
    updated_description = "Крестовая отвертка для работы с саморезами"

    result = engine_tools.update_tool(new_tool.id, name=updated_name, description=updated_description)

    assert result is True, "Инструмент не был обновлен"

    updated_tool = test_session.query(Tools).filter_by(id=new_tool.id).first()
    assert updated_tool.name == updated_name
    assert updated_tool.description == updated_description


def test_delete_tool_success(engine_tools, setup_data, test_session):
    """
    Тест успешного удаления инструмента.
    """
    plan, group = setup_data
    new_tool = Tools(
        id=random.randint(1, 9999),
        barcode=str(random.randint(11111, 99999)),
        name="Отвертка",
        description="Плоская отвертка",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(new_tool)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    result = engine_tools.delete_tool(new_tool.id)
    assert result is True, "Инструмент не был удален"

    deleted_tool = test_session.query(Tools).filter_by(id=new_tool.id).first()
    assert deleted_tool is None, "Инструмент не был удален из базы данных"


# def test_get_tools_with_relations(engine_tools, setup_data, test_session):
#     """
#     Тест получения инструментов с их связанными данными.
#     """
#     plan, group = setup_data
#     new_tool = Tools(
#         id=random.randint(1, 9999),
#         barcode="67890",
#         name="Отвертка",
#         description="Плоская отвертка",
#         img="screwdriver.png",
#         plan_id=plan.id,
#         groups_id=group.id
#     )
#     test_session.add(new_tool)
#     test_session.commit()
#
#     tools_with_relations = engine_tools.get_tools_with_relations()
#
#     assert len(tools_with_relations) > 0, "Инструменты с их отношениями не были найдены"
#     assert tools_with_relations[0].name == "Отвертка"
#     assert tools_with_relations[0].plans is not None
#     assert tools_with_relations[0].groups is not None


def test_get_tools_by_group(engine_tools, setup_data, test_session):
    """
    Тест получения инструментов по ID группы.
    """
    plan, group = setup_data
    new_tool = Tools(
        id=random.randint(1, 9999),
        barcode=str(random.randint(11111, 99999)),
        name="Отвертка",
        description="Плоская отвертка",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(new_tool)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    tools_by_group = engine_tools.get_tools_by_group(group.id)

    assert len(tools_by_group) > 0, "Инструменты для группы не найдены"
    assert tools_by_group[0].name == "Отвертка"


def test_get_tools_by_plan(engine_tools, setup_data, test_session):
    """
    Тест получения инструментов по ID плана.
    """
    plan, group = setup_data
    new_tool = Tools(
        id=random.randint(1, 9999),
        barcode=str(random.randint(11111, 99999)),
        name="Отвертка",
        description="Плоская отвертка",
        img="screwdriver.png",
        plan_id=plan.id,
        groups_id=group.id
    )
    test_session.add(new_tool)
    try:
        test_session.commit()
    except Exception:
        test_session.rollback()
        raise

    tools_by_plan = engine_tools.get_tools_by_plan(plan.id)

    assert len(tools_by_plan) > 0, "Инструменты для плана не найдены"
    assert tools_by_plan[0].name == "Отвертка"

# def test_get_tool_history(engine_tools, setup_data, test_session):
#     """
#     Тест получения истории инструмента.
#     """
#     plan, group = setup_data
#     new_tool = Tools(
#         id=random.randint(1, 9999),
#         barcode="67890",
#         name="Отвертка",
#         description="Плоская отвертка",
#         img="screwdriver.png",
#         plan_id=plan.id,
#         groups_id=group.id
#     )
#     test_session.add(new_tool)
#     test_session.commit()
#
#     history_entry = History(tool_id=new_tool.id, event="Добавление инструмента", timestamp=datetime.utcnow())
#     test_session.add(history_entry)
#     test_session.commit()
#
#     tool_history = engine_tools.get_tool_history(new_tool.id)
#     assert len(tool_history) > 0, "История инструмента не найдена"
#     assert tool_history[0].event == "Добавление инструмента"
