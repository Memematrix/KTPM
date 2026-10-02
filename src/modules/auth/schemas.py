"""
Pydantic schemas — định nghĩa hình dạng request/response cho API auth.
Dùng để FastAPI tự validate input và tự sinh OpenAPI/Swagger docs.
"""

from uuid import UUID
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# User
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



# Movies

class MovieCreate(BaseModel):
    title: str
    description: str | None = None
    duration: int
    release_date: date
    poster_url: str | None = None


class MovieUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    duration: int | None = None
    release_date: date | None = None
    poster_url: str | None = None


class MovieResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    duration: int
    release_date: date | None
    poster_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Reviews

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    movie_id: UUID
    rating: int
    comment: str | None
    created_at: datetime