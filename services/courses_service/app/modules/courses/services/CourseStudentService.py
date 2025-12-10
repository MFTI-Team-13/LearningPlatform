from uuid import UUID
from typing import Optional, List

from app.modules.courses.models_import import CourseUser
from app.modules.courses.repositories.CourseUserRepository import CourseUserRepository
from app.modules.courses.schemas.CourseUserScheme import (
    CourseUserCreate,
    CourseUserUpdate
)


class CourseUserService:

    def __init__(self, repo: CourseUserRepository):
        self.repo = repo

    async def create(self, data: CourseUserCreate) -> CourseUserResponse:
        return await self.repo.create(data.model_dump())

    async def get_by_id(self, id: UUID) -> Optional[CourseUser]:
        return await self.repo.get_by_id(id)

    async def get_by_course_id(self, course_id: UUID) -> List[CourseUserResponse]:
        return await self.repo.get_by_course_id(course_id)

    async def get_by_user_id(self, user_id: UUID) -> List[CourseUserResponse]:
        return await self.repo.get_by_user_id(user_id)

    async def get_by_course_and_user(
        self, course_id: UUID, user_id: UUID
    ) -> Optional[CourseUser]:
        return await self.repo.get_by_course_and_user(course_id, user_id)

    async def get_active_by_user_id(self, user_id: UUID) -> List[CourseUserResponse]:
        return await self.repo.get_active_by_user_id(user_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[CourseUserResponse]:
        return await self.repo.get_all(skip, limit)

    async def get_active(self, skip: int = 0, limit: int = 100) -> List[CourseUserResponse]:
        return await self.repo.get_active(skip, limit)

    async def update(self, id: UUID, data: CourseUserUpdate) -> Optional[CourseUserResponse]:
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(id, update_data)

    async def delete(self, id: UUID) -> bool:
        return await self.repo.hard_delete(id)

    async def activate(self, id: UUID) -> bool:
        return await self.repo.activate(id)

    async def unactivate(self, id: UUID) -> bool:
        return await self.repo.unactivate(id)
