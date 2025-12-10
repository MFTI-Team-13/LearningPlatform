from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated, Callable, Awaitable

import jwt
from fastapi import Depends, HTTPException, Request
from learning_platform_common.utils import ResponseUtils
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

AUTH_JWKS_URL = os.getenv("AUTH_JWKS_URL")
AUTH_ISSUER = os.getenv("AUTH_ISSUER")
AUTH_AUDIENCE = os.getenv("AUTH_AUDIENCE")
AUTH_ALG = os.getenv("AUTH_ALG", "RS256")

PUBLIC_PATHS = {
  "/",
  "/docs",
  "/redoc",
  "/openapi.json",
  "/healthz",
"/courses",
}

_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient:
  global _jwks_client
  if _jwks_client is None:
    if not AUTH_JWKS_URL:
      raise RuntimeError("AUTH_JWKS_URL is not configured")
    _jwks_client = jwt.PyJWKClient(AUTH_JWKS_URL)
  return _jwks_client


def _extract_bearer_token(request: Request) -> str | None:
  auth_header = request.headers.get("authorization")
  if auth_header and auth_header.lower().startswith("bearer "):
    res = auth_header.split(" ", 1)[1].strip()
    print(res)
    return res
  return request.cookies.get("access_token")


def _is_public(request: Request) -> bool:
  if request.method.upper() == "OPTIONS":
    return True
  path = request.url.path.rstrip("/") or "/"
  return path in PUBLIC_PATHS


class AuthMiddleware(BaseHTTPMiddleware):
  async def dispatch(
    self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
  ) -> Response:
    if _is_public(request):
      return await call_next(request)

    token = _extract_bearer_token(request)
    if not token:
      return JSONResponse(ResponseUtils.error("access_required"), status_code=401)

    try:
      jwks_client = _get_jwks_client()
      try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
      except jwt.exceptions.PyJWKClientError:
        signing_keys = jwks_client.get_signing_keys()
        if not signing_keys:
          raise jwt.InvalidTokenError("No signing keys available")
        signing_key = signing_keys[0].key

      payload = jwt.decode(
        token,
        key=signing_key,
        algorithms=[AUTH_ALG],
        issuer=AUTH_ISSUER,
      )
    except jwt.ExpiredSignatureError:
      return JSONResponse(ResponseUtils.error("token_expired"), status_code=401)
    except jwt.InvalidTokenError:
      return JSONResponse(ResponseUtils.error("token_invalid"), status_code=401)
    except jwt.exceptions.PyJWKClientConnectionError:
      return JSONResponse(
        ResponseUtils.error("auth_service_unavailable"), status_code=503
      )

    if payload.get("type") != "access":
      return JSONResponse(ResponseUtils.error("not_access"), status_code=401)

    request.state.auth_payload = payload
    request.state.auth_role = payload.get("role")
    request.state.auth_user_id = payload.get("sub")

    return await call_next(request)


@dataclass
class AuthContext:
  user_id: str
  role: str | None
  claims: dict


def current_auth(request: Request) -> AuthContext:
  payload = getattr(request.state, "auth_payload", None)
  if not payload:
    raise HTTPException(status_code=401, detail="access_required")
  return AuthContext(
    user_id=str(payload.get("sub")),
    role=payload.get("role"),
    claims=payload,
  )


def require_roles(*roles: str):
  async def _checker(ctx: Annotated[AuthContext, Depends(current_auth)]) -> AuthContext:
    if roles and ctx.role not in roles:
      raise HTTPException(status_code=403, detail="forbidden")
    return ctx

  return _checker


def setup_auth_middleware(app) -> None:
  app.add_middleware(AuthMiddleware)
