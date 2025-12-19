from enum import Enum as PyEnum

from app.common.db.base import Base


class EnrollmentStatus(str, PyEnum):
  enrolled = "enrolled"
  active = "active"
  completed = "completed"
  cancelled = "cancelled"


class Enrollment(Base):
  __tablename__ = "enrollments"
