from fastapi import Depends, HTTPException
from uuid import UUID
from datetime import datetime

from app.modules.courses.repositories_import import UserRepository, get_user_repository
from app.modules.courses.schemas.UserScheme import UserCreate, UserUpdate, UserRole
from .BaseService import BaseService


class UserService(BaseService):

    def __init__(self, repo: UserRepository):
        super().__init__(repo)
        self.repo = repo

    async def get_by_login(self, login: str):
        user = await self.repo.get_by_login(login)
        if not user:
            raise HTTPException(404, "Пользователь не найден")
        return user

    async def get_by_display_name(self, display_name: str):
        user = await self.repo.get_by_display_name(display_name)
        if not user:
            raise HTTPException(404, "Пользователь не найден")
        return user

    async def exists_by_login(self, login: str):
        return await self.repo.exists_by_login(login)

    async def get_by_role(self, role: UserRole, skip: int, limit: int):
        return await self.repo.get_by_role(role, skip, limit)

    async def restore(self, id: UUID):
        restored = await self.repo.restore(id)
        if not restored:
            raise HTTPException(404, "Пользователь не найден")
        return restored

    async def search_users(self, query: str, skip: int, limit: int):
        return await self.repo.search_users(query, skip, limit)

    async def change_role(self, id: UUID, new_role: UserRole):
        user = await self.get_by_id(id)
        return await self.repo.change_role(id, new_role)

    async def count_users(self):
        return await self.repo.count_users()

    async def get_users_created_in_period(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int,
        limit: int
    ):
        return await self.repo.get_users_created_in_period(start_date, end_date, skip, limit)

    async def soft_delete(self, id: UUID):
        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        return await self.repo.hard_delete(id)


async def get_user_service(
    repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(repo)
