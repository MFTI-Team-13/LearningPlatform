from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db.base import Base

if TYPE_CHECKING:
  from app.modules.users.models import User


class TokenPurpose(str, enum.Enum):
  VERIFY = "VERIFY"
  RESET = "RESET"


class RefreshToken(Base):
  __tablename__ = "refresh_tokens"

  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  user_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
  )
  token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
  fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
  user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
  replaced_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))

  user: Mapped[User] = relationship("User", back_populates="refresh_tokens")

  __table_args__ = (UniqueConstraint("user_id", "token_hash", name="uq_refreshtoken_user_token"),)
