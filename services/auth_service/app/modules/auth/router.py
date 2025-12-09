import datetime as dt
import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from learning_platform_common.utils import ResponseUtils
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.db.session import get_db
from app.core.config import settings
from app.core.security import (
  TokenError,
  get_public_key_pem,
  hash_password,
  make_access_jwt,
  make_refresh_jwt,
  public_key_to_jwk_components,
  set_token_cookies,
  verify_password,
  verify_refresh_token,
)
from app.middleware.auth import AuthContext, current_auth
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest, RefreshRequest
from app.modules.roles.models import Role
from app.modules.users.models import User, UserProfile
from app.modules.users.schemas import UserOut, UserRegisterRequest

DbSession = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter()


def _hash_refresh_token(raw: str) -> str:
  return hashlib.sha256(raw.encode()).hexdigest()


async def _get_role_or_error(db: DbSession, slug: str) -> Role:
  role = await db.scalar(select(Role).where(Role.slug == slug))
  if not role:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="role_not_configured",
    )
  return role


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
  payload: UserRegisterRequest,
  db: DbSession,
):
  existing_user = await db.scalar(select(User.id).where(User.username == payload.username))
  if existing_user:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username_taken")

  default_role = await _get_role_or_error(db, "student")

  user = User(
    username=payload.username,
    email=payload.email,
    hashed_password=hash_password(payload.password),
    role=default_role,
  )
  profile = UserProfile(
    user=user,
    first_name=payload.first_name,
    last_name=payload.last_name,
    middle_name=payload.middle_name,
    display_name=f"{payload.first_name} {payload.last_name}".strip(),
  )

  db.add(user)
  db.add(profile)

  try:
    await db.commit()
  except IntegrityError:
    await db.rollback()
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username_taken") from None

  await db.refresh(user)

  return ResponseUtils.success(
    message="user_registered",
    user_id=str(user.id),
    username=user.username,
  )


@router.post("/login")
async def login(
  payload: LoginRequest,
  response: Response,
  request: Request,
  db: DbSession,
):
  user = await db.scalar(
    select(User).options(selectinload(User.role)).where(User.username == payload.username)
  )
  if not user or not verify_password(payload.password, user.hashed_password):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

  if not user.role:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="role_not_configured"
    )

  now = dt.datetime.now(dt.UTC)
  refresh_id = uuid.uuid4()
  access_token = make_access_jwt(str(user.id), user.role.slug)
  refresh_token = make_refresh_jwt(str(user.id), str(refresh_id))

  refresh_entry = RefreshToken(
    id=refresh_id,
    user_id=user.id,
    token_hash=_hash_refresh_token(refresh_token),
    fingerprint=request.headers.get("x-device-fingerprint"),
    user_agent=request.headers.get("user-agent"),
    expires_at=now + dt.timedelta(days=settings.jwt_refresh_ttl_days),
  )

  user.last_login = now

  db.add(refresh_entry)

  await db.commit()

  set_token_cookies(response, access_token, refresh_token)

  return ResponseUtils.success(
    message="login_successful",
    access_token=access_token,
    refresh_token=refresh_token,
  )


@router.post("/refresh")
async def refresh_tokens(
  payload: RefreshRequest,
  response: Response,
  request: Request,
  db: DbSession,
):
  raw_refresh = payload.refresh_token or request.cookies.get("refresh_token")
  if not raw_refresh:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_required")

  try:
    claims = verify_refresh_token(raw_refresh)
  except TokenError as exc:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

  token_hash = _hash_refresh_token(raw_refresh)
  refresh_entry = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
  now = dt.datetime.now(dt.UTC)

  if (
    not refresh_entry
    or refresh_entry.revoked_at is not None
    or refresh_entry.expires_at <= now
    or str(refresh_entry.id) != claims.get("jti")
  ):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh_invalid")

  user = await db.scalar(
    select(User).options(selectinload(User.role)).where(User.id == refresh_entry.user_id)
  )
  if not user or not user.is_active:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive")

  if not user.role:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="role_not_configured"
    )

  new_refresh_id = uuid.uuid4()
  access_token = make_access_jwt(str(user.id), user.role.slug)
  new_refresh_token = make_refresh_jwt(str(user.id), str(new_refresh_id))

  refresh_entry.revoked_at = now
  refresh_entry.replaced_by = new_refresh_id

  replacement = RefreshToken(
    id=new_refresh_id,
    user_id=user.id,
    token_hash=_hash_refresh_token(new_refresh_token),
    fingerprint=request.headers.get("x-device-fingerprint"),
    user_agent=request.headers.get("user-agent"),
    expires_at=now + dt.timedelta(days=settings.jwt_refresh_ttl_days),
  )
  db.add(replacement)

  await db.commit()

  set_token_cookies(response, access_token, new_refresh_token)

  return ResponseUtils.success(
    message="tokens_refreshed",
    access_token=access_token,
    refresh_token=new_refresh_token,
  )


@router.get("/me")
async def get_current_user(
  db: DbSession,
  auth: Annotated[AuthContext, Depends(current_auth)],
):
  user = await db.scalar(
    select(User)
    .options(selectinload(User.profile), selectinload(User.role))
    .where(User.id == auth.user_id)
  )

  if not user or not user.is_active:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive")

  profile = user.profile
  user_payload = UserOut(
    id=str(user.id),
    email=user.email or "",
    is_active=user.is_active,
    is_verified=user.is_verified,
    must_change_password=user.must_change_password,
    role=user.role.slug if user.role else None,
    created_at=user.created_at,
    updated_at=user.updated_at,
    last_login=user.last_login,
    display_name=profile.display_name if profile else None,
    login=user.username,
  ).model_dump()

  return ResponseUtils.success(message="current_user", user=user_payload)


@router.post("/change-password")
async def change_password(
  payload: ChangePasswordRequest,
  db: DbSession,
  auth: Annotated[AuthContext, Depends(current_auth)],
):
  user = await db.get(User, auth.user_id)
  if not user or not user.is_active:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive")

  if not verify_password(payload.current_password, user.hashed_password):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="wrong_password")

  if payload.current_password == payload.new_password:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="password_same")

  user.hashed_password = hash_password(payload.new_password)
  user.must_change_password = False

  now = dt.datetime.now(dt.UTC)
  await db.execute(
    update(RefreshToken)
    .where(RefreshToken.user_id == user.id)
    .where(RefreshToken.revoked_at.is_(None))
    .values(revoked_at=now)
  )

  await db.commit()

  return ResponseUtils.success(message="password_changed")


@router.get("/.well-known/jwks.json")
async def jwks():
  if settings.jwt_alg != "RS256":
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="jwks_not_available")

  public_key = get_public_key_pem()
  n, e = public_key_to_jwk_components(public_key)

  return {
    "keys": [
      {
        "kty": "RSA",
        "use": "sig",
        "kid": "main-key-1",
        "alg": "RS256",
        "n": n,
        "e": e,
      }
    ]
  }
