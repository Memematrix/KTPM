from __future__ import annotations

import uuid
from datetime import UTC, datetime
import decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Numeric, Uuid, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base



class Food(Base):
    __tablename__ = "food"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    order_foods: Mapped[list[OrderFood]] = relationship(back_populates="food")


class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    order_foods: Mapped[list[OrderFood]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    tickets: Mapped[list[Ticket]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user: Mapped[User] = relationship(back_populates="orders")


class OrderFood(Base):
    __tablename__ = "order_food"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("food.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[Orders] = relationship(back_populates="order_foods")
    food: Mapped[Food] = relationship(back_populates="order_foods")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("showtime_id", "seat_id", name="tickets_showtime_seat_unique"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    showtime_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("showtimes.id"), index=True, nullable=False)
    seat_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("seats.id"), index=True, nullable=False)
    price: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", server_default="pending")

    order: Mapped[Orders] = relationship(back_populates="tickets")
    showtime: Mapped[Showtime] = relationship(back_populates="tickets")
