"""
SQLAlchemy ORM model cho bảng `users` — khớp với schema đã cập nhật
(thêm cột username, password để tự làm auth, không phụ thuộc Supabase Auth).

Đây là NƠI DUY NHẤT trong module auth được phép import SQLAlchemy Column
types — Service và Router không đụng tới file này trực tiếp.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime

from src.common.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, default="customer")  # 'admin' | 'customer'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)