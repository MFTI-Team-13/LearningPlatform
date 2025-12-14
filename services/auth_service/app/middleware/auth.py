from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from learning_platform_common.utils import ResponseUtils
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.common.db.session import SessionLocal
from app.core.security import TokenError, verify_access_token
from app.modules.users.models import User

PUBLIC_PATHS = {
  "/",
  "/docs",
  "/redoc",
  "/openapi.json",
  "/healthz",
  "/auth/login",
  "/auth/register",
  "/auth/refresh",
  "/auth/.well-known/jwks.json",
}

PUBLIC_GET_PATHS = {
  "/roles",
}


def _normalize_path(path: str) -> str:
  normalized = path.rstrip("/")
  return normalized or "/"


def _is_public(path: str, method: str) -> bool:
  if method == "OPTIONS":
    return True
  if path in PUBLIC_PATHS:
    return True
  if method == "GET" and path in PUBLIC_GET_PATHS:
    return True
  if method == "GET" and path.startswith("/roles/"):
    return True
  return False


def _extract_bearer_token(request: Request) -> str | None:
  auth_header = request.headers.get("authorization")
  if auth_header and auth_header.lower().startswith("bearer "):
    return auth_header.split(" ", 1)[1].strip()
  return request.cookies.get("access_token")


class AuthMiddleware(BaseHTTPMiddleware):
  async def dispatch(
    self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
  ) -> Response:
    path = _normalize_path(request.url.path)
    if _is_public(path, request.method.upper()):
      return await call_next(request)

    token = _extract_bearer_token(request)
    if not token:
      return JSONResponse(ResponseUtils.error("access_required"), status_code=401)

    try:
      claims = verify_access_token(token)
    except TokenError as exc:
      return JSONResponse(ResponseUtils.error(str(exc)), status_code=401)

    try:
      user_id = uuid.UUID(claims.get("sub", ""))
    except (TypeError, ValueError):
      return JSONResponse(ResponseUtils.error("invalid_subject"), status_code=401)

    async with SessionLocal() as db:
      user = await db.scalar(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
      )

    if not user or not user.is_active:
      return JSONResponse(ResponseUtils.error("user_inactive"), status_code=401)

    if not user.role:
      return JSONResponse(ResponseUtils.error("role_not_configured"), status_code=500)

    request.state.auth_user_id = user.id
    request.state.auth_user_role = user.role.slug
    request.state.auth_token = token
    request.state.auth_claims = claims

    return await call_next(request)


@dataclass
class AuthContext:
  user_id: uuid.UUID
  role: str
  claims: dict


def current_auth(request: Request) -> AuthContext:
  user_id = getattr(request.state, "auth_user_id", None)
  role = getattr(request.state, "auth_user_role", None)
  claims = getattr(request.state, "auth_claims", None)
  if not user_id or not role:
    raise HTTPException(status_code=401, detail="access_required")
  return AuthContext(user_id=user_id, role=role, claims=claims or {})


def require_roles(*roles: str):
  async def _checker(ctx: Annotated[AuthContext, Depends(current_auth)]) -> AuthContext:
    if roles and ctx.role not in roles:
      raise HTTPException(status_code=403, detail="forbidden")
    return ctx

  return _checker


def setup_auth_middleware(app: FastAPI) -> None:
  app.add_middleware(AuthMiddleware)
