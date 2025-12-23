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
    Поддерживает два формата:
    1. Массив строк (каждая строка - отдельный блок)
    2. Одна строка с табуляциями в качестве разделителей
    
    Логика парсинга:
    Блок 0 (первый) → designation
    Блок 3 (четвертый, индекс 3) → enterprise
    Блок 4 (пятый, индекс 4) → добавляется к designation через дефис
    Блок 5 (шестой, индекс 5) → name
    description → пустая строка
    
    Поддерживает пустые блоки (две табуляции подряд = пустой блок)
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
    
    blocks = []
    
    # Если пришла одна строка с табуляциями - разбиваем её
    if len(decoded_strings) == 1 and '\t' in decoded_strings[0]:
        logger.info("Обнаружена одна строка с табуляциями, разбиваем на блоки")
        # Разбиваем по табуляциям, сохраняя пустые блоки
        raw_blocks = decoded_strings[0].split('\t')
        # Обрабатываем каждый блок
        for block in raw_blocks:
            blocks.append(block)
        logger.info(f"Разбито на {len(blocks)} блоков")
    else:
        # Используем массив строк как массив блоков
        blocks = decoded_strings
        logger.info(f"Используем массив строк как блоки (количество: {len(blocks)})")
    
    if blocks:
        # Логируем все блоки
        for i, block in enumerate(blocks):
            block_stripped = block.strip()
            logger.info(f"  Блок [{i}]: {repr(block)} (длина: {len(block)}, после strip: {repr(block_stripped)})")
        
        # Блок 0 (первый) → designation
        designation = blocks[0].strip() if len(blocks) > 0 and blocks[0].strip() else ""
        logger.info(f"Блок 0 → designation (начальное): {repr(designation)}")
        
        # Блок 3 (четвертый, индекс 3) → enterprise
        enterprise = ""
        if len(blocks) > 3:
            block_3_raw = blocks[3]
            block_3 = block_3_raw.strip()
            logger.info(f"Блок 3 (индекс 3): {repr(block_3_raw)} → после strip: {repr(block_3)}")
            if block_3:  # Если блок не пустой после strip
                enterprise = block_3
                logger.info(f"  Блок 3 → enterprise: {repr(enterprise)}")
            else:
                logger.info(f"  Блок 3 пустой, enterprise останется пустым")
        else:
            logger.warning(f"Блок 3 отсутствует (всего блоков: {len(blocks)})")
        
        # Блок 4 (пятый, индекс 4) → добавляется к designation через дефис
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
                logger.info(f"  Блок 4 пустой, не добавляется к designation")
        else:
            logger.warning(f"Блок 4 отсутствует (всего блоков: {len(blocks)})")
        
        # Блок 5 (шестой, индекс 5) → name
        name = ""
        if len(blocks) > 5:
            block_5_raw = blocks[5]
            block_5 = block_5_raw.strip()
            logger.info(f"Блок 5 (индекс 5): {repr(block_5_raw)} → после strip: {repr(block_5)}")
            if block_5:  # Если блок не пустой после strip
                name = block_5
                logger.info(f"Блок 5 → name: {repr(name)}")
            else:
                logger.info(f"  Блок 5 пустой, name останется пустым")
        else:
            logger.warning(f"Блок 5 отсутствует (всего блоков: {len(blocks)})")
        
        # description → пустая строка
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