from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db.base import Base

if TYPE_CHECKING:
  from app.modules.users.models import User


class Role(Base):
  __tablename__ = "roles"

  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
  name: Mapped[str] = mapped_column(String(100), nullable=False)
  description: Mapped[str | None] = mapped_column(String(255))
  is_system: Mapped[bool] = mapped_column(
    Boolean, nullable=False, default=False, server_default=text("false")
  )
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
  )

  users: Mapped[list[User]] = relationship("User", back_populates="role")

  def __repr__(self) -> str:
    return f"Role(id={self.id}, slug={self.slug!r})"
