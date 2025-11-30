from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
  username: str = Field(min_length=3, max_length=150)
  password: str = Field(min_length=8)
  first_name: str = Field(min_length=1)
  last_name: str = Field(min_length=1)
  middle_name: str | None = None
  email: EmailStr | None = None


class UserOut(BaseModel):
  id: str
  email: str
  is_active: bool
  is_verified: bool
  must_change_password: bool

  role: str

  created_at: datetime | None = None
  updated_at: datetime | None = None
  last_login: datetime | None = None

  display_name: str | None = None
  login: str | None = None
