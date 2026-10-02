from __future__ import annotations
from enum import StrEnum
from sqlalchemy import Uuid, Float
import uuid

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base
# from src.modules.auth.models import Review

class SeatType(StrEnum):
    standard = "standard"
    vip = "vip"
    sweetbox = "sweetbox"

class Movie(Base):
    __tablename__ = "movies"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text)
    duration: Mapped[int] = mapped_column(Integer)
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    poster_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # reviews: Mapped[list[Review]] = relationship(
    #     "Review",
    #     back_populates="movie",
    # )
    showtimes: Mapped[list[Showtime]] = relationship(
        back_populates="movie"
    )

class Screen(Base):
    __tablename__ = "screens"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)

    seats: Mapped[list[Seat]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan"
    )

    showtimes: Mapped[list[Showtime]] = relationship(
        back_populates="screen"
    )

class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint(
            "screen_id",
            "row_letter",
            "seat_number",
            name="unique_seat_row_seat"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    screen_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("screens.id"),
        index=True
    )
    row_letter: Mapped[str] = mapped_column(String, nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[SeatType] = mapped_column(
        Enum(SeatType, native_enum=False),
        default=SeatType.standard,
        nullable=False
    )

    room: Mapped[Screen] = relationship(
        back_populates= "seats"
    )

class Showtime(Base):
    __tablename__ = "showtimes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    movie_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("movies.id"),
        index=True
    )
    screen_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("screens.id"),
        index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    base_price: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    movie: Mapped[Movie] = relationship(
        back_populates="showtimes"
    )
    screen: Mapped[Screen] = relationship(
        back_populates="showtimes"
    )
    tickets: Mapped[list[Ticket]] = relationship(
        back_populates="showtime"
    )

class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    showtime_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("showtimes.id"),
        index=True,
        nullable=False
    )
    seat_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("seats.id"),
        index=True,
        nullable=False
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    showtime: Mapped[Showtime] = relationship(
        back_populates="tickets"
    )