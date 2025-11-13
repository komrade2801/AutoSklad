# import traceback
import traceback
from typing import List

# from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, status  # Depends, HTTPException,
from sqlalchemy.exc import IntegrityError
import secrets
from API.backend.request_models import (UserResponse, RoleResponse, UserUpdate,
                                        UserPartialUpdate, UserCreate, RoleUpdate,
                                        RoleCreate, RightsCreate, RightsResponse,
                                        RightsUpdate, AllUserResponse,
                                        UserCredentialsInput, UserCredentialsResponse, StatusResponse)  # AuthResponse,
from Core.authorization import AuthService, TokenData
from DB.Engine.StatusCRUD import EngineStatus
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.RightsCRUD import EngineRights
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.UserCRUD import EngineUser
# import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta  # datetime,
# путь и название модели может отличаться
from API.backend.request_models import AuthResponse
import barcode
from barcode.codex import Code128
from barcode.writer import ImageWriter
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


# from frontend.front_router import validation_user
# from get_token import SECRET_KEY
auth_service = AuthService()
# Настройки для JWT
# SECRET_KEY = "your_secret_key_here"

status_router = APIRouter(tags=["status"])

@status_router.get(
    "/status/{status_id}",
    response_model=StatusResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Ошибка при получении статуса"}}
)
def get_status(status_id: int, db: Session = Depends(get_db)):
    # 1) Получаем статус
    e_status = EngineStatus()
    status = e_status.get_status_by_id(status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    return {
        "id": status.id,
        "stype": status.stype,
        "description": status.description
    }


@status_router.get(
    "/status",
    response_model=List[StatusResponse],
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Ошибка при получении статусов"}}
)
def get_status(db: Session = Depends(get_db)):
    e_status = EngineStatus()
    status_list = e_status.all()
    if not status_list:
        raise HTTPException(status_code=404, detail="Statuses were not found")

    status_result = []

    for status in status_list:
        status_result.append({
            "id": status.id,
            "stype": status.stype,
            "description": status.description
        })

    return status_result