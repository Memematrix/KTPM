from src.modules.scheduling.models import Seat
from src.common.auth.role_guard import require_role
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Date, cast, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.scheduling import models
from src.common.database import get_db
from src.modules.scheduling.schemas import (
    AvailableSeatResponse,
    ShowtimeCreate,
    ShowtimeResponse,
)

router = APIRouter()

@router.get("", response_model=list[ShowtimeResponse])
async def get_showtimes(movie_id: uuid.UUID, date: date, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Showtime).where(models.Showtime.movie_id == movie_id, cast(models.Showtime.start_time, Date) == date))
    showtimes = result.scalars().all()
    if not showtimes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No showtime available"
        )
    return showtimes

@router.get("/{showtime_id}", response_model=AvailableSeatResponse)
async def get_showtime_detail(showtime_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Showtime).where(models.Showtime.id == showtime_id).options(selectinload(models.Showtime.screen).selectinload(models.Screen.seats), selectinload(models.Showtime.tickets)))
    showtime = result.scalars().first()
    if not showtime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showtime not exist"
        )
    booked_seat_ids = {ticket.seat_id for ticket in showtime.tickets}

    available_seats = [
        {
            "seat": seat,
            "is_available": seat.id not in booked_seat_ids
        } 
        for seat in showtime.screen.seats
    ]

    return {
        "showtime": showtime,
        "available_seats": available_seats
    }

@router.post("", response_model=ShowtimeResponse, status_code=status.HTTP_201_CREATED)
async def create_showtime(showtime: ShowtimeCreate, db: Annotated[AsyncSession, Depends(get_db)], current_user = Depends(require_role("admin"))):
    if showtime.start_time >= showtime.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )

    result = await db.execute(select(models.Movie).where(models.Movie.id == showtime.movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not exist"
        )
    result = await db.execute(select(models.Screen).where(models.Screen.id == showtime.screen_id))
    screen = result.scalars().first()
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screen not exist"
        )
    # Check if the new showtime time overlap with showtimes from the same screen
    result = await db.execute(select(models.Showtime).where(models.Showtime.screen_id == showtime.screen_id, models.Showtime.start_time < showtime.end_time, models.Showtime.end_time > showtime.start_time))

    overlap_screen = result.scalars().first()

    if overlap_screen:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Screen already has an overlapping showtime during this period"
        )

    new_showtime = models.Showtime(
        movie_id = showtime.movie_id,
        screen_id = showtime.screen_id,
        start_time = showtime.start_time,
        end_time = showtime.end_time,
        base_price = showtime.base_price,
    )

    db.add(new_showtime)
    await db.commit()
    await db.refresh(new_showtime, attribute_names=["movie", "screen"])
    return new_showtime

@router.delete("/{showtime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_showtime(showtime_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user = Depends(require_role("admin"))):
    result = await db.execute(select(models.Showtime).where(models.Showtime.id == showtime_id))
    showtime = result.scalars().first()
    if not showtime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showtime not found",
        )

    await db.delete(showtime)
    await db.commit()
