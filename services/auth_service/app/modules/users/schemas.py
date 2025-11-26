from datetime import datetime

from pydantic import BaseModel


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
