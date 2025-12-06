from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
  slug: str = Field(min_length=2, max_length=50)
  name: str = Field(min_length=1, max_length=100)
  description: str | None = Field(default=None, max_length=255)
  is_system: bool = False


class RoleCreate(RoleBase):
  slug: str = Field(min_length=2, max_length=50)


class RoleUpdate(BaseModel):
  slug: str | None = Field(default=None, min_length=2, max_length=50)
  name: str | None = Field(default=None, min_length=1, max_length=100)
  description: str | None = Field(default=None, max_length=255)
  is_system: bool | None = None


class RoleOut(BaseModel):
  id: str
  slug: str
  name: str
  description: str | None = None
  is_system: bool
  created_at: datetime | None = None
  updated_at: datetime | None = None

  model_config = ConfigDict(from_attributes=True)
