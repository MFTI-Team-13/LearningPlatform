from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, validator


class CourseProgressStatus(str, Enum):
  NOT_STARTED = "not_started"
  IN_PROGRESS = "in_progress"
  COMPLETED = "completed"
  PAUSED = "paused"
  ARCHIVED = "archived"


class CourseProgressBase(BaseModel):
  user_id: int = Field(..., description="ID пользователя")
  course_id: int = Field(..., description="ID курса")

  progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
  status: CourseProgressStatus = Field(default=CourseProgressStatus.NOT_STARTED)

  completed_lessons: int = Field(default=0, ge=0)
  total_lessons: int = Field(default=10, ge=1)

  time_spent_seconds: int = Field(default=0, ge=0)

  total_score: float = Field(default=0.0, ge=0.0)
  average_score: Optional[float] = Field(None, ge=0.0, le=100.0)
  user_rating: Optional[int] = Field(None, ge=1, le=5)
  user_feedback: Optional[str] = Field(None, max_length=1000)

  is_favorite: bool = Field(default=False)
  is_bookmarked: bool = Field(default=False)
  notifications_enabled: bool = Field(default=True)

  metadata: Optional[dict[str, Any]] = Field(None)


class CourseProgressCreate(CourseProgressBase):
  pass


class CourseProgressUpdate(BaseModel):
  progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
  status: Optional[CourseProgressStatus] = None

  completed_lessons: Optional[int] = Field(None, ge=0)
  time_spent_seconds: Optional[int] = Field(None, ge=0)

  total_score: Optional[float] = Field(None, ge=0.0)
  average_score: Optional[float] = Field(None, ge=0.0, le=100.0)
  user_rating: Optional[int] = Field(None, ge=1, le=5)
  user_feedback: Optional[str] = Field(None, max_length=1000)

  is_favorite: Optional[bool] = None
  is_bookmarked: Optional[bool] = None
  notifications_enabled: Optional[bool] = None

  metadata: Optional[dict[str, Any]] = None


class CourseProgressResponse(CourseProgressBase):
  id: int
  last_accessed_at: Optional[datetime] = None
  started_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None
  created_at: datetime
  updated_at: datetime

  model_config = ConfigDict(from_attributes=True)


class CourseStats(BaseModel):
  course_id: int
  total_users: int = Field(default=0)
  active_users: int = Field(default=0)
  completed_users: int = Field(default=0)

  avg_progress: float = Field(default=0.0, ge=0.0, le=100.0)
  avg_score: Optional[float] = Field(None, ge=0.0, le=100.0)
  avg_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
  avg_time_spent: int = Field(default=0)

  completion_rate: float = Field(default=0.0, ge=0.0, le=100.0)

  status_distribution: dict[str, int] = Field(default_factory=dict)
  lesson_completion: list[dict[str, Any]] = Field(default_factory=list)


class UserCoursesSummary(BaseModel):
  user_id: int
  total_courses: int = Field(default=0)
  in_progress_courses: int = Field(default=0)
  completed_courses: int = Field(default=0)
  archived_courses: int = Field(default=0)

  total_time_spent: int = Field(default=0)
  average_progress: float = Field(default=0.0)

  favorite_courses: list[int] = Field(default_factory=list)
  last_activity: Optional[datetime] = None
  recent_courses: list[dict[str, Any]] = Field(default_factory=list)


class PaginatedCourseProgress(BaseModel):
  items: list[CourseProgressResponse]
  total: int
  page: int
  size: int
  pages: int


class BulkCourseProgressUpdate(BaseModel):
  course_id: int
  data: CourseProgressUpdate


class BulkCourseProgressResponse(BaseModel):
  successful: list[int]
  failed: list[dict[str, Any]]
