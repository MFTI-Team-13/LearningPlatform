import uuid
from enum import Enum as PyEnum

from app.common.db.base import Base
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class RoleEnum(str, PyEnum):
  student = "student"
  teacher = "teacher"
  admin = "admin"


class User(Base):
  __tablename__ = "users"

  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class UserProfile(Base):
  __tablename__ = "user_profiles"

  id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
