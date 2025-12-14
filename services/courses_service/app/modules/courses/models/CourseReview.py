import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .Base import Base


class CourseReview(Base):
    __tablename__ = "course_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    course_id = Column(UUID(as_uuid=True),ForeignKey('courses.id', ondelete='CASCADE'),nullable=False)
    user_id = Column(UUID(as_uuid=True),nullable=False)

    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    is_published = Column(Boolean, nullable=False, default=True)
    delete_flg = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint('course_id', 'user_id', name='uq_review_course_user'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
