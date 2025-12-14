import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.modules.courses.enums import CourseLevel

from .Base import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, unique=True)
    description = Column(Text)
    level = Column(Enum(CourseLevel), default=CourseLevel.BEGINNER)
    author_id = Column(UUID(as_uuid=True), nullable=False)
    is_published = Column(Boolean, nullable=False, default=False)

    delete_flg = Column(Boolean, nullable=False, default=False)
    create_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    courseUser = relationship("CourseUser", back_populates="courses", cascade="all, delete-orphan")
    lesson = relationship("Lesson", back_populates="course",lazy="selectin", cascade="all, delete-orphan")
    reviews = relationship("CourseReview", back_populates="course", cascade="all, delete-orphan")
