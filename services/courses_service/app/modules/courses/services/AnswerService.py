from fastapi import Depends, HTTPException
from uuid import UUID

from app.modules.courses.repositories_import import AnswerRepository, get_answer_repository
from app.modules.courses.schemas_import import AnswerCreate, AnswerUpdate
from .BaseService import BaseService


class AnswerService(BaseService):

    def __init__(self, repo: AnswerRepository):
        super().__init__(repo)
        self.repo = repo

    async def get_by_question_and_order(self, question_id: UUID, order_index: int):
        res = await self.repo.get_by_question_and_order(question_id, order_index)
        if not res:
            raise HTTPException(404, "Ответ не найден")
        return res

    async def get_by_question_id(self, question_id: UUID):
        return await self.repo.get_by_question_id(question_id)

    async def get_correct_answers_by_question(self, question_id: UUID):
        return await self.repo.get_correct_answers_by_question(question_id)

    async def create_bulk(self, answers: list[AnswerCreate]):
        return await self.repo.create_bulk([a.model_dump() for a in answers])

    async def get_max_order_index(self, question_id: UUID):
        return await self.repo.get_max_order_index(question_id)

    async def reorder_answers(self, question_id: UUID, new_order: list[UUID]):
        return await self.repo.reorder_answers(question_id, new_order)

    async def count_by_question(self, question_id: UUID):
        return await self.repo.count_by_question(question_id)

    async def count_correct_answers_by_question(self, question_id: UUID):
        return await self.repo.count_correct_answers_by_question(question_id)

    async def soft_delete(self, id: UUID):
        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        return await self.repo.hard_delete(id)


async def get_answer_service(
    repo: AnswerRepository = Depends(get_answer_repository)
) -> AnswerService:
    return AnswerService(repo)
