"""
Auth Middleware — dùng chung cho toàn hệ thống (đúng yêu cầu: "xác thực qua
middleware/filter/interceptor của framework, không viết lặp trong từng endpoint").

Ghi chú kiến trúc: FastAPI không có middleware kiểu Express (gắn req.user rồi
next()). Cơ chế tương đương và được khuyến nghị trong FastAPI là Dependency
Injection (Depends) — 1 dependency được định nghĩa 1 lần ở đây, các module
B/C chỉ cần khai báo Depends(get_current_user) trong route, không viết lại
logic verify JWT.

Cách dùng ở B / C:

    from fastapi import Depends
    from common.middleware import get_current_user, CurrentUser

    @router.post("/orders")
    def create_order(current_user: CurrentUser = Depends(get_current_user)):
        user_id = current_user.id
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt as pyjwt

from .jwt import verify_access_token, TokenPayload as CurrentUser  # re-export cho dễ đọc ở nơi dùng

__all__ = ["get_current_user", "CurrentUser"]

# HTTPBearer tự động đọc header: Authorization: Bearer <token>
# auto_error=False để tự kiểm soát response 401 thay vì để FastAPI trả lỗi mặc định.
_bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    Dependency dùng ở MỌI endpoint cần đăng nhập — đây là "Auth Middleware".

    Luồng xử lý:
        Request -> lấy JWT từ Authorization header -> verify JWT
        -> lấy payload -> trả về CurrentUser (id, role)

    - Không có JWT trong header        -> 401
    - JWT sai định dạng / hết hạn      -> 401
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        current_user = verify_access_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user