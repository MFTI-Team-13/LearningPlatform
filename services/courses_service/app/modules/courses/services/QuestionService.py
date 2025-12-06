from fastapi import Depends, HTTPException
from uuid import UUID

from app.modules.courses.repositories_import import QuestionRepository, get_question_repository
from app.modules.courses.schemas.QuestionScheme import QuestionCreate, QuestionUpdate
from .BaseService import BaseService


class QuestionService(BaseService):

    def __init__(self, repo: QuestionRepository):
        super().__init__(repo)
        self.repo = repo

    async def get_by_test_and_order(self, test_id: UUID, order_index: int):
        q = await self.repo.get_by_test_and_order(test_id, order_index)
        if not q:
            raise HTTPException(404, "Вопрос не найден")
        return q

    async def get_by_test_id(self, test_id: UUID, skip: int, limit: int):
        return await self.repo.get_by_test_id(test_id, skip, limit)

    async def get_by_question_type(self, question_type, skip: int, limit: int):
        return await self.repo.get_by_question_type(question_type, skip, limit)

    async def create_bulk(self, questions: list[QuestionCreate]):
        return await self.repo.create_bulk([q.model_dump() for q in questions])

    async def get_max_order_index(self, test_id: UUID):
        return await self.repo.get_max_order_index(test_id)

    async def reorder_questions(self, test_id: UUID, new_order: list[UUID]):
        return await self.repo.reorder_questions(test_id, new_order)

    async def search_in_test(self, test_id: UUID, query: str, skip: int, limit: int):
        return await self.repo.search_in_test(test_id, query, skip, limit)

    async def count_by_test(self, test_id: UUID):
        return await self.repo.count_by_test(test_id)

    async def get_total_score_by_test(self, test_id: UUID):
        return await self.repo.get_total_score_by_test(test_id)

    async def get_with_answers(self, id: UUID):
        res = await self.repo.get_with_answers(id)
        if not res:
            raise HTTPException(404, "Вопрос или ответы не найдены")
        return res

    async def soft_delete(self, id: UUID):
        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        return await self.repo.hard_delete(id)


async def get_question_service(
    repo: QuestionRepository = Depends(get_question_repository)
) -> QuestionService:
    return QuestionService(repo)
