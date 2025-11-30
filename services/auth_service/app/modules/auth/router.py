from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from learning_platform_common.utils import ResponseUtils
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_db
from app.core.config import settings
from app.core.security import (
  get_public_key_pem,
  hash_password,
  public_key_to_jwk_components,
)
from app.modules.users.models import User, UserProfile
from app.modules.users.schemas import UserRegisterRequest

DbSession = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter()


@router.get("/")
async def root():
  return ResponseUtils.success("ok")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
  payload: UserRegisterRequest,
  db: DbSession,
):
  existing_user = await db.scalar(select(User.id).where(User.username == payload.username))
  if existing_user:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username_taken")

  user = User(
    username=payload.username,
    email=payload.email,
    hashed_password=hash_password(payload.password),
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
