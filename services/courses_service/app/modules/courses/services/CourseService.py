# services/course_service.py

from fastapi import Depends, HTTPException, status
from uuid import UUID

from app.modules.courses.repositories_import import CourseRepository, get_course_repository
from app.modules.courses.schemas.CourseScheme import CourseCreate, CourseUpdate, CourseResponse
from .BaseService import BaseService


class CourseService(BaseService):
    def __init__(self, repo: CourseRepository):
        super().__init__(repo)
        self.repo: CourseRepository = repo

    async def create(self, in_data: CourseCreate) -> CourseResponse:
        if await self.exists_by_title(in_data.title):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Курс с таким названием уже существует"
            )
        return await super().create(in_data)

    async def get_by_title(self, title: str) -> CourseResponse | None:
        return await self.repo.get_by_title(title)

    async def exists_by_title(self, title: str) -> bool:
        return bool(await self.repo.exists_by_title(title))

    async def get_by_author(self, author_id: UUID, skip: int, limit: int):
        return await self.repo.get_by_author(author_id, skip, limit)

    async def get_by_level(self, level: str, skip: int, limit: int):
        return await self.repo.get_by_level(level, skip, limit)

    async def get_published(self, skip: int, limit: int):
        return await self.repo.get_published(skip, limit)

    async def get_with_lessons(self, course_id: UUID):
        res = await self.repo.get_with_lessons(course_id)

        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Курс не найден или уроки отсутствуют"
            )
        return res

    async def count(self) -> int:
        return await self.repo.count()

    async def update(self, id: UUID, in_data: CourseUpdate) -> CourseResponse:
        existing = await self.get_by_id(id)

        if in_data.title and in_data.title != existing.title:
            if await self.exists_by_title(in_data.title):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Курс с таким названием уже существует"
                )

        return await super().update(id, in_data)

    async def soft_delete(self, id: UUID):
        course = await self.get_by_id(id)

        if course.delete_flg:
            raise HTTPException(
                status_code=400,
                detail="Курс уже удалён (soft delete)"
            )

        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        await self.get_by_id(id)
        return await self.repo.hard_delete(id)

    async def publish(self, id: UUID):
        course = await self.get_by_id(id)

        if course.is_published:
            raise HTTPException(status_code=400, detail="Курс уже опубликован")

        return await self.repo.publish(id)

    async def unpublish(self, id: UUID):
        course = await self.get_by_id(id)

        if not course.is_published:
            raise HTTPException(status_code=400, detail="Курс уже скрыт")

        return await self.repo.unpublish(id)


async def get_course_service(
    repo: CourseRepository = Depends(get_course_repository)
) -> CourseService:
    return CourseService(repo)
