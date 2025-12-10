from typing import Any

from app.modules.users.models import User


def user_to_full_dict(user: User) -> dict[str, Any]:
  role = getattr(user, "role", None)
  profile = getattr(user, "profile", None)

  return {
    "id": str(user.id),
    "email": user.email,
    "is_active": bool(getattr(user, "is_active", False)),
    "is_verified": bool(getattr(user, "is_verified", False)),
    "must_change_password": bool(getattr(user, "must_change_password", False)),
    "roles": [str(getattr(role, "id", ""))] if role else [],
    "role_names": [getattr(role, "name", "")] if role else [],
    "created_at": getattr(user, "created_at", None),
    "updated_at": getattr(user, "updated_at", None),
    "last_login": getattr(user, "last_login", None),
    "login": getattr(profile, "login", None) if profile else None,
  }
