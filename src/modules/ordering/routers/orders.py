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
from src.modules.ordering import models as order_models
from src.modules.scheduling import models as scheduling_models
from src.modules.ordering.schemas import OrderCreate, OrderResponse

router = APIRouter()



@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser = Depends(get_current_user),):
    
    # KIỂM TRA
    if len(set(payload.seat_ids)) != len(payload.seat_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate seat_ids")
    if len({item.food_id for item in payload.items}) != len(payload.items):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate food_id")

    showtime = (
        await db.execute(
            select(scheduling_models.Showtime)
            .where(scheduling_models.Showtime.id == payload.showtime_id)
            )
        ).scalars().first()
    if not showtime:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found") 
    
       
    seats = (
        await db.execute(
            select(scheduling_models.Seat)
            .where(scheduling_models.Seat.id.in_(payload.seat_ids), scheduling_models.Seat.screen_id == showtime.screen_id, )
        )
    ).scalars().all()
    if len(seats) != len(payload.seat_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more seats do not belong to this showtime's screen")
    
    
    booked_seat = (
        await db.execute(
            select(scheduling_models.Ticket)
            .where(scheduling_models.Ticket.showtime_id == payload.showtime_id, scheduling_models.Ticket.seat_id.in_(payload.seat_ids), scheduling_models.Ticket.status.in_(["confirmed", "pending"]))
        )
    ).scalars().first()
    if booked_seat:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail="One or more seats are booked")
    
    
    if payload.items:
        list_food_id = [item.food_id for item in payload.items]
        foods = (
            await db.execute(
                select(order_models.Food)
                .where(order_models.Food.id.in_(list_food_id))
            )  
        ).scalars().all()
        foods_dict = {food.id: food for food in foods}
        
        if len(foods) != len(list_food_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more food items not found")


    # TÍNH TOÁN
    ticket_price = Decimal(str(showtime.base_price))
    total_tickets_amount = Decimal(str(showtime.base_price)) * len(seats)

    total_foods_amount = sum(
        (foods_dict[item.food_id].price * item.quantity for item in payload.items), 
        Decimal("0")
    )
    
    final_total_amount = total_tickets_amount + total_foods_amount

    new_order = order_models.Orders(
        user_id=current_user.id, 
        total_amount=final_total_amount, 
    )

    new_order.tickets = [
        scheduling_models.Ticket(
            showtime_id=payload.showtime_id, 
            seat_id=seat.id, 
            price=ticket_price
        )
        for seat in seats
    ]

    new_order.order_foods = [
        order_models.OrderFood(
            food_id=item.food_id, 
            quantity=item.quantity, 
            price=foods_dict[item.food_id].price
        )
        for item in payload.items
    ]
    
    db.add(new_order)


    # TRẢ KẾT QUẢ
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="One or more seats were booked during processing")
    
    
    return (
        await db.execute(
            select(order_models.Orders)
            .options(
                selectinload(order_models.Orders.order_foods).selectinload(order_models.OrderFood.food), 
                selectinload(order_models.Orders.tickets)
            )
            .where(order_models.Orders.id == new_order.id)
        )
    ).scalars().first()


@router.get("", response_model=list[OrderResponse])
async def get_orders(db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser = Depends(get_current_user),):
    query = (
        select(order_models.Orders)
        .options(
            selectinload(order_models.Orders.order_foods).selectinload(order_models.OrderFood.food),
            selectinload(order_models.Orders.tickets),
        )
        .order_by(order_models.Orders.created_at.desc())
    )
    if current_user.role != "admin":
        query = query.where(order_models.Orders.user_id == current_user.id)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser = Depends(get_current_user),
):
    query = (
        select(order_models.Orders)
        .options(
            selectinload(order_models.Orders.order_foods).selectinload(order_models.OrderFood.food),
            selectinload(order_models.Orders.tickets),
        )
        .where(order_models.Orders.id == order_id)
    )
    if current_user.role != "admin":
        query = query.where(order_models.Orders.user_id == current_user.id)

    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user: CurrentUser = Depends(get_current_user),):
    query = select(order_models.Orders).where(order_models.Orders.id == order_id)
    if current_user.role != "admin":
        query = query.where(order_models.Orders.user_id == current_user.id)

    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    await db.delete(order)
    await db.commit()