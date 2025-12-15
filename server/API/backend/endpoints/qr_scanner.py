# API/backend/endpoints/history_operation.py
import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List

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
    content: List[str]


@qr_scanner_router.post("/qr/", response_model=QrResponse)
def get_qr_text(data: QrRequest):

    strings = data.content
    decoded_strings = []
    for string in strings:
        text_string = string.encode().decode('u8').encode('cp1251', 'ignore').decode('u8', 'ignore')
        decoded_strings.append(text_string)

    return {'content':  decoded_strings}