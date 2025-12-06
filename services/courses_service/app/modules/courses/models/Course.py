import uuid
from datetime import datetime


from sqlalchemy import Enum, DateTime, Column,String,Text,ForeignKey,Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .Base import Base
from app.modules.courses.enums import CourseLevel


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, unique=True)
    description = Column(Text)
    level = Column(Enum(CourseLevel), default=CourseLevel.BEGINNER)
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    delete_flg = Column(Boolean, nullable=False, default=False)
    is_published = Column(Boolean, nullable=False, default=False)
    create_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="course")
    lesson = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    reviews = relationship("CourseReview", back_populates="course", cascade="all, delete-orphan")
