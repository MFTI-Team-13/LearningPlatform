from typing import Optional,List
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.modules.courses.enums import QuestionType


class QuestionBase(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  text: str = Field(..., min_length=5, max_length=2000, description="Текст вопроса")
  question_type: QuestionType = Field(..., description="Тип вопроса")
  order_index: int = Field(..., ge=0, le=100, description="Порядковый номер")
  score: int = Field(..., ge=1, le=100, description="Баллы за вопрос")

  @field_validator('text')
  @classmethod
  def validate_text(cls, v: str) -> str:
    if not v or v.isspace():
      raise ValueError('Текст вопроса не может быть пустым')
    if len(v.strip()) < 10:
      raise ValueError('Текст вопроса должен содержать минимум 10 символов')
    return v.strip()

  @field_validator('question_type')
  @classmethod
  def validate_question_type(cls, v: QuestionType) -> QuestionType:
    if not isinstance(v, QuestionType):
      raise ValueError('Некорректный тип вопроса')
    return v

  @field_validator('score')
  @classmethod
  def validate_score(cls, v: int) -> int:
    if v < 1 or v > 100:
      raise ValueError('Баллы за вопрос должны быть в диапазоне от 1 до 100')
    return v


class QuestionCreate(QuestionBase):
  test_id: UUID = Field(..., description="ID теста")


class QuestionUpdate(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  text: Optional[str] = Field(None, min_length=10, max_length=2000)
  question_type: Optional[QuestionType] = None
  order_index: Optional[int] = Field(None, ge=0, le=100)
  score: Optional[int] = Field(None, ge=1, le=100)

  @model_validator(mode='after')
  def validate_not_all_null(self):
    if all([
      self.text is None,
      self.question_type is None,
      self.order_index is None,
      self.score is None
    ]):
      raise ValueError('Для обновления вопроса необходимо указать хотя бы одно поле')
    return self


class QuestionResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  text: str
  question_type: QuestionType
  order_index: int
  score: int
  test_id: UUID
  delete_flg:bool
  created_at: datetime
  update_at: datetime


class QuestionWithTest(QuestionResponse):
  test: 'TestResponse'


class QuestionWithAnswers(QuestionResponse):
  answers: List['AnswerResponse'] = Field(default_factory=list, description="Варианты ответов")
