from fastapi import Depends, HTTPException
from uuid import UUID

from app.modules.courses.repositories_import import QuestionRepository, get_question_repository,TestRepository, get_test_repository
from app.modules.courses.schemas.QuestionScheme import QuestionCreate, QuestionUpdate,QuestionResponse
from .BaseService import BaseService
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)


class QuestionService(BaseService):

    def __init__(self, repo: QuestionRepository, test_repo: TestRepository):
        super().__init__(repo)
        self.repo = repo
        self.test_repo = test_repo

    async def create(self, in_data: QuestionCreate) -> QuestionResponse:
        test = await self.test_repo.get_by_id(in_data.test_id, delete_flg=False)
        if not test:
            raise NotFoundError("Тест для вопроса не найден")

        max_order = await self.repo.get_max_order_index(in_data.test_id,None)
        in_data.order_index = max_order + 1

        return await super().create(in_data)

    async def get_by_test_id(self, test_id: UUID, delete_flg: bool | None, skip: int, limit: int):
        question = await self.repo.get_by_test_id(test_id, delete_flg, skip, limit)

        if not question:
            raise NotFoundError("Вопросы не найдены")

        return question

    async def get_by_test_and_order(self, test_id: UUID, order_index: int,delete_flg: bool | None):
        question = await self.repo.get_by_test_and_order(test_id, order_index,delete_flg)

        if not question:
          raise NotFoundError("Вопрос с таким порядком не найден")

        return question

    async def get_by_question_type(self, question_type,delete_flg: bool, skip: int, limit: int):
        question = await self.repo.get_by_question_type(question_type,delete_flg, skip, limit)

        if not question:
            raise NotFoundError("Вопросы не найдены")

        return question

    async def get_max_order_index(self, test_id: UUID, delete_flg: bool | None) -> int:
        course = await self.test_repo.get_by_id(test_id, delete_flg=None)
        if not course:
           raise NotFoundError("Вопрос не найден")

        max_index = await self.repo.get_max_order_index(test_id, delete_flg)

        if max_index == -1:
          raise NotFoundError("У данного курса нет уроков")

        return max_index

    async def search_in_test(self, test_id: UUID, query: str,delete_flg: bool | None, skip: int, limit: int):
        questions = await self.repo.search_in_test(test_id,query,delete_flg, skip, limit)

        if not questions:
            raise NotFoundError("Вопросы не найдены")

        return questions

    async def create_bulk(self, questions: list[QuestionCreate]):
      if not questions:
        raise ConflictError("Список вопросов пуст")

      test_id = questions[0].test_id
      test = await self.test_repo.get_by_id(test_id, delete_flg=False)

      if not test:
        raise NotFoundError("Тест для добавления вопросов не найден")

      return await self.repo.create_bulk([q.model_dump() for q in questions])

    async def get_total_score_by_test(self, test_id: UUID, delete_flg: bool | None ):
        result = await self.repo.get_total_score_by_test(test_id,delete_flg)

        if result == -1:
            raise NotFoundError("Вопросы не найдены")

        return result

    async def get_with_answers(self, id: UUID):
        res = await self.repo.get_with_answers(id)
        if not res:
            raise HTTPException(404, "Вопрос или ответы не найдены")
        return res



async def get_question_service(
    repo: QuestionRepository = Depends(get_question_repository),
    test_repo: TestRepository = Depends(get_test_repository)
) -> QuestionService:
    return QuestionService(repo,test_repo)
