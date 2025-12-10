from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class TestBase(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  title: str = Field(..., min_length=3, max_length=255, description="Название теста")
  description: Optional[str] = Field(None, description="Описание теста")
  is_active: bool = Field(default=True, description="Активен ли тест")

  @field_validator('title')
  @classmethod
  def validate_title(cls, v: str) -> str:
    if not v or v.isspace():
      raise ValueError('Название теста не может быть пустым')
    return v.strip()


class TestCreate(TestBase):
  lesson_id: UUID = Field(..., description="ID урока")


class TestUpdate(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  title: Optional[str] = Field(None, min_length=3, max_length=255)
  description: Optional[str] = None
  is_active: Optional[bool] = None

  @model_validator(mode='after')
  def validate_not_all_null(self):
    if all([
      self.title is None,
      self.description is None,
      self.is_active is None
    ]):
      raise ValueError('Для обновления теста необходимо указать хотя бы одно поле')
    return self


class TestResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  title: str
  description: Optional[str]
  is_active: bool
  delete_flg:bool
  created_at: datetime
  update_at: datetime
  lesson_id: UUID
