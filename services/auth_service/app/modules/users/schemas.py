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

  role: str | None = None

  created_at: datetime | None = None
  updated_at: datetime | None = None
  last_login: datetime | None = None

  display_name: str | None = None
  login: str | None = None


class UserUpdateRequest(BaseModel):
  email: EmailStr | None = None
  role_id: str | None = None
  is_active: bool | None = None
  is_verified: bool | None = None
  must_change_password: bool | None = None
  first_name: str | None = Field(default=None, min_length=1)
  last_name: str | None = Field(default=None, min_length=1)
  middle_name: str | None = None
  display_name: str | None = None
