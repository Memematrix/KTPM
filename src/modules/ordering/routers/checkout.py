from src.common.auth.role_guard import require_role
from decimal import Decimal
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.common.auth.middleware import CurrentUser, get_current_user
from src.common.database import get_db
from src.modules.ordering import models as orderModel
from src.modules.auth import models as userModel
from src.modules.ordering.schemas import OrderCreate, OrderResponse

router = APIRouter()

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(order_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser = Depends(get_current_user), guard = Depends(require_role("admin", "customer"))):
    result = await db.execute(select(orderModel.Orders).where(orderModel.Orders.id == order_id).options(selectinload(orderModel.Orders.tickets), selectinload(orderModel.Orders.order_foods)))
    order = result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.status != "pending":
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail=f"Order cannot be checked out (current status: {order.status})"
    )


    result = await db.execute(select(userModel.User).where(userModel.User.id == current_user.id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="You cannot checkout an order that does not belong to you"
    )

    if user.balance < order.total_amount:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient balance")

    user.balance = float(user.balance) - float(order.total_amount)
    order.status = "completed"
    for ticket in order.tickets:
        ticket.status = "confirmed"


    await db.commit()
    await db.refresh(order)

    return order
