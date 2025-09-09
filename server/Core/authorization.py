from __future__ import annotations

# services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt import PyJWTError
from fastapi import Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError

from options import SECRET_KEY


class TokenData(BaseModel):
    user_id: int
    user_barcode: int
    role_id: int


class AuthService:
    """
    Сервис для работы с JWT через строго определённую модель данных.
    """
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 180

    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self,
                            token_data: TokenData,
                            expires_delta: Optional[timedelta] = None
                            ) -> str:
        """
        Создаёт JWT по данным TokenData с временем жизни токена.
        """
        to_encode = token_data.dict()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenData | dict:
        """
        Декодирует JWT. При успешной валидации возвращает объект TokenData.
        При ошибке возвращает словарь с описанием ошибки.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(**payload)
        except (PyJWTError, ValidationError) as e:
            return {"status": "error", "url": "/error_token.html", "detail": str(e)}

    def extract_token(self, request: Request) -> Optional[str]:
        """
        Пытается достать токен из заголовка Authorization или query-параметра.
        """
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth.split(None, 1)[1]
        return request.query_params.get("token")

    def validation_user(self, request: Request) -> TokenData | RedirectResponse | dict:
        """
        Извлекает токен из запроса и валидирует его.
        При успехе — возвращает TokenData.
        При отсутствии токена — RedirectResponse на /.
        При ошибке токена — dict c ошибкой.
        """
        token = self.extract_token(request)
        if not token:
            return RedirectResponse("/", status_code=302)
        return self.verify_token(token)

# from datetime import datetime, timedelta
# from typing import Optional
#
# import jwt
# from fastapi import HTTPException, Header, status
# from fastapi import Query
# from pydantic import BaseModel
#
# from options import secret_key
#
# # Конфигурация JWT
# SECRET_KEY = secret_key  # Замените на реальный секретный ключ
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30
#
#
# # --------- Pydantic модели ---------
# class WriteHelpRequest(BaseModel):
#     text: str
#     date: Optional[datetime] = None
#
#
# class UpdateHelpRequest(BaseModel):
#     help_id: int
#     text: Optional[str] = None
#     date: Optional[datetime] = None
#
#
# class TokenData(BaseModel):
#     user_id: str
#
#
# # --------- JWT Функции ---------
# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#
#
# class ExpiredSignatureError(Exception):
#     pass
#
#
# class InvalidTokenError(Exception):
#     pass
#
# def verify_token(token: str):
#     """
#     Верифицирует JWT токен и возвращает payload
#
#     Args:
#         token: JWT токен в виде строки
#
#     Returns:
#         dict: Декодированный payload токена
#
#     Raises:
#         HTTPException: 401 UNAUTHORIZED для всех ошибок валидации
#     """
#     try:
#         payload = jwt.decode(
#             token,
#             SECRET_KEY,
#             algorithms=[ALGORITHM],
#             options={"require_exp": True}  # Обязательная проверка срока действия
#         )
#         return payload
#
#     except ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token expired",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except InvalidTokenError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Invalid token: {str(e)}",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except jwt.PyJWTError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Token verification failed: {str(e)}",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
# # --------- Dependency для аутентификации ---------
# async def get_current_user(
#         authorization_header: Optional[str] = Header(None, alias="Authorization"),
#         authorization_query: Optional[str] = Query(None, alias="authorization")
# ) -> TokenData:
#     """
#     Аутентификация пользователя через JWT токен.
#     Поддерживает два способа передачи:
#     1. В заголовке Authorization: Bearer <token>
#     2. В query-параметре authorization: Bearer <token>
#
#     Приоритет: Заголовок > Query-параметр
#     """
#     # token_source = None
#     # auth_value = None
#
#     # Определяем источник токена
#     if authorization_header:
#         token_source = "header"
#         auth_value = authorization_header
#     elif authorization_query:
#         token_source = "query"
#         auth_value = authorization_query
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization credentials missing",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     # Извлекаем схему и токен
#     try:
#         scheme, token = auth_value.split(maxsplit=1)
#         scheme = scheme.strip().lower()
#     except ValueError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Invalid authorization format from {token_source}",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     # Проверяем схему
#     if scheme != "bearer":
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Invalid authentication scheme in {token_source}",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     # Проверяем и возвращаем токен
#     try:
#         payload = verify_token(token)
#         return TokenData(**payload)
#     except HTTPException as e:
#         e.headers = {"WWW-Authenticate": "Bearer"}
#         raise
#
#
#
# class WriteCellRequest(BaseModel):
#     index: int
#     number: int
#     tools_id: int
#     status_id: int
#     groups_id: Optional[int] = None
#     description: Optional[str] = None
#
#
# class UpdateCellRequest(BaseModel):
#     cell_id: int
#     number: Optional[int] = None
#     tools_id: Optional[int] = None
#     status_id: Optional[int] = None
#     groups_id: Optional[int] = None
#     description: Optional[str] = None
#
#
# class UpdateCellStatusRequest(BaseModel):
#     cell_id: int
#     status_id: int
