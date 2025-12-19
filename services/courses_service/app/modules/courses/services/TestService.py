from typing import List, Optional

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.models_import import Test
from app.modules.courses.repositories_import import (
    TestRepository,
    get_test_repository,
    LessonRepository,
    get_lesson_repository
)
from app.modules.courses.schemas.TestScheme import TestCreate,TestUpdate
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)
from app.common.deps.auth import CurrentUser

class TestService(BaseService,BaseAccessCheckerCourse):
    def __init__(self, repo: TestRepository, lesson_repo: LessonRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, repo)
        self.repo = repo
        self.lesson_repo = lesson_repo

    async def find_lesson(self, lesson_id: UUID, delete_flg:bool | None)  -> bool:
        lesson_exists = await self.lesson_repo.get_by_id(lesson_id, delete_flg=None)

        if not lesson_exists:
            raise NotFoundError("Урок не существует")
        if delete_flg == False and lesson_exists.delete_flg == True:
            raise NotFoundError("Урок не найден")

        return True

    async def create_test(self, user:CurrentUser, in_data: TestCreate) -> Test:
        await self.find_lesson(in_data.lesson_id, False)
        await self.check_course_access_to_create(user,in_data.lesson_id)

        return await super().create(in_data.model_dump())

    async def get_by_id_test(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        res = await self.get_by_id(id, delete_flg)

        await self.check_course_access(user, res, None)
        return res
    async def get_by_lesson_id(self,user:CurrentUser, lesson_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> List[Test]:
        await self.find_lesson(lesson_id, delete_flg)
        tests = await self.repo.get_by_lesson_id(lesson_id, delete_flg, skip, limit)

        if not tests:
            raise NotFoundError("Тесты не найдены")

        tests = await self.filter_courses_access(user, tests, None)

        if not tests:
            raise NotFoundError("Тесты не найдены")

        return tests

    async def activate(self, user:CurrentUser, id: UUID) -> Optional[Test]:
        test = await self.get_by_id(id, None)
        await self.check_course_access(user, test, None)

        if test.delete_flg:
          raise ConflictError("Нельзя активировать удалённый тест")

        if test.is_active:
            raise ConflictError("Тест уже активен")

        return await self.repo.activate(id)

    async def deactivate(self, user:CurrentUser,id: UUID) -> Optional[Test]:
        test = await self.get_by_id(id, None)
        await self.check_course_access(user, test, None)

        if not test.is_active:
          raise ConflictError("Тест уже скрыт")

        return await self.repo.deactivate(id)

    async def update_test(self, user:CurrentUser, id: UUID, in_data: TestUpdate) -> Test:

        await self.check_course_access(user, None, id)
        return await self.update(id, in_data)

    async def soft_delete_test(self, user:CurrentUser, id: UUID) -> bool:
        test = await self.get_by_id(id, None)
        await self.check_course_access(user, test, None)

        if test.is_active:
          await self.repo.deactivate(id)

        return await super().soft_delete(id)



    async def get_all_active(self,  user:CurrentUser, delete_flg: bool | None, skip: int, limit: int) -> List[Test]:
        res = await self.repo.get_all_active(delete_flg,skip, limit)

        if not res:
          raise NotFoundError("Активные тесты не найдены")

        tests = await self.filter_courses_access(user, res, None)

        if not tests:
          raise NotFoundError("Тесты не найдены")

        return tests



    async def get_by_course_id(self, user:CurrentUser, course_id: UUID, delete_flg:bool | None, skip: int, limit: int) -> List[Test]:
        res = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError("Тесты не найдены для данного курса")

        tests = await self.filter_courses_access(user, res, None)

        if not tests:
          raise NotFoundError("Тесты не найдены")

        return tests


    async def get_with_questions(self, test_id: UUID):
        res = await self.repo.get_with_questions(test_id)
        if not res:
            raise HTTPException(404, "Тест или вопросы не найдены")
        return res


async def get_test_service(
    repo: TestRepository = Depends(get_test_repository),
    lesson_repo: LessonRepository = Depends(get_lesson_repository)
) -> TestService:
    return TestService(repo,lesson_repo)
