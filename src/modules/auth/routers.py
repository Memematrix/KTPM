"""
Auth Router — tầng API.

"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from src.common.database import get_db
from src.common.auth.jwt import create_access_token
from src.common.auth.middleware import get_current_user, CurrentUser
from src.common.auth.role_guard import require_role
from src.common.auth.hash_pw import hash_password as hashpw, verify_password

from .schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from .models import User


router = APIRouter(prefix="/auth", tags=["auth"])




@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản (không cần xác thực)",
)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(User).where(User.username == payload.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exist"
        )

    hash_pw = hashpw(payload.password)
    new_user = User(
        username = payload.username,
        password_hash = hash_pw,
        name = payload.name,
        phone = payload.phone
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):

    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username"
        )
    hash_pw = user.password_hash
    if verify_password(payload.password, hash_pw):
        token = create_access_token(
            user_id=user.id,
            role=user.role
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect password"
    )



@router.get(
    "/me",
    response_model=UserResponse,
    summary="Thông tin user hiện tại (cần xác thực) — endpoint GET có auth theo yêu cầu đề bài",
)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()

    return user