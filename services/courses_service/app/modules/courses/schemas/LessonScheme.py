from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.modules.courses.enums import ContentType


class LessonBase(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  title: str = Field(..., min_length=3, max_length=255, description="Название урока")
  short_description: Optional[str] = Field(None, max_length=500, description="Краткое описание")
  content_type: ContentType = Field(default=ContentType.TEXT, description="Тип контента")
  order_index: int = Field(..., ge=0, le=1000, description="Порядковый номер")
  text_content: Optional[str] = Field(None, description="Текстовый контент")
  content_url: Optional[str] = Field(None, max_length=500, description="URL видео")

  @field_validator('title')
  @classmethod
  def validate_title(cls, v: str) -> str:
    if not v or v.isspace():
      raise ValueError('Название урока не может быть пустым')
    return v.strip()

  @field_validator('content_type')
  @classmethod
  def validate_content_type(cls, v: ContentType) -> ContentType:
    if not isinstance(v, ContentType):
      raise ValueError('Некорректный тип контента')
    return v

  @field_validator('content_url')
  @classmethod
  def validate_video_url(cls, v: Optional[str], info) -> Optional[str]:
    if v and info.data.get('content_type') == ContentType.VIDEO:
      if not v.startswith(('http://', 'https://')):
        raise ValueError('URL видео должен начинаться с http:// или https://')
      if len(v) > 500:
        raise ValueError('URL видео не может превышать 500 символов')
    return v

  @model_validator(mode='after')
  def validate_content_consistency(self):
    if self.content_type == ContentType.TEXT and not self.text_content:
      raise ValueError('Для текстового урока необходимо указать текстовый контент')
    if self.content_type == ContentType.VIDEO and not self.content_url:
      raise ValueError('Для видеоурока необходимо указать URL видео')
    return self


class LessonCreate(LessonBase):
  course_id: UUID = Field(..., description="ID курса")


class LessonUpdate(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  title: Optional[str] = Field(None, min_length=3, max_length=255)
  short_description: Optional[str] = Field(None, max_length=500)
  content_type: Optional[ContentType] = None
  order_index: Optional[int] = Field(None, ge=0, le=1000)
  text_content: Optional[str] = None
  content_url: Optional[str] = Field(None, max_length=500)

  @model_validator(mode='after')
  def validate_at_least_one_field(self):

    if not any([
      self.title is not None,
      self.short_description is not None,
      self.content_type is not None,
      self.order_index is not None,
      self.text_content is not None,
      self.content_url is not None
    ]):
      raise ValueError('Для обновления урока необходимо указать хотя бы одно поле')
    return self

  @model_validator(mode='after')
  def validate_content_consistency(self):
    if self.content_type == ContentType.TEXT and not self.text_content:
      raise ValueError('Для текстового урока необходимо указать текстовый контент')
    if self.content_type == ContentType.VIDEO and not self.content_url:
      raise ValueError('Для видеоурока необходимо указать URL видео')
    return self

  @field_validator('content_url')
  @classmethod
  def validate_video_url(cls, v: Optional[str], info) -> Optional[str]:
    if v and info.data.get('content_type') == ContentType.VIDEO:
      if not v.startswith(('http://', 'https://')):
        raise ValueError('URL видео должен начинаться с http:// или https://')
      if len(v) > 500:
        raise ValueError('URL видео не может превышать 500 символов')
    return v

class LessonResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  title: str
  short_description: Optional[str]
  content_type: ContentType
  order_index: int
  text_content: Optional[str]
  content_url: Optional[str]
  course_id: UUID
  delete_flg: bool
  created_at: datetime
  updated_at: datetime

