import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from learning_platform_common.utils import ResponseUtils
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.db.session import get_db
from app.middleware.auth import require_roles
from app.modules.roles.models import Role
from app.modules.users.models import User, UserProfile
from app.modules.users.schemas import UserOut, UserUpdateRequest

DbSession = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter()


@router.get("/", dependencies=[Depends(require_roles("admin"))])
async def list_users(
  db: DbSession,
  q: Annotated[str | None, Query(description="search by username or email")] = None,
  role_ids: Annotated[list[uuid.UUID] | None, Query(alias="role_ids[]")] = None,
  order_by: Annotated[str, Query(pattern="^(email|created_at|verified)$")] = "created_at",
  order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
  limit: Annotated[int, Query(ge=1, le=100)] = 20,
  offset: Annotated[int, Query(ge=0)] = 0,
):
  stmt = select(User).options(selectinload(User.role), selectinload(User.profile))

  if q:
    like_expr = f"%{q}%"
    stmt = stmt.where(or_(User.email.ilike(like_expr), User.username.ilike(like_expr)))

  if role_ids:
    stmt = stmt.join(User.role).where(Role.id.in_(role_ids))

  if order_by == "email":
    ob_col = User.email
  elif order_by == "verified":
    ob_col = User.is_verified
  else:
    ob_col = User.created_at

  stmt = stmt.order_by(ob_col.asc() if order == "asc" else ob_col.desc())

  rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().unique().all()

  count_stmt = select(func.count(func.distinct(User.id))).select_from(User)
  if q:
    like_expr = f"%{q}%"
    count_stmt = count_stmt.where(or_(User.email.ilike(like_expr), User.username.ilike(like_expr)))
  if role_ids:
    count_stmt = count_stmt.join(User.role).where(Role.id.in_(role_ids))

  total = await db.scalar(count_stmt)

  items = [
    UserOut(
      id=str(u.id),
      email=u.email or "",
      is_active=u.is_active,
      is_verified=u.is_verified,
      must_change_password=u.must_change_password,
      role=u.role.slug if u.role else None,
      created_at=u.created_at,
      updated_at=u.updated_at,
      last_login=u.last_login,
      display_name=u.profile.display_name if u.profile else None,
      login=u.username,
    ).model_dump()
    for u in rows
  ]

  return ResponseUtils.success(items=items, total=total or 0, limit=limit, offset=offset)


@router.get("/{user_id}", dependencies=[Depends(require_roles("admin"))])
async def get_user_by_id(user_id: uuid.UUID, db: DbSession):
  user = await db.scalar(
    select(User)
    .options(selectinload(User.role), selectinload(User.profile))
    .where(User.id == user_id)
  )
  if not user:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

  payload = UserOut(
    id=str(user.id),
    email=user.email or "",
    is_active=user.is_active,
    is_verified=user.is_verified,
    must_change_password=user.must_change_password,
    role=user.role.slug if user.role else None,
    created_at=user.created_at,
    updated_at=user.updated_at,
    last_login=user.last_login,
    display_name=user.profile.display_name if user.profile else None,
    login=user.username,
  ).model_dump()

  return ResponseUtils.success(user=payload)


@router.patch("/{user_id}", dependencies=[Depends(require_roles("admin"))])
async def update_user(user_id: uuid.UUID, payload: UserUpdateRequest, db: DbSession):
  user = await db.scalar(
    select(User)
    .options(selectinload(User.role), selectinload(User.profile))
    .where(User.id == user_id)
  )
  if not user:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

  if payload.role_id:
    role = await db.get(Role, uuid.UUID(payload.role_id))
    if not role:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role_not_found")
    user.role = role

  if payload.email is not None:
    user.email = payload.email
  if payload.is_active is not None:
    user.is_active = payload.is_active
  if payload.is_verified is not None:
    user.is_verified = payload.is_verified
  if payload.must_change_password is not None:
    user.must_change_password = payload.must_change_password

  profile = user.profile
  if not profile:
    profile = UserProfile(user=user)
    db.add(profile)

  if payload.first_name is not None:
    profile.first_name = payload.first_name
  if payload.last_name is not None:
    profile.last_name = payload.last_name
  if payload.middle_name is not None:
    profile.middle_name = payload.middle_name
  if payload.display_name is not None:
    profile.display_name = payload.display_name

  await db.commit()
  await db.refresh(user)

  return await get_user_by_id(user_id, db)
