from typing import List, Optional

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from app.modules.courses.models_import import Test
from app.modules.courses.repositories_import import (
    TestRepository,
    get_test_repository,
    LessonRepository,
    get_lesson_repository
)
from app.modules.courses.schemas.TestScheme import TestCreate
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)

class TestService(BaseService):
    def __init__(self, repo: TestRepository, lesson_repo: LessonRepository):
        super().__init__(repo)
        self.repo = repo
        self.lesson_repo = lesson_repo

    async def find_lesson(self, lesson_id: UUID, delete_flg:bool | None)  -> bool:
        lesson_exists = await self.lesson_repo.get_by_id(lesson_id, delete_flg=None)

        if not lesson_exists:
            raise NotFoundError("Урок не существует")
        if delete_flg == False and lesson_exists.delete_flg == True:
            raise NotFoundError("Урок не найден")

        return True

    async def create(self, in_data: TestCreate) -> Test:
        await self.find_lesson(in_data.lesson_id, False)
        return await super().create(in_data)

    async def get_by_lesson_id(self, lesson_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> List[Test]:
        await self.find_lesson(lesson_id, delete_flg)
        tests = await self.repo.get_by_lesson_id(lesson_id, delete_flg, skip, limit)

        if not tests:
            raise NotFoundError("Тесты не найдены")

        return tests

    async def activate(self, id: UUID) -> Optional[Test]:
        test = await self.get_by_id(id, None)

        if test.delete_flg:
          raise ConflictError("Нельзя активировать удалённый тест")

        if test.is_active:
            raise ConflictError("Тест уже активен")

        return await self.repo.activate(id)

    async def deactivate(self, id: UUID) -> Optional[Test]:
        test = await self.get_by_id(id, None)

        if not test.is_active:
          raise ConflictError("Тест уже скрыт")

        return await self.repo.deactivate(id)

    async def soft_delete(self, id: UUID) -> bool:
        test = await self.get_by_id(id, None)

        if test.is_active:
          await self.repo.deactivate(id)

        return await super().soft_delete(id)



    async def get_all_active(self,  delete_flg: bool | None, skip: int, limit: int) -> List[Test]:
        res = await self.repo.get_all_active(delete_flg,skip, limit)

        if not res:
          raise NotFoundError("Активные объекты не найдены")

        return res



    async def get_by_course_id(self, course_id: UUID, delete_flg:bool | None, skip: int, limit: int) -> List[Test]:
        res = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError("Тесты не найдены для данного курса")

        return res

    async def search(self, query: str, delete_flg:bool|None,skip: int, limit: int) -> List[Test]:
        res = await self.repo.search(query,delete_flg, skip, limit)

        if not res:
            raise NotFoundError("Тесты не найдены")

        return res


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
