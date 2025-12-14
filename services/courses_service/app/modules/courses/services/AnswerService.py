from uuid import UUID

from fastapi import Depends

from app.modules.courses.exceptions import ConflictError, NotFoundError
from app.modules.courses.models_import import Answer
from app.modules.courses.repositories_import import (
    AnswerRepository,
    QuestionRepository,
    get_answer_repository,
    get_question_repository,
)
from app.modules.courses.schemas_import import AnswerCreate

from .BaseService import BaseService


class AnswerService(BaseService):
    def __init__(self, repo: AnswerRepository, question_repo: QuestionRepository):
        super().__init__(repo)
        self.repo = repo
        self.question_repo = question_repo

    async def find_question(self, question_id: UUID, delete_flg:bool | None)  -> bool:
        question_exists = await self.question_repo.get_by_id(question_id, delete_flg=None)

        if not question_exists:
            raise NotFoundError("Вопрос для ответа не найден")
        if delete_flg == False and question_exists.delete_flg == True:
            raise NotFoundError("Вопрос не найден")

        return True

    async def create(self, in_data: AnswerCreate) -> Answer:
        await self.find_question(in_data.question_id, delete_flg=False)
        return await super().create(in_data)

    async def get_by_question_and_order(self, question_id: UUID, order_index: int, delete_flg: bool | None) -> Answer | None:
        await self.find_question(question_id, delete_flg)
        answer = await self.repo.get_by_question_and_order(question_id, order_index,delete_flg)

        if not answer:
          raise NotFoundError("Ответ с таким порядком не найден")

        return answer

    async def get_by_question_id(self, question_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> list[Answer]:
        await self.find_question(question_id, delete_flg)
        answers = await self.repo.get_by_question_id(question_id, delete_flg, skip, limit)

        if not answers:
            raise NotFoundError("Ответы не найдены")

        return answers

    async def get_correct_answers_by_question(self, question_id: UUID,is_correct: bool | None, delete_flg:bool | None,skip: int = 0, limit: int = 100) -> list[Answer]:
        await self.find_question(question_id, delete_flg)
        res =  await self.repo.get_correct_answers_by_question(question_id, is_correct, delete_flg, skip, limit)

        if not res:
          raise NotFoundError("Ответы не найдены")

        return res

    async def get_max_order_index(self, question_id: UUID, delete_flg: bool | None) -> int:
        await self.find_question(question_id, delete_flg)

        max_index = await self.repo.get_max_order_index(question_id, delete_flg)

        if max_index == -1:
          raise NotFoundError("У данного вопроса нет ответов")

        return max_index


    async def create_bulk(self, answers: list[AnswerCreate]) -> list[Answer]:
      if not answers:
        raise ConflictError("Список ответов пуст")

      question_id = answers[0].question_id
      await self.find_question(question_id, False)

      return await self.repo.create_bulk([a.model_dump() for a in answers])


    async def count_by_question(self, question_id: UUID, delete_flg: bool | None) -> int:
        await self.find_question(question_id, delete_flg)
        res = await self.repo.count_by_question(question_id, delete_flg)

        if res == 0:
          raise NotFoundError("Ответы не найдены")

        return res


async def get_answer_service(
    repo: AnswerRepository = Depends(get_answer_repository),
    question_repo: QuestionRepository = Depends(get_question_repository)
) -> AnswerService:
    return AnswerService(repo, question_repo)
