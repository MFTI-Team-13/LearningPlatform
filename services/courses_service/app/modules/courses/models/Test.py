from datetime import datetime

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .Base import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    lesson_id = Column(UUID(as_uuid=True),ForeignKey('lessons.id', ondelete='CASCADE'),nullable=False,unique=True)

    title = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)

    delete_flg = Column(Boolean, nullable=False, default=False)
    create_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    lesson = relationship("Lesson", back_populates="test", uselist=False)
    question = relationship("Question", back_populates="test", cascade="all, delete-orphan")
