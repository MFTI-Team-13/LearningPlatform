from typing import Optional,List
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from uuid import UUID

from app.modules.courses.enums import CourseLevel
from app.modules.courses.schemas.LessonScheme import LessonResponse


class CourseBase(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  title: str = Field(..., min_length=5, max_length=200, description="Название курса")
  description: Optional[str] = Field(None, max_length=1000, description="Описание курса")
  level: CourseLevel = Field(default=CourseLevel.BEGINNER, description="Уровень сложности")
  is_published: bool = Field(default=False, description="Публичность курса")

  @field_validator('title')
  @classmethod
  def validate_title(cls, v: str) -> str:
    if not v or v.isspace():
      raise ValueError('Название курса не может быть пустым')
    if len(v.strip()) < 5:
      raise ValueError('Название курса должно содержать минимум 5 символов')
    return v.strip()

  @field_validator('level')
  @classmethod
  def validate_level(cls, v: CourseLevel) -> CourseLevel:
    if not isinstance(v, CourseLevel):
      raise ValueError('Некорректный уровень курса')
    return v


class CourseCreate(CourseBase):
  pass


class CourseUpdate(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  title: Optional[str] = Field(None, min_length=5, max_length=200)
  description: Optional[str] = Field(None, max_length=1000)
  level: Optional[CourseLevel] = None
  is_published: Optional[bool] = None

  @model_validator(mode='after')
  def validate_at_least_one_field(self):
    if not any([self.title, self.description, self.level, self.is_published is not None]):
      raise ValueError('Для обновления необходимо указать хотя бы одно поле')
    return self


class CourseResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  title: str
  description: Optional[str]
  level: CourseLevel
  author_id: UUID
  is_published: bool
  delete_flg: bool
  create_at: datetime
  update_at: datetime

class CourseWithLessonsResponse(CourseResponse):
  lessons: List['LessonResponse'] = Field(default_factory=list, description="Уроки")
