import enum
import uuid
from datetime import datetime

from app.common.db.base import Base
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class TokenPurpose(str, enum.Enum):
  VERIFY = "VERIFY"
  RESET = "RESET"


class RefreshToken(Base):
  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
  token_hash: Mapped[str] = mapped_column(String(255))
  fingerprint: Mapped[str | None]
  user_agent: Mapped[str | None]
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
  replaced_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))

  __table_args__ = (UniqueConstraint("user_id", "token_hash", name="uq_refreshtoken_user_token"),)
