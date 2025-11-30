from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db.base import Base

if TYPE_CHECKING:
  from app.modules.auth.models import RefreshToken


class RoleEnum(str, PyEnum):
  student = "student"
  teacher = "teacher"
  admin = "admin"


class User(Base):
  __tablename__ = "users"

  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
  email: Mapped[str | None] = mapped_column(String(255), nullable=True)
  hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
  role: Mapped[RoleEnum] = mapped_column(
    Enum(RoleEnum, name="user_role_enum"), nullable=False, default=RoleEnum.student
  )
  is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
  )

  profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="user", uselist=False)
  refresh_tokens: Mapped[list[RefreshToken]] = relationship("RefreshToken", back_populates="user")

  def __repr__(self) -> str:
    return f"User(id={self.id}, username={self.username!r}, role={self.role})"


class UserProfile(Base):
  __tablename__ = "user_profiles"

  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  user_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
  )
  first_name: Mapped[str] = mapped_column(String(100), nullable=False)
  last_name: Mapped[str] = mapped_column(String(100), nullable=False)
  middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
  )

  user: Mapped[User] = relationship("User", back_populates="profile")
