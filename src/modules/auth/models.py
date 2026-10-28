"""
SQLAlchemy ORM model cho bảng `users` — khớp với schema đã cập nhật
(thêm cột username, password để tự làm auth, không phụ thuộc Supabase Auth).

Đây là NƠI DUY NHẤT trong module auth được phép import SQLAlchemy Column
types — Service và Router không đụng tới file này trực tiếp.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Uuid, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base
if TYPE_CHECKING:
    from src.modules.catalog.models import Review
    from src.modules.ordering.models import Orders


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

    balance: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=0
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
        back_populates="user"
    )
    
    orders: Mapped[list["Orders"]] = relationship(back_populates="user")

  
