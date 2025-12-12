from datetime import datetime

import uuid
from sqlalchemy import Column, Text, Integer,Boolean, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .Base import Base
from app.modules.courses.enums import QuestionType


class Question(Base):
  __tablename__ = "questions"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

  # Связь с тестом
  test_id = Column(
    UUID(as_uuid=True),
    ForeignKey('tests.id', ondelete='CASCADE'),
    nullable=False,
    index=True
  )

  text = Column(Text, nullable=False)  # Текст вопроса
  question_type = Column(Enum(QuestionType), nullable=False)
  order_index = Column(Integer, nullable=False, default=0)
  score = Column(Integer, nullable=False, default=1)  # Баллы за вопрос

  delete_flg = Column(Boolean, nullable=False, default=False)
  created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
  update_at = Column(DateTime, nullable=False, default=datetime.utcnow)

  test = relationship("Test", back_populates="question")
  answer = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

  __table_args__ = (
    UniqueConstraint('test_id', 'order_index', name='uq_question_order_per_test'),
  )
