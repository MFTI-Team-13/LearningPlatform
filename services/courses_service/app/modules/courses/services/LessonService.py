from typing import List, Optional

from fastapi import Depends, HTTPException, status
from uuid import UUID

from .BaseService import BaseService
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.models_import import Lesson
from app.modules.courses.repositories_import import (
    LessonRepository,
    get_lesson_repository,
    CourseRepository,
    get_course_repository
)
from app.modules.courses.schemas_import import LessonCreate, LessonUpdate
from app.modules.courses.exceptions import (
    NotFoundError
)
from app.common.deps.auth import CurrentUser


class LessonService(BaseService, BaseAccessCheckerCourse):
    def __init__(self, repo: LessonRepository, course_repo: CourseRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, course_repo)
        self.repo = repo
        self.course_repo = course_repo

    async def find_course(self, user:CurrentUser, course_id: UUID, delete_flg:bool | None)  -> bool:
        course_exists = await self.course_repo.get_by_id(course_id, delete_flg=None)

        if not course_exists:
            raise NotFoundError("Курс не существует")
        if delete_flg == False and course_exists.delete_flg == True:
            raise NotFoundError("Курс не найден")

        await self.check_course_access(user, course_exists, None)

        return course_exists

    async def create_lesson(self, user:CurrentUser, in_data: LessonCreate) -> Lesson:
        await self.find_course(user, in_data.course_id, False)

        max_order = await self.repo.get_max_order_index(in_data.course_id,None)
        in_data.order_index = max_order + 1

        return await super().create(in_data.model_dump())

    async def get_by_id_lesson(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        res = await self.get_by_id(id, delete_flg)

        await self.check_course_access(user, None, res.course_id)
        return res

    async def get_by_course_id(self, user:CurrentUser, course_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> List[Lesson]:
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        await self.find_course(user, course_id, delete_flg)
        lessons = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not lessons:
            raise NotFoundError("Уроки не найдены")

        return lessons

    async def get_by_course_and_order(self, user:CurrentUser,course_id: UUID, order_index: int,delete_flg: bool | None) -> Optional[Lesson]:

        await self.find_course(user, course_id, delete_flg)
        lesson = await self.repo.get_by_course_and_order(course_id, order_index,delete_flg)

        if not lesson:
          raise NotFoundError("Урок с таким порядком не найден")

        return lesson

    async def get_by_content_type(self, user:CurrentUser, content_type,delete_flg: bool | None, skip: int, limit: int) -> List[Lesson]:
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        lessons = await self.repo.get_by_content_type(content_type,delete_flg, skip, limit)

        if not lessons:
            raise NotFoundError("Уроки не найдены")

        courses_id = set([lesson.course_id for lesson in lessons])
        allowed_courses = await self.filter_courses_access(user, None, courses_id)
        allowed_course_ids = [course.id for course in allowed_courses]

        filtered_lessons = [
          lesson for lesson in lessons
          if lesson.course_id in allowed_course_ids
        ]

        if not filtered_lessons:
            raise NotFoundError("Уроки не найдены")

        return lessons

    async def get_max_order_index(self, user:CurrentUser,course_id: UUID, delete_flg: bool | None) -> int:
        await self.find_course(user, course_id, delete_flg)

        max_index = await self.repo.get_max_order_index(course_id, delete_flg)

        if max_index == -1:
          raise NotFoundError("У данного курса нет уроков")

        return max_index

    async def search_in_course(self, user:CurrentUser, course_id: UUID, query: str, delete_flg: bool | None, skip: int, limit: int) -> List[Lesson]:
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        await self.find_course(user, course_id, delete_flg)

        lessons = await self.repo.search_in_course(course_id,query,delete_flg, skip, limit)

        if not lessons:
            raise NotFoundError("Уроки не найдены")

        return lessons

    async def update_lesson(self, user:CurrentUser, id: UUID, in_data: LessonUpdate) -> Lesson:
        await self.get_by_id_lesson(user, id, False)

        return await self.update(id, in_data)

    async def soft_delete_lesson(self, user:CurrentUser,id: UUID):
      await self.get_by_id_lesson(user, id, False)

      return await self.soft_delete(id)


async def get_lesson_service(
  repo: LessonRepository = Depends(get_lesson_repository),
  course_repo: CourseRepository = Depends(get_course_repository)
) -> LessonService:
  return LessonService(repo, course_repo)
