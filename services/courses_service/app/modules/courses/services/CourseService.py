from fastapi import Depends
from uuid import UUID

from app.modules.courses.repositories_import import CourseRepository, get_course_repository
from app.modules.courses.schemas.CourseScheme import CourseCreate, CourseUpdate, CourseResponse
from .BaseService import BaseService

from app.modules.courses.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ConflictError,
)


class CourseService(BaseService):
    def __init__(self, repo: CourseRepository):
        super().__init__(repo)
        self.repo: CourseRepository = repo

    async def create(self, in_data: CourseCreate) -> CourseResponse:
        if await self.find_by_title(in_data.title):
            raise AlreadyExistsError("Курс с таким названием уже существует")

        return await super().create(in_data)

    async def find_by_title(self, title: str, delete_flg: bool | None = None) -> CourseResponse:
        return await self.repo.get_by_title(title, delete_flg)

    async def get_by_title(self, title: str, delete_flg: bool | None = None) -> CourseResponse:
        res = await self.find_by_title(title, delete_flg)

        if res is None:
            raise NotFoundError("Курс с таким названием не найден")

        return res

    async def get_by_author(self, author_id: UUID, skip: int, limit: int):
        return await self.repo.get_by_author(author_id, skip, limit)

    async def get_by_level(self, level: str, skip: int, limit: int):
        return await self.repo.get_by_level(level, skip, limit)

    async def get_published(self, skip: int, limit: int):
        return await self.repo.get_published(skip, limit)

    async def get_with_lessons(self, course_id: UUID):
        res = await self.repo.get_with_lessons(course_id)

        if not res:
            raise NotFoundError("Курс не найден или уроки отсутствуют")

        return res

    async def count(self) -> int:
        return await self.repo.count()


    async def update(self, id: UUID, in_data: CourseUpdate) -> CourseResponse:
        existing = await self.get_by_id(id, False)

        if in_data.title and in_data.title != existing.title:
            if await self.find_by_title(in_data.title):
                raise AlreadyExistsError("Курс с таким названием уже существует")

        return await super().update(id, in_data)


    # ----------------------------
    # PUBLISH
    # ----------------------------
    async def publish(self, id: UUID):
        course = await self.get_by_id(id)

        if course.is_published:
            raise ConflictError("Курс уже опубликован")

        return await self.repo.publish(id)

    async def unpublish(self, id: UUID):
        course = await self.get_by_id(id)

        if not course.is_published:
            raise ConflictError("Курс уже скрыт")

        return await self.repo.unpublish(id)


async def get_course_service(
    repo: CourseRepository = Depends(get_course_repository)
) -> CourseService:
    return CourseService(repo)
