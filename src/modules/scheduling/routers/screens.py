from sqlalchemy.exc import IntegrityError
from src.modules.scheduling.schemas import SeatCreate, SeatResponse, ScreenCreate
import uuid
from src.common.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from src.modules.scheduling import models
from src.common.auth.role_guard import require_role
from sqlalchemy.orm import selectinload
router = APIRouter()

@router.get("")
async def get_screens(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Screen))
    screens = result.scalars().all()
    return screens

@router.post("")
async def create_screen(screen: ScreenCreate, db: Annotated[AsyncSession, Depends(get_db)], current_user = Depends(require_role("admin"))):
    new_screen = models.Screen(
        name = screen.name,
        total_seats = screen.total_seats
    )

    db.add(new_screen)
    await db.commit()
    await db.refresh(new_screen)
    return new_screen

@router.delete("/{screen_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_screen(screen_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user = Depends(require_role("admin"))):
    result = await db.execute(select(models.Screen).where(models.Screen.id == screen_id))
    screen = result.scalars().first()
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screen not found"
        )
    
    await db.delete(screen)
    await db.commit()

@router.get("/{screen_id}/seats", response_model=list[SeatResponse])
async def get_seats_of_screen(screen_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Screen).where(models.Screen.id == screen_id))
    screen = result.scalars().first()
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screen not found"
        )

    result = await db.execute(select(models.Seat).where(models.Seat.screen_id == screen.id))
    seats = result.scalars().all()
    return seats

@router.post("/{screen_id}/seats", response_model=SeatResponse)
async def create_seat_of_screen(screen_id: uuid.UUID, seat: SeatCreate, db: Annotated[AsyncSession, Depends(get_db)], current_user = Depends(require_role("admin"))):
    result = await db.execute(select(models.Screen).options(selectinload(models.Screen.seats)).where(models.Screen.id == screen_id))
    screen = result.scalars().first()
    if not screen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screen not found"
        )

    seat_count = await db.scalar(select(func.count()).select_from(models.Seat).where(models.Seat.screen_id == screen_id)) or 0
    
    if seat_count >= screen.total_seats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum seats reached {seat_count} out of {screen.total_seats}"
        )
    
    new_seat = models.Seat(
        screen_id = screen_id,
        row_letter = seat.row_letter.upper(),
        seat_number = seat.seat_number,
        type = seat.type
    )

    db.add(new_seat)
    try: 
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat {seat.row_letter.upper()}{seat.seat_number} already exists in this screen"
        )
    await db.refresh(new_seat, attribute_names=["room"])
    return new_seat
