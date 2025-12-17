from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class LessonProgressBase(BaseModel):
  user_id: int = Field(..., description="ID пользователя")
  course_id: int = Field(..., description="ID курса")
  lesson_id: int = Field(..., description="ID урока")
  lesson_number: int = Field(..., ge=1, le=10, description="Номер урока (1-10)")

  # Статус и прогресс
  is_completed: bool = Field(default=False)
  is_started: bool = Field(default=False)
  is_passed: bool = Field(default=False)
  progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

  # Время и попытки
  time_spent_seconds: int = Field(default=0, ge=0)
  attempts: int = Field(default=0, ge=0)

  # Оценки и результаты
  score: Optional[float] = Field(None, ge=0.0)
  max_score: float = Field(default=100.0, ge=0.0)
  passing_score: float = Field(default=60.0, ge=0.0)

  # Контент и ответы
  content_progress: Optional[dict[str, Any]] = Field(None)
  answers: Optional[dict[str, Any]] = Field(None)
  feedback: Optional[dict[str, Any]] = Field(None)
  user_notes: Optional[str] = Field(None, max_length=2000)

  # Флаги
  needs_review: bool = Field(default=False)
  is_bookmarked: bool = Field(default=False)

  # Дополнительные данные
  metadata: Optional[dict[str, Any]] = Field(None)


class LessonProgressCreate(LessonProgressBase):
  course_progress_id: Optional[int] = Field(None, description="ID прогресса курса")


class LessonProgressUpdate(BaseModel):
  is_completed: Optional[bool] = None
  is_started: Optional[bool] = None
  is_passed: Optional[bool] = None
  progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)

  time_spent_seconds: Optional[int] = Field(None, ge=0)
  attempts: Optional[int] = Field(None, ge=0)

  score: Optional[float] = Field(None, ge=0.0)
  max_score: Optional[float] = Field(None, ge=0.0)
  passing_score: Optional[float] = Field(None, ge=0.0)

  content_progress: Optional[dict[str, Any]] = None
  answers: Optional[dict[str, Any]] = None
  feedback: Optional[dict[str, Any]] = None
  user_notes: Optional[str] = Field(None, max_length=2000)

  needs_review: Optional[bool] = None
  is_bookmarked: Optional[bool] = None

  metadata: Optional[dict[str, Any]] = None


class LessonProgressResponse(LessonProgressBase):
  id: int
  course_progress_id: int
  started_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None
  last_accessed_at: Optional[datetime] = None
  created_at: datetime
  updated_at: datetime

  model_config = ConfigDict(from_attributes=True)


class LessonStats(BaseModel):
  lesson_id: int
  lesson_number: int
  total_users: int = Field(default=0)
  started_users: int = Field(default=0)
  completed_users: int = Field(default=0)
  passed_users: int = Field(default=0)

  avg_progress: float = Field(default=0.0, ge=0.0, le=100.0)
  avg_score: Optional[float] = Field(None)
  avg_time_spent: int = Field(default=0)
  avg_attempts: float = Field(default=0.0)

  completion_rate: float = Field(default=0.0, ge=0.0, le=100.0)
  pass_rate: float = Field(default=0.0, ge=0.0, le=100.0)

  difficulty_index: Optional[float] = Field(None, ge=0.0, le=1.0)
  common_mistakes: list[dict[str, Any]] = Field(default_factory=list)


class UserLessonsSummary(BaseModel):
  user_id: int
  total_lessons: int = Field(default=0)
  started_lessons: int = Field(default=0)
  completed_lessons: int = Field(default=0)
  passed_lessons: int = Field(default=0)

  total_time_spent: int = Field(default=0)
  average_progress: float = Field(default=0.0)
  average_score: Optional[float] = Field(None)
  total_attempts: int = Field(default=0)

  last_activity: Optional[datetime] = None
  current_lesson: Optional[dict[str, Any]] = None
  recent_lessons: list[dict[str, Any]] = Field(default_factory=list)


class PaginatedLessonProgress(BaseModel):
  items: list[LessonProgressResponse]
  total: int
  page: int
  size: int
  pages: int


class LessonAnswerSubmit(BaseModel):
  answers: dict[str, Any] = Field(..., description="Ответы пользователя")
  time_spent: Optional[int] = Field(None, ge=0, description="Время, потраченное на урок (сек)")


class LessonContentProgress(BaseModel):
  section_id: str = Field(..., description="ID раздела")
  progress: float = Field(..., ge=0.0, le=100.0, description="Прогресс по разделу")
  completed: bool = Field(default=False, description="Раздел завершен")
