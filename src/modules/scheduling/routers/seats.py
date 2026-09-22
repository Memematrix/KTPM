from src.common.auth.role_guard import require_role
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.scheduling import models
from src.common.database import get_db

router = APIRouter()

@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(seat_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user = Depends(require_role("admin"))):
    result = await db.execute(select(models.Seat).where(models.Seat.id == seat_id))
    seat = result.scalars().first()
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found"
        )
    
    await db.delete(seat)
    await db.commit()
