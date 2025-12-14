from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CourseReviewBase(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  rating: int = Field(..., ge=1, le=5, description="Рейтинг от 1 до 5")
  comment: str | None = Field(None, max_length=2000, description="Комментарий")
  is_published: bool = Field(default=True, description="Опубликован ли отзыв")

  @field_validator('rating')
  @classmethod
  def validate_rating(cls, v: int) -> int:
    if v not in [1, 2, 3, 4, 5]:
      raise ValueError('Рейтинг должен быть целым числом от 1 до 5')
    return v

  @field_validator('comment')
  @classmethod
  def validate_comment(cls, v: str | None) -> str | None:
    if v and len(v.strip()) < 10:
      raise ValueError('Комментарий должен содержать минимум 10 символов')
    return v

  @model_validator(mode='after')
  def validate_comment_for_low_rating(self):
    if self.rating <= 2 and not self.comment:
      raise ValueError('Для низкого рейтинга (1-2 звезды) необходимо указать комментарий')
    return self


class CourseReviewCreate(CourseReviewBase):
  course_id: UUID = Field(..., description="ID курса")
  user_id: UUID = Field(..., description="ID пользователя")


class CourseReviewUpdate(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  rating: int | None = Field(None, ge=1, le=5)
  comment: str | None = Field(None, max_length=2000)

  @model_validator(mode='after')
  def validate_not_all_null(self):
    if all([
      self.rating is None,
      self.comment is None
    ]):
      raise ValueError('Для обновления отзыва необходимо указать хотя бы одно поле')
    return self


class CourseReviewResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  rating: int
  comment: str | None
  is_published: bool
  course_id: UUID
  user_id: UUID
  delete_flg: bool
  created_at: datetime
  updated_at: datetime


class CourseReviewWithCourse(CourseReviewResponse):
  course: 'CourseResponse'
