from datetime import datetime
from sqlalchemy.exc import IntegrityError
from src.schemas import SeatCreate, SeatResponse, ScreenCreate
import uuid
from src.common.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from src import models
from src.common.auth.role_guard import require_role
from sqlalchemy.orm import selectinload
router = APIRouter()

@router.get("/")
async def get_current_showtimes_from_movie(movie_id: uuid.UUID, date: datetime, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Showtime).where(models.Showtime.movie_id == movie_id and models.Showtime.start_time == date))
    showtime = result.scalars().first()
    return showtime