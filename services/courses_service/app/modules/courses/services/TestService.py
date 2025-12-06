from fastapi import Depends, HTTPException
from uuid import UUID

from app.modules.courses.repositories_import import TestRepository, get_test_repository
from app.modules.courses.schemas.TestScheme import TestCreate, TestUpdate
from .BaseService import BaseService


class TestService(BaseService):

    def __init__(self, repo: TestRepository):
        super().__init__(repo)
        self.repo = repo

    async def create(self, in_data: TestCreate):
        return await super().create(in_data)

    async def get_by_lesson_id(self, lesson_id: UUID, skip: int, limit: int):
        return await self.repo.get_by_lesson_id(lesson_id, skip, limit)

    async def get_all_active(self, skip: int, limit: int):
        return await self.repo.get_all_active(skip, limit)

    async def get_by_course_id(self, course_id: UUID, skip: int, limit: int):
        return await self.repo.get_by_course_id(course_id, skip, limit)

    async def search(self, query: str, skip: int, limit: int):
        return await self.repo.search(query, skip, limit)

    async def count_active_by_course(self, course_id: UUID):
        return await self.repo.count_active_by_course(course_id)

    async def get_with_questions(self, test_id: UUID):
        res = await self.repo.get_with_questions(test_id)
        if not res:
            raise HTTPException(404, "Тест или вопросы не найдены")
        return res

    async def activate(self, id: UUID):
        test = await self.get_by_id(id)
        if test.is_active:
            raise HTTPException(400, "Тест уже активен")
        return await self.repo.activate(id)

    async def deactivate(self, id: UUID):
        test = await self.get_by_id(id)
        if not test.is_active:
            raise HTTPException(400, "Тест уже не активен")
        return await self.repo.deactivate(id)

    async def soft_delete(self, id: UUID):
        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        return await self.repo.hard_delete(id)


async def get_test_service(
    repo: TestRepository = Depends(get_test_repository)
) -> TestService:
    return TestService(repo)
