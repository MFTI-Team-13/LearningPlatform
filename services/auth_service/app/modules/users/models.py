import uuid
from datetime import datetime, UTC
from typing import Optional, List

from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.common.db.base import Base


class RoleEnum(str, PyEnum):
  student = "student"
  teacher = "teacher"
  admin = "admin"


class User(Base):
  __tablename__ = "users"

  id: Mapped[uuid.UUID] = mapped_column(
    PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
  )
  email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
  password_hash: Mapped[str] = mapped_column(String(255))
  full_name: Mapped[str] = mapped_column(String(255))
  is_active: Mapped[bool] = mapped_column(Boolean, default=True)
  is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

  role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum, name="role_enum"), default=RoleEnum.student)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(UTC)
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=lambda: datetime.now(UTC),
    onupdate=lambda: datetime.now(UTC)
  )

  profile: Mapped[Optional["UserProfile"]] = relationship(
    "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
  )

  courses: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="user")  # type: ignore[name-defined]


class UserProfile(Base):
  __tablename__ = "user_profiles"

  id: Mapped[uuid.UUID] = mapped_column(
    PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
  )
  user_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
  )
  bio: Mapped[str] = mapped_column(String(500), default="")
  avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
  specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

  user: Mapped["User"] = relationship("User", back_populates="profile")
