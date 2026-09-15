"""
JWT Utility — tạo (sign) và kiểm tra (verify) JSON Web Token.

Contract chung cho cả nhóm (đã chốt trong Sprint 0):
    payload JWT chứa: { "sub": <user_id>, "role": <role>, "iat": ..., "exp": ... }

Lưu ý đặt tên: file này tên là jwt.py và nằm trong package `common`
(common/jwt.py), nên bên trong ta import thư viện PyJWT với alias `pyjwt`
để không gây nhầm lẫn giữa "module nội bộ" và "thư viện ngoài".
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status

import jwt as pyjwt

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES"))


class TokenPayload:
    """
    Đại diện cho payload sau khi verify JWT thành công.
    Đây chính là object được trả về cho Auth Middleware để tạo "req.user"
    tương đương (xem middleware.py -> CurrentUser).
    """

    def __init__(self, user_id: str, role: str):
        self.id = user_id
        self.role = role

    def __repr__(self) -> str:
        return f"TokenPayload(id={self.id!r}, role={self.role!r})"


def create_access_token(user_id: str, role: str, expires_minutes: Optional[int] = None) -> str:
    """
    Tạo JWT sau khi login thành công (dùng ở endpoint POST /auth/login).

    :param user_id: uuid của user (cột users.id)
    :param role: "admin" | "customer"
    :param expires_minutes: override thời hạn token; mặc định = JWT_EXPIRE_MINUTES
    :return: chuỗi JWT chứ chưa phải chuối json
    Sau này ở endpoint /auth/login sẽ nhận token này rồi xử lý để tạo chuỗi json

    cách dùng:
    @app.post("/auth/login")
    def login(...):
        ...
        token = create_access_token(
            user_id=user.id,
            role=user.role
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }
    
    """
    now = datetime.now(timezone.utc)
    expire_delta = timedelta(
        minutes=expires_minutes if expires_minutes is not None else JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),        # subject — quy ước chuẩn JWT để lưu id chủ thể token
        "role": role,
        "iat": now,                 # issued at
        "exp": now + expire_delta,  # expiry
    }

    return pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> TokenPayload:
    """
    Verify chữ ký + hạn dùng của token (KHÔNG chỉ decode).

    :raises jwt.ExpiredSignatureError: token đã hết hạn
    :raises jwt.InvalidTokenError: token sai định dạng / sai chữ ký / thiếu field
    :return: TokenPayload nếu hợp lệ
    """
    try:
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    role = payload.get("role")

    if user_id is None or role is None:
        raise pyjwt.InvalidTokenError("Token thiếu field 'sub' hoặc 'role'")

    return TokenPayload(user_id=user_id, role=role)