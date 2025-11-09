from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserOut(BaseModel):
  id: str
  email: str
  is_active: bool
  is_verified: bool
  must_change_password: bool

  role: str

  created_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None
  last_login: Optional[datetime] = None

  display_name: Optional[str] = None
  login: Optional[str] = None