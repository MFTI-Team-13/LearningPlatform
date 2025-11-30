from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
  username: str = Field(min_length=3, max_length=150)
  password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
  refresh_token: str | None = None


class ChangePasswordRequest(BaseModel):
  current_password: str = Field(min_length=8)
  new_password: str = Field(min_length=8)
