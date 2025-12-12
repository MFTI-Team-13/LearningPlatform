from typing import Optional, List

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from app.modules.courses.models_import import CourseUser
from app.modules.courses.repositories_import import (
    CourseUserRepository,
    get_course_user_repository,
    CourseRepository,
    get_course_repository
)
from app.modules.courses.schemas.CourseUserScheme import (
    CourseUserCreate
)
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)

class CourseUserService(BaseService):

    def __init__(self, repo: CourseUserRepository, course_repo: CourseRepository):
        super().__init__(repo)
        self.repo = repo
        self.course_repo = course_repo

    async def find_course(self, course_id: UUID, delete_flg:bool | None):
        course_exists = await self.course_repo.get_by_id(course_id, delete_flg=None)

        if not course_exists:
            raise NotFoundError("Курс не существует")
        if delete_flg == False and course_exists.delete_flg == True:
            raise NotFoundError("Курс не найден")

        return course_exists

    async def create(self, in_data: CourseUserCreate) -> CourseUser:
        await self.find_course(in_data.course_id, delete_flg=False)
        return await self.repo.create(in_data.model_dump())

    async def get_by_course_id(self, course_id: UUID, delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        await self.find_course(course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not res:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_by_user_id(self, user_id: UUID, delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        res = await self.repo.get_by_user_id(user_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_by_course_and_user_id(self, course_id: UUID, user_id: UUID, delete_flg:bool | None) -> Optional[CourseUser]:
        await self.find_course(course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_and_user_id(course_id, user_id, delete_flg)
        if not res:
            raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_active_by_user_id(self, user_id: UUID, delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        res = await self.repo.get_active_by_user_id(user_id, delete_flg,skip, limit)

        if not res:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_all_active(self, is_active:bool,delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        res =  await self.repo.get_active(is_active, delete_flg, skip, limit)

        if not res:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def activate(self, id: UUID):
        courseUser = await self.get_by_id(id, None)

        if courseUser.delete_flg:
          raise ConflictError("Нельзя активировать удалённое назначение")

        if courseUser.is_active:
            raise ConflictError("Назначенный курс уже активен для пользователя")

        return await self.repo.activate(id)

    async def deactivate(self, id: UUID):
        courseUser = await self.get_by_id(id, None)

        if not courseUser.is_active:
          raise ConflictError("Назначенный курс уже не активен для пользователя")

        return await self.repo.deactivate(id)

async def get_course_user_service(
  repo: CourseUserRepository = Depends(get_course_user_repository),
  course_repo: CourseRepository = Depends(get_course_repository)
) -> CourseUserService:
  return CourseUserService(repo, course_repo)
