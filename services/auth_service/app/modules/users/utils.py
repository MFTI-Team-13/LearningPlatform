from typing import Dict, Any

from app.modules.users.models import User


def user_to_full_dict(user: User) -> Dict[str, Any]:
  roles = getattr(user, "roles", []) or []
  profile = getattr(user, "profile", None)

  return {
    "id": str(user.id),
    "email": user.email,
    "is_active": bool(getattr(user, "is_active", False)),
    "is_verified": bool(getattr(user, "is_verified", False)),
    "must_change_password": bool(getattr(user, "must_change_password", False)),

    "roles": [str(getattr(r, "id", "")) for r in roles],
    "role_names": [getattr(r, "name", "") for r in roles],

    "created_at": getattr(user, "created_at", None),
    "updated_at": getattr(user, "updated_at", None),
    "last_login": getattr(user, "last_login", None),

    "login": getattr(profile, "login", None) if profile else None,
  }