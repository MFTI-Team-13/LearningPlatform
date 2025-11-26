from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path

import jwt
from app.core.config import settings
from jwt import (
  ExpiredSignatureError,
  InvalidSignatureError,
  InvalidTokenError,
)
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from starlette.responses import Response

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class TokenError(ValueError):
  pass


def _int_from_env_or_settings(env: str, settings_value, default: int) -> int:
  v = os.getenv(env)
  if v is not None:
    return int(v)
  if settings_value is not None:
    return int(settings_value)
  return int(default)


@lru_cache
def _pwd_ctx() -> CryptContext:
  scheme = (
    getattr(settings, "password_scheme", None) or os.getenv("PASSWORD_SCHEME") or "argon2"
  ).lower()

  a_time = _int_from_env_or_settings(
    "ARGON2_TIME_COST",
    getattr(settings, "argon2_time_cost", None),
    3,
  )

  a_mem = _int_from_env_or_settings(
    "ARGON2_MEMORY_COST",
    getattr(settings, "argon2_memory_cost", None),
    65536,
  )

  a_par = _int_from_env_or_settings(
    "ARGON2_PARALLELISM",
    getattr(settings, "argon2_parallelism", None),
    2,
  )
  if scheme == "bcrypt":
    schemes = ["bcrypt", "argon2"]
    deprecated = ["argon2"]
    bcrypt_rounds = _int_from_env_or_settings(
      "BCRYPT_ROUNDS", getattr(settings, "bcrypt_rounds", None), 12
    )

    return CryptContext(
      schemes=schemes,
      deprecated=deprecated,
      bcrypt__rounds=bcrypt_rounds,
      argon2__type="ID",
      argon2__time_cost=a_time,
      argon2__memory_cost=a_mem,
      argon2__parallelism=a_par,
    )
  else:
    schemes = ["argon2", "bcrypt"]
    deprecated = ["bcrypt"]
    return CryptContext(
      schemes=schemes,
      deprecated=deprecated,
      argon2__type="ID",
      argon2__time_cost=a_time,
      argon2__memory_cost=a_mem,
      argon2__parallelism=a_par,
    )


def set_token_cookies(response: Response, access: str, refresh: str) -> None:
  common = dict(
    httponly=True,
    secure=settings.cookie_secure,
    samesite=settings.cookie_samesite,
    path="/",
  )
  response.set_cookie("access_token", access, max_age=settings.jwt_access_ttl_min * 60, **common)
  response.set_cookie(
    "refresh_token",
    refresh,
    max_age=settings.jwt_refresh_ttl_days * 24 * 3600,
    **common,
  )


def hash_password(raw: str) -> str:
  return _pwd_ctx().hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
  try:
    return _pwd_ctx().verify(raw, hashed)
  except UnknownHashError:
    if hashed and HEX64_RE.fullmatch(hashed):
      return hashlib.sha256(raw.encode()).hexdigest() == hashed
    return False


def needs_rehash(hashed: str) -> bool:
  try:
    return _pwd_ctx().needs_update(hashed)
  except UnknownHashError:
    return True


def _read_keys():
  if settings.jwt_alg == "RS256":
    private_key = Path(settings.jwt_private_key_path).read_text()
    public_key = Path(settings.jwt_public_key_path).read_text()
  else:
    private_key = settings.jwt_secret
    public_key = settings.jwt_secret
  return private_key, public_key


_private_key, _public_key = _read_keys()


def make_access_jwt(subject: str) -> str:
  now = dt.datetime.now(dt.UTC)
  payload: dict = {
    "iss": settings.jwt_iss,
    "sub": subject,
    "iat": int(now.timestamp()),
    "exp": int((now + dt.timedelta(minutes=settings.jwt_access_ttl_min)).timestamp()),
    "type": "access",
  }
  return jwt.encode(payload, _private_key, algorithm=settings.jwt_alg)


def make_refresh_jwt(subject: str, jti: str) -> str:
  now = dt.datetime.now(dt.UTC)
  payload: dict = {
    "iss": settings.jwt_iss,
    "sub": subject,
    "iat": int(now.timestamp()),
    "exp": int((now + dt.timedelta(days=settings.jwt_refresh_ttl_days)).timestamp()),
    "jti": jti,
    "type": "refresh",
  }
  return jwt.encode(payload, _private_key, algorithm=settings.jwt_alg)


def decode_jwt(token: str) -> dict:
  return jwt.decode(token, _public_key, algorithms=[settings.jwt_alg])


def verify_access_token(token: str) -> dict:
  try:
    payload = decode_jwt(token)
  except ExpiredSignatureError as err:
    raise TokenError("token_expired") from err
  except (InvalidSignatureError, InvalidTokenError) as err:
    raise TokenError("token_invalid") from err

  iss_cfg = getattr(settings, "jwt_iss", None)
  if iss_cfg and payload.get("iss") != iss_cfg:
    raise TokenError("bad_issuer") from None

  if payload.get("type") != "access":
    raise TokenError("not_access") from None

  if "sub" not in payload:
    raise TokenError("no_sub") from None

  return payload


def verify_refresh_token(token: str) -> dict:
  try:
    payload = decode_jwt(token)
  except ExpiredSignatureError as err:
    raise TokenError("token_expired") from err
  except (InvalidSignatureError, InvalidTokenError) as err:
    raise TokenError("token_invalid") from err

  iss_cfg = getattr(settings, "jwt_iss", None)
  if iss_cfg and payload.get("iss") != iss_cfg:
    raise TokenError("bad_issuer") from None

  if payload.get("type") != "refresh":
    raise TokenError("not_refresh") from None

  if "sub" not in payload or "jti" not in payload:
    raise TokenError("no_sub_or_jti") from None

  return payload
