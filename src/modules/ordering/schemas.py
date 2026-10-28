from decimal import Decimal
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FoodBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(ge=Decimal("0.0"))
    image_url: str | None = None


class FoodCreate(FoodBase):
    pass


class FoodResponse(FoodBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class OrderFoodCreate(BaseModel):
    food_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class OrderFoodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    food_id: uuid.UUID
    quantity: int
    price: Decimal
    food: FoodResponse | None = None


class OrderBase(BaseModel):
    status: str = Field(default="pending")


class OrderCreate(BaseModel):
    showtime_id: uuid.UUID
    seat_ids: list[uuid.UUID] = Field(min_length=1)
    items: list[OrderFoodCreate] = Field(default_factory=list)


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    total_amount: Decimal
    created_at: datetime

    order_foods: list[OrderFoodResponse] = []
    tickets: list["TicketResponse"] = []


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    showtime_id: uuid.UUID
    seat_id: uuid.UUID
    price: Decimal
    status: str
