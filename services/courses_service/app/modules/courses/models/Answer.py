import uuid
from datetime import datetime

from sqlalchemy import Column, Text, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .Base import Base


class Answer(Base):
  __tablename__ = "answers"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

  question_id = Column(UUID(as_uuid=True),ForeignKey('questions.id', ondelete='CASCADE'),nullable=False,index=True)

  text = Column(Text, nullable=False)
  is_correct = Column(Boolean, nullable=False, default=False)
  order_index = Column(Integer, nullable=False, default=0)

  delete_flg = Column(Boolean, nullable=False, default=False)
  created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
  update_at = Column(DateTime, nullable=False, default=datetime.utcnow)

  question = relationship("Question", back_populates="answer")

  __table_args__ = (
    UniqueConstraint('question_id', 'order_index', name='uq_answer_order_per_question'),
  )
