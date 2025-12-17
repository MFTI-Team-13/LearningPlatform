from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.db.base import Base
from app.core.config import settings

if TYPE_CHECKING:
  from app.modules.progress.lessons.models import LessonProgress


class CourseProgressStatus(str, PyEnum):
  NOT_STARTED = "not_started"
  IN_PROGRESS = "in_progress"
  COMPLETED = "completed"
  PAUSED = "paused"
  ARCHIVED = "archived"


class CourseProgress(Base):
  __tablename__ = "course_progress"
  __table_args__ = {"schema": settings.progress_schema}

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
  course_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

  # Прогресс и статус
  progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
  status: Mapped[str] = mapped_column(
    Enum(CourseProgressStatus, name="course_progress_status"),
    default=CourseProgressStatus.NOT_STARTED
  )

  # Статистика по урокам
  completed_lessons: Mapped[int] = mapped_column(Integer, default=0)
  total_lessons: Mapped[int] = mapped_column(Integer, default=settings.max_lessons_per_course)

  # Время и даты
  time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
  last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

  # Оценки и рейтинги
  total_score: Mapped[float] = mapped_column(Float, default=0.0)
  average_score: Mapped[float | None] = mapped_column(Float, nullable=True)
  user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
  user_feedback: Mapped[str | None] = mapped_column(String, nullable=True)

  # Флаги
  is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
  is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
  notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

  # Дополнительные данные
  metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

  # Связи
  lessons: Mapped[list[LessonProgress]] = relationship(
    "LessonProgress",
    back_populates="course",
    cascade="all, delete-orphan",
    lazy="selectin"
  )

  # Уникальный индекс
  __table_args__ = (
    {"schema": settings.progress_schema},
    {"unique": ["user_id", "course_id"]},
  )

  def update_progress(self) -> None:
    """Обновляет процент выполнения на основе завершенных уроков"""
    if self.total_lessons > 0:
      self.progress_percentage = (self.completed_lessons / self.total_lessons) * 100

      # Обновляем статус
      if self.progress_percentage >= 100:
        self.status = CourseProgressStatus.COMPLETED
        if not self.completed_at:
          self.completed_at = datetime.utcnow()
      elif self.progress_percentage > 0 and self.status == CourseProgressStatus.NOT_STARTED:
        self.status = CourseProgressStatus.IN_PROGRESS
        if not self.started_at:
          self.started_at = datetime.utcnow()

  def update_time_spent(self, seconds: int) -> None:
    """Добавляет время, проведенное на курсе"""
    self.time_spent_seconds += seconds
    self.last_accessed_at = datetime.utcnow()

  def toggle_favorite(self) -> bool:
    """Переключает статус избранного"""
    self.is_favorite = not self.is_favorite
    return self.is_favorite

  def archive(self) -> None:
    """Архивирует курс"""
    self.status = CourseProgressStatus.ARCHIVED
