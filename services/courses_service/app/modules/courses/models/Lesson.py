from datetime import datetime

import uuid
from sqlalchemy import Column, String, Text, Integer,Boolean, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .Base import Base
from app.modules.courses.enums import ContentType


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    course_id = Column(UUID(as_uuid=True),ForeignKey('courses.id', ondelete='CASCADE'),nullable=False)

    title = Column(String, nullable=False)
    short_description = Column(String)
    content_type = Column(Enum(ContentType),nullable=False,default=ContentType.TEXT)

    text_content = Column(Text)
    content_url = Column(String)

    order_index = Column(Integer, nullable=False, default=0)
    delete_flg = Column(Boolean, nullable=False, default=False)

    create_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_at = Column(DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="lesson")
    test = relationship("Test", back_populates="lesson", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('course_id', 'order_index', name='uq_lesson_order_per_course'),
    )

