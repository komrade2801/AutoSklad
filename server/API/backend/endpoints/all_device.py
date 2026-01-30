# import traceback
import traceback
from typing import Optional # List,

from Core.app_logging import get_logger

logger = get_logger(__name__)

# from sqlalchemy.orm import Session
from fastapi import APIRouter, status  # Depends, Request, HTTPException,
# from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
# import secrets
# from API.backend.request_models import (UserResponse, RoleResponse, UserUpdate,
#                                         UserPartialUpdate, UserCreate, RoleUpdate,
#                                         RoleCreate, RightsCreate, RightsResponse,
#                                         RightsUpdate, AllUserResponse,
#                                         UserCredentialsInput, UserCredentialsResponse)  # AuthResponse, , DeviceResponse, AllDeviceResponse
from Core.authorization import AuthService  # , TokenData
# # from DB.Data.db_depends import get_db
# from DB.session import get_db
from DB.session import get_db
from DB.Engine.DeviceCRUD import EngineDevice
# from DB.Engine.RightsCRUD import EngineRights
# from DB.Engine.RoleCRUD import EngineRole
# from DB.Engine.UserCRUD import EngineUser
# import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
# from datetime import timedelta, datetime  # datetime,
# from API.backend.request_models import AuthResponse  # путь и название модели может отличаться
# import barcode
# from barcode.writer import ImageWriter
# from fastapi.responses import StreamingResponse
# from fastapi.responses import FileResponse
# from io import BytesIO
# from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import requests


auth_service = AuthService()
all_device_router = APIRouter(tags=["all_device"])

# Маршрутизатор для работы с устройствами
# e_device_router = APIRouter(tags=["all_device"])

# -- Новые Pydantic-модели для найденных устройств --
class Cell(BaseModel):
    length: int  # длина в ячейках
    columns: int  # количество столбцов
    rows: int  # количество строк

class Signature(BaseModel):
    serial_number: int  # серийный номер устройства
    cells: Cell  # параметры ячеек

class NetworkInfo(BaseModel):
    ip: str  # IP-адрес устройства
    port: int  # сетевой порт

class SerialConfig(BaseModel):
    port: str  # COM-порт для последовательного подключения
    baudrate: int  # скорость передачи данных

class BarcodeConfig(BaseModel):
    port: str  # COM-порт для сканера штрихкода
    baudrate: int  # скорость передачи данных сканера

class Locks(BaseModel):
    load_locked: int  # флаг блокировки загрузки
    drop_locked: int  # флаг блокировки выгрузки

class Logs(BaseModel):
    critical_errors: List[str]  # список критических ошибок

class Details(BaseModel):
    signature: Signature  # подпись устройства
    network: NetworkInfo  # сетевая информация
    serial: SerialConfig  # конфигурация последовательного интерфейса
    barcode: BarcodeConfig  # конфигурация сканера штрихкода
    locks: Locks  # состояние замков
    logs: Logs  # журналы ошибок

class ScannedDevice(BaseModel):
    details: Details  # детальная информация об устройстве
    registrationDate: datetime  # дата обнаружения/регистрации

class ScanDevicesResponse(BaseModel):
    devices: List[ScannedDevice]  # список найденных устройств

class DeviceResponse(BaseModel):
    name: str
    description: str
    details: str
    registrationDate: Optional[datetime]


class AllDeviceResponse(BaseModel):
    devices: List[DeviceResponse]


class DeviceCreate(BaseModel):
    number: int
    name: str
    description: str
    details: str
    create: Optional[datetime]


class DevicePartialUpdate(BaseModel):
    number: Optional[int]
    name: Optional[str]
    description: Optional[str]
    details: Optional[str]
    create: Optional[datetime]


class DeviceUpdate(BaseModel):
    number: int
    name: str
    description: str
    details: str
    create: datetime

# -- Механизм обнаружения устройств по HTTP --
def scan_network_for_devices_http(
    network_prefix: str = "192.168.0",  # префикс сети (первые три октета)
    device_port: int = 8000,  # HTTP-порт на устройстве
    endpoint: str = "/device_info",  # путь эндпоинта на устройстве
    timeout: float = 1.0  # таймаут HTTP-запроса в секундах
) -> List[Dict[str, Any]]:
    """
    Пытается опросить устройства по HTTP в заданном диапазоне IP-адресов:
    1. Формирует адреса от network_prefix.1 до network_prefix.254
    2. Отправляет GET-запрос на каждый адрес: порт device_port и путь endpoint
    3. Если устройство отвечает корректным JSON, добавляем его в список
    :param network_prefix: первые три октета сети, например "192.168.0"
    :param device_port: порт HTTP-сервера на устройстве
    :param endpoint: путь эндпоинта для получения информации об устройстве
    :param timeout: максимальное время ожидания ответа в секундах
    :return: список словарей с данными устройств
    """
    discovered: List[Dict[str, Any]] = []
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        url = f"http://{ip}:{device_port}{endpoint}"
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                payload = resp.json()
                # Заполняем поле IP из URL
                payload['details']['network']['ip'] = ip
                payload['details']['network']['port'] = device_port
                discovered.append(payload)
        except requests.RequestException:
            # устройство не отвечает или не HTTP-клиент
            continue
    return discovered



# -- Новый эндпоинт для сканирования устройств --
@all_device_router.get(
    "/scan_devices",
    response_model=ScanDevicesResponse,
    status_code=status.HTTP_200_OK
)
def scan_devices(
    network_prefix: str = "192.168.0",  # префикс сети
    device_port: int = 8000,  # порт устройств
    endpoint: str = "/device_info",  # путь эндпоинта устройств
    timeout: float = 1.0  # таймаут опроса
):
    """
    Обнаруживает незарегистрированные устройства по HTTP в локальной сети и возвращает их данные.
    :param network_prefix: префикс сети (первые три октета)
    :param device_port: HTTP-порт устройств
    :param endpoint: путь эндпоинта для сбора данных
    :param timeout: время ожидания ответа от каждого устройства
    :return: JSON с информацией о найденных устройствах
    """
    raw_devices = scan_network_for_devices_http(
        network_prefix=network_prefix,
        device_port=device_port,
        endpoint=endpoint,
        timeout=timeout
    )
    if not raw_devices:
        raise HTTPException(status_code=404, detail="Устройства в сети не обнаружены")

    try:
        devices = [ScannedDevice(**device) for device in raw_devices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при разборе данных устройства: {e}")

    return ScanDevicesResponse(devices=devices)



@all_device_router.get(
    "/all_device",
    response_model=AllDeviceResponse,
    status_code=status.HTTP_200_OK
)
def all_device(db: Session = Depends(get_db)):
    e_device = EngineDevice()
    devices = e_device.get_all_devices()
    if not devices:
        raise HTTPException(status_code=404, detail="Устройства не найдены")

    all_devices = [
        DeviceResponse(
            name=f"{d.name} №{d.number}",
            description=d.description,
            details=d.details,
            registrationDate=d.create
        )
        for d in devices
    ]
    return AllDeviceResponse(devices=all_devices)


@all_device_router.post("/create_device", response_model=DeviceResponse)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    e_device = EngineDevice()
    try:
        created_device = e_device.create_device(**device.to_dict())

        if not created_device:
            raise HTTPException(status_code=400, detail="Ошибка создания пользователя")
        return DeviceResponse(
            number=created_device.number,
            name=created_device.name,
            description=created_device.description,
            details=created_device.details,
            create=created_device.create,
        )
    except IntegrityError: # as ie
        # например, код занят
        raise HTTPException(status_code=409, detail="Code already exists")
    except Exception: # as e
        # любые другие ошибки
        logger.exception("create_device")
        raise HTTPException(status_code=500, detail="Unexpected server error")


@all_device_router.put("/update_device/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, device_data: DeviceUpdate, db: Session = Depends(get_db)):
    """
    Полностью обновляет данные устройства по его идентификатору.

    :param device_id: Идентификатор устройства.
    :param device_data: Объект с новыми данными устройства.
    :param db: Сессия для работы с базой данных.
    :return: Обновленный устройство.
    """

    e_device = EngineDevice()
    updated_device = e_device.put_device(device_id, device_data)
    if not updated_device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return updated_device


@all_device_router.patch("/patch_device/{device_id}", response_model=DeviceResponse)
def patch_device(device_id: int, device_data: DevicePartialUpdate, db: Session = Depends(get_db)):
    """
    Частично обновляет данные устройства по его идентификатору.

    :param device_id: Идентификатор устройства.
    :param device_data: Объект с данными для частичного обновления.
    :param db: Сессия для работы с базой данных.
    :return: Обновленный устройство.
    """

    e_device = EngineDevice()
    patched_device = e_device.patch_device(device_id, device_data)
    if not patched_device:
        raise HTTPException(status_code=404, detail="Устройство не найден")
    return patched_device


@all_device_router.delete("/delete_device/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    """
    Удаляет устройство по идентификатору.

    :param device_id: Идентификатор устройства.
    :param db: Сессия базы данных.
    :return: Сообщение об успешном удалении.
    """

    e_device = EngineDevice()
    if not e_device.delete_device(device_id):
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return {"detail": "Запись о устройстве успешно удалена"}
