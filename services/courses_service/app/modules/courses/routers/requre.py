from fastapi import Depends, HTTPException, status
from app.common.deps.auth import get_current_user,CurrentUser

def require_roles(*allowed_roles):
  async def role_checker(user=Depends(get_current_user)):
    user_roles = set(user.roles)
    if user_roles.intersection(allowed_roles):
      return user
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Недостаточно прав"
    )

  return role_checker
