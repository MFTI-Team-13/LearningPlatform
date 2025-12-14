# app/common/deps/auth.py
from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel

from app.core.security import current_token_payload


class CurrentUser(BaseModel):
    id: UUID
    roles: set[str]
    payload: dict[str, Any]


async def get_current_user(
    payload: dict[str, Any] = Security(current_token_payload),
) -> CurrentUser:
    """
    Достаём id и роли из payload токена.
    Ожидаем поля:
      - sub: user_id
      - roles / role_slugs: ["admin", "teacher", ...]
    """
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token_sub",
        )

    try:
        user_id = UUID(str(sub))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token_sub",
        )

    roles_raw = payload.get("role") or payload.get("role_slugs") or []
    if not isinstance(roles_raw, (list, tuple, set)):
        roles_raw = [roles_raw]

    roles = {str(r) for r in roles_raw}

    if not roles:
        # можно убрать, если хочешь пускать юзеров без ролей
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="no_roles",
        )

    return CurrentUser(id=user_id, roles=roles,payload=payload)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(*allowed_roles: str):
  allowed = {r.lower() for r in allowed_roles}

  async def _checker(user: CurrentUser = Security(get_current_user)) -> None:
    user_roles = {r.lower() for r in user.roles}
    if not (user_roles & allowed):
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "forbidden_role", "allowed": list(allowed)},
      )

  return _checker
