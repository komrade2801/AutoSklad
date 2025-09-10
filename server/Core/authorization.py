from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Union

import jwt  # This must be PyJWT, not 'jwt' package
from fastapi import Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError

from options import SECRET_KEY


class TokenData(BaseModel):
    user_id: int
    user_barcode: int
    role_id: int


class AuthService:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 180

    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(
        self,
        token_data: TokenData,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        payload = token_data.dict()
        expire = datetime.utcnow() + \
            (expires_delta or timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES))
        payload.update({"exp": expire})
        # PyJWT >= 2 returns str
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Union[TokenData, dict]:
        try:
            payload = jwt.decode(token, self.secret_key,
                                 algorithms=[self.algorithm])
            return TokenData(**payload)
        except (jwt.PyJWTError, ValidationError) as e:
            return {"status": "error", "url": "/error_token.html", "detail": str(e)}

    def extract_token(self, request: Request) -> Optional[str]:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth.split(None, 1)[1]
        return request.query_params.get("token")

    def validation_user(self, request: Request):
        token = self.extract_token(request)
        if not token:
            return RedirectResponse("/", status_code=302)
        return self.verify_token(token)
