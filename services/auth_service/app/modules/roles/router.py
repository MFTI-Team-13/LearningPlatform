from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from learning_platform_common.utils import ResponseUtils
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_db
from app.middleware.auth import require_roles
from app.modules.roles.models import Role
from app.modules.roles.schemas import RoleCreate, RoleOut, RoleUpdate
from app.modules.users.models import User

DbSession = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter(dependencies=[Depends(require_roles("admin"))])


def _serialize_role(role: Role) -> dict:
  return RoleOut(
    id=str(role.id),
    slug=role.slug,
    name=role.name,
    description=role.description,
    is_system=role.is_system,
    created_at=role.created_at,
    updated_at=role.updated_at,
  ).model_dump()


def _parse_uuid(role_id: str) -> uuid.UUID:
  try:
    return uuid.UUID(role_id)
  except ValueError as exc:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_role_id") from exc


def _get_slug(value: str | None) -> str | None:
  return value.lower().strip() if value else value


@router.get("/")
async def list_roles(db: DbSession):
  result = await db.scalars(select(Role).order_by(Role.slug))
  roles = result.all()
  return ResponseUtils.success(
    total=len(roles),
    roles=[_serialize_role(role) for role in roles],
  )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreate, db: DbSession):
  role = Role(
    slug=_get_slug(payload.slug) or payload.slug,
    name=payload.name,
    description=payload.description,
    is_system=payload.is_system,
  )
  db.add(role)

  try:
    await db.commit()
  except IntegrityError as exc:
    await db.rollback()
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="role_exists") from exc

  await db.refresh(role)
  return ResponseUtils.success(role=_serialize_role(role))


async def _get_role_or_404(role_id: str, db: DbSession) -> Role:
  rid = _parse_uuid(role_id)
  role = await db.get(Role, rid)
  if not role:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="role_not_found")
  return role


@router.get("/{role_id}")
async def get_role(role_id: str, db: DbSession):
  role = await _get_role_or_404(role_id, db)
  return ResponseUtils.success(role=_serialize_role(role))


@router.patch("/{role_id}")
async def update_role(role_id: str, payload: RoleUpdate, db: DbSession):
  role = await _get_role_or_404(role_id, db)

  if payload.slug is not None:
    role.slug = _get_slug(payload.slug) or role.slug
  if payload.name is not None:
    role.name = payload.name
  if payload.description is not None:
    role.description = payload.description
  if payload.is_system is not None:
    role.is_system = payload.is_system

  try:
    await db.commit()
  except IntegrityError as exc:
    await db.rollback()
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="role_exists") from exc

  await db.refresh(role)
  return ResponseUtils.success(role=_serialize_role(role))


@router.delete("/{role_id}")
async def delete_role(role_id: str, db: DbSession):
  role = await _get_role_or_404(role_id, db)

  if role.is_system:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role_protected")

  assignments = await db.scalar(
    select(func.count()).select_from(User).where(User.role_id == role.id)
  )
  if assignments:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role_in_use")

  await db.delete(role)
  await db.commit()
  return ResponseUtils.success(message="role_deleted")
