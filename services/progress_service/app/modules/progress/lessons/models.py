from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db.base import Base
from app.core.config import settings

if TYPE_CHECKING:
  from app.modules.progress.courses.models import CourseProgress


class LessonProgress(Base):
  __tablename__ = "lesson_progress"
  __table_args__ = {"schema": settings.progress_schema}

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
  course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
  lesson_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
  lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Номер урока от 1 до 10

  # Связь с курсом
  course_progress_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey(f"{settings.progress_schema}.course_progress.id", ondelete="CASCADE"),
    nullable=False,
    index=True
  )

  # Статус и прогресс
  is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
  is_started: Mapped[bool] = mapped_column(Boolean, default=False)
  is_passed: Mapped[bool] = mapped_column(Boolean, default=False)
  progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)

  # Время и попытки
  time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
  attempts: Mapped[int] = mapped_column(Integer, default=0)
  started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

  # Оценки и результаты
  score: Mapped[float | None] = mapped_column(Float, nullable=True)
  max_score: Mapped[float] = mapped_column(Float, default=100.0)
  passing_score: Mapped[float] = mapped_column(Float, default=60.0)

  # Контент и ответы
  content_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
  answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
  feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
  user_notes: Mapped[str | None] = mapped_column(String, nullable=True)

  # Флаги
  needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
  is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)

  # Дополнительные данные
  metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

  # Связи
  course: Mapped[CourseProgress] = relationship(
    "CourseProgress",
    back_populates="lessons",
    lazy="selectin"
  )

  # Уникальный индекс
  __table_args__ = (
    {"schema": settings.progress_schema},
    {"unique": ["user_id", "course_id", "lesson_id"]},
  )

  def update_progress(self, progress: float) -> None:
    """Обновляет процент выполнения урока"""
    self.progress_percentage = max(0.0, min(100.0, progress))

    if self.progress_percentage >= 100 and not self.is_completed:
      self.is_completed = True
      self.completed_at = datetime.utcnow()
    elif self.progress_percentage > 0 and not self.is_started:
      self.is_started = True
      self.started_at = datetime.utcnow()

  def update_time_spent(self, seconds: int) -> None:
    """Добавляет время, проведенное на уроке"""
    self.time_spent_seconds += seconds
    self.last_accessed_at = datetime.utcnow()

  def submit_answer(self, answer_data: dict, score: float | None = None) -> None:
    """Отправляет ответ на урок"""
    self.answers = answer_data
    self.attempts += 1
    self.last_accessed_at = datetime.utcnow()

    if score is not None:
      self.score = score
      self.is_passed = score >= self.passing_score

  def toggle_bookmark(self) -> bool:
    """Переключает статус закладки"""
    self.is_bookmarked = not self.is_bookmarked
    return self.is_bookmarked
