from typing import Optional
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CourseUserBase(BaseModel):
  course_id: UUID = Field(..., description="ID курса")
  user_id: UUID = Field(..., description="ID пользователя")
  is_active: bool = Field(True, description="Активна ли запись")

  model_config = ConfigDict(
    from_attributes=True
  )


class CourseUserCreate(CourseUserBase):
  pass


class CourseUserUpdate(BaseModel):
  course_id: Optional[UUID] = Field(None, description="ID курса (уникальный)")
  user_id: Optional[UUID] = Field(None, description="ID пользователя")
  is_active: Optional[bool] = Field(None, description="Активна ли запись")

  model_config = ConfigDict(
    from_attributes=True
  )

class CourseUserResponse(BaseModel):
  id: UUID
  course_id: UUID
  user_id: UUID
  is_active: bool
  delete_flg: bool
  create_at: datetime
  update_at: datetime

  model_config = ConfigDict(from_attributes=True)
