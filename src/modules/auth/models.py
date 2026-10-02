"""
SQLAlchemy ORM model cho bảng `users` — khớp với schema đã cập nhật
(thêm cột username, password để tự làm auth, không phụ thuộc Supabase Auth).

Đây là NƠI DUY NHẤT trong module auth được phép import SQLAlchemy Column
types — Service và Router không đụng tới file này trực tiếp.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from src.modules.scheduling.models import Movie
from src.common.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="customer",
    )  # 'admin' | 'customer'

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    reviews: Mapped[list[Review]] = relationship(
        "Review",
        back_populates="user"
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    movie_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="reviews",
    )

    # movie: Mapped[Movie] = relationship(
    #     "Movie",
    #     back_populates="reviews",
    # )