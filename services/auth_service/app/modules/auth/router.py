from typing import Annotated

from app.common.db.session import get_db
from app.modules.users.models import User
from app.modules.users.schemas import UserOut
from app.modules.users.utils import user_to_full_dict
from fastapi import APIRouter, Depends, HTTPException
from learning_platform_common.utils import ResponseUtils
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import current_user

router = APIRouter()
CurUser = Annotated[User, Depends(current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/me/", response_model=dict)
async def me(user: CurUser, db: DbSession):
  fresh = await db.scalar(
    select(User).options(selectinload(User.profile)).where(User.id == user.id)
  )
  if not fresh:
    raise HTTPException(status_code=404, detail="user_not_found")
  return ResponseUtils.success(user=UserOut(**user_to_full_dict(fresh)))
