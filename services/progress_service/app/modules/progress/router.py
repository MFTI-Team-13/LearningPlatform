from fastapi import APIRouter, Security
from learning_platform_common.utils import ResponseUtils

from app.common.deps.auth import CurrentUser, get_current_user

router = APIRouter()


@router.get("/")
async def root():
  return ResponseUtils.success("ok")

@router.get("/get_user")
async def root(user: CurrentUser = Security(get_current_user),):
  return ResponseUtils.success(user=user)
