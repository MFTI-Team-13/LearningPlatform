# app/core/security.py
from __future__ import annotations

import base64
import time
from typing import Any

import httpx
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyCookie

from app.core.config import settings


class _JWKS:
    keys: dict[str, Any] | None = None
    exp_at: float = 0.0
    ttl: int = 300  # 5 минут


async def _get_jwks() -> dict[str, Any]:
    now = time.time()
    if _JWKS.keys is not None and now < _JWKS.exp_at:
        return _JWKS.keys  # type: ignore[return-value]

    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(settings.auth_jwks_url)
        r.raise_for_status()
        data = r.json()

    _JWKS.keys = data
    _JWKS.exp_at = now + _JWKS.ttl
    return data


def _rsa_pub_from_n_e(n_b64: str, e_b64: str) -> bytes:
    n = int.from_bytes(base64.urlsafe_b64decode(n_b64 + "=="), "big")
    e = int.from_bytes(base64.urlsafe_b64decode(e_b64 + "=="), "big")
    pub = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


async def verify_jwt(token: str) -> dict[str, Any]:
  try:
    headers = jwt.get_unverified_header(token)
  except jwt.InvalidTokenError as err:
    raise jwt.InvalidTokenError("bad_header") from err

  jwks = await _get_jwks()
  keys = jwks.get("keys", []) or []

  kid = headers.get("kid")

  if kid:
    key = next((k for k in keys if k.get("kid") == kid), None)
    if not key:
      raise jwt.InvalidTokenError("kid_not_found")
  else:
    # fallback: если kid нет, но ключ один — берём его
    if len(keys) == 1:
      key = keys[0]
    else:
      raise jwt.InvalidTokenError("missing_kid")

  pub_pem = _rsa_pub_from_n_e(key["n"], key["e"])

  payload = jwt.decode(
    token,
    pub_pem,
    algorithms=[key.get("alg", "RS256")],
    issuer=settings.auth_issuer,
    options={"require": ["exp", "iat", "iss"]},
  )
  return payload


# ---------- cookie auth для Swagger / зависимостей ----------

access_token_cookie = APIKeyCookie(
    name="access_token",
    auto_error=False,  # сами кинем 401
)


async def current_token_payload(
    raw_token: str | None = Security(access_token_cookie),
) -> dict[str, Any]:
    """
    Достаём и валидируем access_token из cookie.
    Эта зависимость попадает в OpenAPI как security-схема.
    """
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )

    try:
        payload = await verify_jwt(raw_token)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token_expired",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail={"code": "invalid_token", "reason": str(e)},
        ) from e

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="wrong_token_type",
        )

    return payload
