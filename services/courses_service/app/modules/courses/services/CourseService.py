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

    async def get_by_author(self, author_id: UUID,delete_flg:bool, skip: int, limit: int):
        res = await self.repo.get_by_author(author_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Объекты не найдены")

        return res

    async def get_by_level(self, level: str,delete_flg:bool,skip: int, limit: int):
        res = await self.repo.get_by_level(level,delete_flg, skip, limit)

        if not res:
          raise NotFoundError(f"Объекты уровня '{level}' не найдены")

        return res

    async def get_published(self, delete_flg:bool, skip: int, limit: int):
        res = await self.repo.get_published(delete_flg, skip, limit)

        if not res:
          raise NotFoundError("Опубликованные объекты не найдены")

        return res


    async def update(self, id: UUID, in_data: CourseUpdate) -> CourseResponse:
        existing = await self.get_by_id(id, False)

        if in_data.title and in_data.title != existing.title:
            if await self.find_by_title(in_data.title):
                raise AlreadyExistsError("Курс с таким названием уже существует")

        return await super().update(id, in_data)

    async def publish(self, id: UUID):
        course = await self.get_by_id(id,None)

        if course.delete_flg:
          raise ConflictError("Нельзя опубликовать удалённый курс")

        if course.is_published:
            raise ConflictError("Курс уже опубликован")

        return await self.repo.publish(id)

    async def unpublish(self, id: UUID):
        course = await self.get_by_id(id,None)

        if not course.is_published:
            raise ConflictError("Курс уже скрыт")

        return await self.repo.unpublish(id)

    async def soft_delete(self, id: UUID):
      course = await self.get_by_id(id, delete_flg=False)

      if course.is_published:
        await self.repo.unpublish(id)

      return await super().soft_delete(id)

    async def get_all_with_lessons(self, delete_flg: bool | None, skip: int, limit: int):
      courses = await self.repo.get_all_with_lessons(delete_flg, skip, limit)

      if not courses:
        raise NotFoundError("Курсы не найдены")

      return courses




async def get_course_service(
    repo: CourseRepository = Depends(get_course_repository)
) -> CourseService:
    return CourseService(repo)
