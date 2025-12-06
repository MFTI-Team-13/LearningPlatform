from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.roles.router import router as roles_router
from app.modules.users.router import router as users_router

main_router = APIRouter()

main_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
main_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
main_router.include_router(users_router, prefix="/users", tags=["Users"])

__all__ = ["main_router"]
