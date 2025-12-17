# API/backend/endpoints/history_operation.py
import traceback
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List

logger = logging.getLogger(__name__)

from API.backend.request_models import (
    # Pydantic-модель: {"operation": { "0": HistoryOperation, ... } }
    HistoryOperationResponse,
    HistoryOperation,  # Модель записи истории (при чтении/обновлении)
    HistoryOperationCreate,  # Модель для создания записи
    HistoryOperationUpdate  # Модель для обновления записи
)
from DB.Engine.ToolsCRUD import EngineTools
from DB.Engine.UserCRUD import EngineUser
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
from Logic.HistoryOperationCRUD import EngineHistoryOperation
from DB.Engine.Tools_has_DeviceCRUD import EngineToolsHasDevice

qr_scanner_router = APIRouter(tags=["QR Scanner"])



class QrRequest(BaseModel):
    content: List[str]

class QrResponse(BaseModel):
    designation: str
    name: str
    enterprise: str
    description: str


@qr_scanner_router.post("/qr/", response_model=QrResponse)
def get_qr_text(data: QrRequest):
    """
    Декодирует строки QR-кода и парсит их.
    Ожидается одна строка с табуляциями в качестве разделителей.
    Блок 0 (первый) → designation
    Блок 5 (6-й, индекс 5) → добавляется к designation через дефис
    Блок 6 (7-й, индекс 6) → name
    enterprise и description → пустые строки
    """
    logger.info("=" * 60)
    logger.info("QR декодирование: начало обработки")
    logger.info(f"Входные данные (количество строк): {len(data.content)}")
    
    strings = data.content
    decoded_strings = []
    
    # Декодируем все строки
    for idx, string in enumerate(strings):
        logger.info(f"Строка {idx} (исходная): {repr(string)}")
        text_string = string.encode().decode('u8').encode('cp1251', 'ignore').decode('u8', 'ignore')
        decoded_strings.append(text_string)
        logger.info(f"Строка {idx} (декодированная): {repr(text_string)}")
    
    # Данные приходят уже разбитыми на отдельные строки (блоки)
    # Каждая строка в массиве - это отдельный блок
    if decoded_strings:
        # Используем весь массив как массив блоков
        blocks = decoded_strings
        logger.info(f"Количество блоков в массиве: {len(blocks)}")
        
        # Логируем все блоки
        for i, block in enumerate(blocks):
            block_stripped = block.strip()
            logger.info(f"  Блок [{i}]: {repr(block)} (длина: {len(block)}, после strip: {repr(block_stripped)})")
        
        # Блок 0 (первый) → designation
        designation = blocks[0].strip() if len(blocks) > 0 else ""
        logger.info(f"Блок 0 → designation (начальное): {repr(designation)}")
        
        # Блок 4 (индекс 4) → добавляется к designation через дефис
        # По логам видно, что '39' находится в блоке 4, а не в блоке 5
        if len(blocks) > 4:
            block_4_raw = blocks[4]
            block_4 = block_4_raw.strip()
            logger.info(f"Блок 4 (индекс 4): {repr(block_4_raw)} → после strip: {repr(block_4)}")
            logger.info(f"  Блок 4 пустой? {not block_4}")
            logger.info(f"  Блок 4 длина: {len(block_4)}")
            
            if block_4:  # Если блок не пустой после strip
                old_designation = designation
                designation = f"{designation}-{block_4}" if designation else block_4
                logger.info(f"  Добавлен блок 4 к designation: {repr(old_designation)} → {repr(designation)}")
            else:
                logger.warning(f"  Блок 4 пустой, не добавляется к designation")
        else:
            logger.warning(f"Блок 4 отсутствует (всего блоков: {len(blocks)})")
        
        # Блок 6 (индекс 6) → name
        if len(blocks) > 6:
            name = blocks[6].strip()
            logger.info(f"Блок 6 (индекс 6) → name: {repr(name)}")
        else:
            name = ""
            logger.warning(f"Блок 6 отсутствует (всего блоков: {len(blocks)})")
        
        # enterprise и description → пустые строки
        enterprise = ""
        description = ""
        
        result = {
            'designation': designation,
            'name': name,
            'enterprise': enterprise,
            'description': description
        }
        
        logger.info("Результат парсинга:")
        logger.info(f"  designation: {repr(result['designation'])}")
        logger.info(f"  name: {repr(result['name'])}")
        logger.info(f"  enterprise: {repr(result['enterprise'])}")
        logger.info(f"  description: {repr(result['description'])}")
        logger.info("=" * 60)
        
        return result
    else:
        # Если строк нет, возвращаем пустые значения
        logger.warning("Нет декодированных строк для парсинга")
        logger.info("=" * 60)
        return {
            'designation': "",
            'name': "",
            'enterprise': "",
            'description': ""
        }