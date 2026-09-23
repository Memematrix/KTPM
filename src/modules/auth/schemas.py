"""
Pydantic schemas — định nghĩa hình dạng request/response cho API auth.
Dùng để FastAPI tự validate input và tự sinh OpenAPI/Swagger docs.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)


class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    # from_attributes=True cho phép tạo trực tiếp từ UserEntity (dataclass),
    # không cần convert thủ công từng field.
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    name: str
    phone: Optional[str] = None
    role: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


    