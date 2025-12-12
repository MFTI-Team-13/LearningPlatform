from typing import List, Optional

from fastapi import Depends, HTTPException, status
from uuid import UUID

from .BaseService import BaseService
from app.modules.courses.models_import import Lesson
from app.modules.courses.repositories_import import (
    LessonRepository,
    get_lesson_repository,
    CourseRepository,
    get_course_repository
)
from app.modules.courses.schemas_import import LessonCreate
from app.modules.courses.exceptions import (
    NotFoundError
)


class LessonService(BaseService):
    def __init__(self, repo: LessonRepository, course_repo: CourseRepository):
        super().__init__(repo)
        self.repo = repo
        self.course_repo = course_repo

    async def find_course(self, course_id: UUID, delete_flg:bool | None)  -> bool:
        course_exists = await self.course_repo.get_by_id(course_id, delete_flg=None)

        if not course_exists:
            raise NotFoundError("Курс не существует")
        if delete_flg == False and course_exists.delete_flg == True:
            raise NotFoundError("Курс не найден")

        return True

    async def create(self, in_data: LessonCreate) -> Lesson:
        await self.find_course(in_data.course_id, False)

        max_order = await self.repo.get_max_order_index(in_data.course_id,None)
        in_data.order_index = max_order + 1

        return await super().create(in_data)

    async def get_by_course_id(self, course_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> List[Lesson]:
        await self.find_course(course_id, delete_flg)
        lessons = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not lessons:
            raise NotFoundError("Уроки не найдены")

        return lessons

    async def get_by_course_and_order(self, course_id: UUID, order_index: int,delete_flg: bool | None) -> Optional[Lesson]:
        await self.find_course(course_id, delete_flg)
        lesson = await self.repo.get_by_course_and_order(course_id, order_index,delete_flg)

        if not lesson:
          raise NotFoundError("Урок с таким порядком не найден")

        return lesson

    async def get_by_content_type(self, content_type,delete_flg: bool | None, skip: int, limit: int) -> List[Lesson]:
        lessons = await self.repo.get_by_content_type(content_type,delete_flg, skip, limit)

        if not lessons:
            raise NotFoundError("Уроки не найдены")

        return lessons

    async def get_max_order_index(self, course_id: UUID, delete_flg: bool | None) -> int:
        await self.find_course(course_id, delete_flg)

        max_index = await self.repo.get_max_order_index(course_id, delete_flg)

        if max_index == -1:
          raise NotFoundError("У данного курса нет уроков")

        return max_index

    async def search_in_course(self, course_id: UUID, query: str, delete_flg: bool | None, skip: int, limit: int) -> List[Lesson]:
        await self.find_course(course_id, delete_flg)
        lessons = await self.repo.search_in_course(course_id,query,delete_flg, skip, limit)

        if not lessons:
            raise NotFoundError("Уроки не найдены")

        return lessons


async def get_lesson_service(
  repo: LessonRepository = Depends(get_lesson_repository),
  course_repo: CourseRepository = Depends(get_course_repository)
) -> LessonService:
  return LessonService(repo, course_repo)
