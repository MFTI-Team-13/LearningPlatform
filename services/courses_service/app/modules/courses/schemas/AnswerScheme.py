from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from typing import Optional
from uuid import UUID


class AnswerBase(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  text: str = Field(..., min_length=1, max_length=1000, description="Текст ответа")
  is_correct: bool = Field(default=False, description="Правильный ли ответ")
  order_index: int = Field(..., ge=1, le=100, description="Порядковый номер")

  @field_validator('text')
  @classmethod
  def validate_text(cls, v: str) -> str:
    if not v or v.isspace():
      raise ValueError('Текст ответа не может быть пустым')
    return v.strip()

  @field_validator('order_index')
  @classmethod
  def validate_order_index(cls, v: int) -> int:
    if v < 1 or v > 100:
      raise ValueError('Порядковый номер должен быть в диапазоне от 1 до 100')
    return v


class AnswerCreate(AnswerBase):
  question_id: UUID = Field(..., description="ID вопроса")


class AnswerUpdate(BaseModel):
  model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

  text: Optional[str] = Field(None, min_length=1, max_length=1000)
  is_correct: Optional[bool] = None
  order_index: Optional[int] = Field(None, ge=1, le=100)

  @model_validator(mode='after')
  def validate_not_all_null(self):
    if all([
      self.text is None,
      self.is_correct is None,
      self.order_index is None
    ]):
      raise ValueError('Для обновления ответа необходимо указать хотя бы одно поле')
    return self


class AnswerResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  text: str
  is_correct: bool
  order_index: int
  question_id: UUID


class AnswerWithQuestion(AnswerResponse):
  question: 'QuestionResponse'
