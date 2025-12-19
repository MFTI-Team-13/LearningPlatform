import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EnrollmentStatus(str, Enum):
  enrolled = "enrolled"
  active = "active"
  completed = "completed"
  cancelled = "cancelled"


class EnrollmentCreate(BaseModel):
  user_id: uuid.UUID
  course_id: uuid.UUID


class EnrollmentOut(BaseModel):
  id: uuid.UUID
  user_id: uuid.UUID
  course_id: uuid.UUID
  status: EnrollmentStatus
  progress: int
  enrolled_at: datetime
  completed_at: datetime | None = None
