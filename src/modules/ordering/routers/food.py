from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.auth.role_guard import require_role
from src.common.database import get_db
from src.modules.ordering import models
from src.modules.ordering.schemas import FoodCreate, FoodResponse

router = APIRouter()


@router.get("", response_model=list[FoodResponse])
async def get_food(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Food).order_by(models.Food.name))
    return result.scalars().all()


@router.post("", response_model=FoodResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin"))],)
async def create_food(food: FoodCreate, db: Annotated[AsyncSession, Depends(get_db)],):
    new_food = models.Food(**food.model_dump())
    db.add(new_food)
    await db.commit()
    await db.refresh(new_food)
    return new_food


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))],)
async def delete_food(food_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Food).where(models.Food.id == food_id))
    food = result.scalar_one_or_none()
    if food is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found",
        )

    await db.delete(food)
    await db.commit()