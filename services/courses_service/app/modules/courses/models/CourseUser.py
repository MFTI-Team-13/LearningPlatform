import uuid
from datetime import datetime


from sqlalchemy import Column,DateTime,Boolean,ForeignKey,UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .Base import Base

class CourseUser(Base):
  __tablename__ = "course_students"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
  user_id = Column(UUID(as_uuid=True), nullable=False)
  is_active = Column(Boolean, nullable=False, default = True)

  create_at = Column(DateTime, nullable=False, default=datetime.utcnow)
  update_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

  courses = relationship("Course", back_populates="courseUser")

  __table_args__ = (
    UniqueConstraint('course_id', 'user_id', name='uq_course_user_rel'),
  )

