from typing import Optional, List

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from app.modules.courses.models_import import Answer
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.repositories_import import (
    AnswerRepository,
    get_answer_repository,
    QuestionRepository,
    get_question_repository
)
from app.modules.courses.schemas_import import AnswerCreate,AnswerUpdate
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)
from app.common.deps.auth import CurrentUser


class AnswerService(BaseService,BaseAccessCheckerCourse):
    def __init__(self, repo: AnswerRepository, question_repo: QuestionRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, repo)
        self.repo = repo
        self.question_repo = question_repo

    async def find_question(self, question_id: UUID, delete_flg:bool | None)  -> bool:
        question_exists = await self.question_repo.get_by_id(question_id, delete_flg=None)

        if not question_exists:
            raise NotFoundError("Вопрос для ответа не найден")
        if delete_flg == False and question_exists.delete_flg == True:
            raise NotFoundError("Вопрос не найден")

        return question_exists

    async def create_answer(self, user:CurrentUser, in_data: AnswerCreate) -> Answer:
        await self.find_question(in_data.question_id, delete_flg=False)
        await self.check_course_access_to_create(user,in_data.question_id)

        return await super().create(in_data.model_dump())

    async def get_by_id_answer(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        res = await self.get_by_id(id, delete_flg)

        await self.check_course_access(user, res, None)
        return res

    async def get_by_question_and_order(self, question_id: UUID, order_index: int, delete_flg: bool | None) -> Optional[Answer]:
        await self.find_question(question_id, delete_flg)
        answer = await self.repo.get_by_question_and_order(question_id, order_index,delete_flg)

        if not answer:
          raise NotFoundError("Ответ с таким порядком не найден")

        return answer

    async def get_by_question_id(self, user:CurrentUser, question_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> List[Answer]:
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        await self.find_question(question_id, delete_flg)
        answers = await self.repo.get_by_question_id(question_id, delete_flg, skip, limit)

        if not answers:
            raise NotFoundError("Ответы не найдены")

        answers = await self.filter_courses_access(user, answers, None)

        if not answers:
            raise NotFoundError("Тесты не найдены")

        return answers

    async def get_correct_answers_by_question(self, user:CurrentUser,question_id: UUID,is_correct: bool | None, delete_flg:bool | None,skip: int = 0, limit: int = 100) -> List[Answer]:
        if "teacher" in user.roles:
            delete_flg = False

        await self.find_question(question_id, delete_flg)
        res =  await self.repo.get_correct_answers_by_question(question_id, is_correct, delete_flg, skip, limit)

        if not res:
          raise NotFoundError(f"Ответы не найдены")

        answers = await self.filter_courses_access(user, res, None)

        if not answers:
          raise NotFoundError("Ответы не найдены")

        return res

    async def get_max_order_index(self, question_id: UUID, delete_flg: bool | None) -> int:
        await self.find_question(question_id, delete_flg)

        max_index = await self.repo.get_max_order_index(question_id, delete_flg)

        if max_index == -1:
          raise NotFoundError("У данного вопроса нет ответов")

        return max_index

    async def update_answer(self, user:CurrentUser, id: UUID, in_data: AnswerUpdate) -> Answer:
        answer = await self.get_by_id(id, False)
        await self.check_course_access(user, answer, None)

        return await self.update(id, in_data)

    async def soft_delete_answer(self, user:CurrentUser, id: UUID) -> bool:
        answer = await self.get_by_id(id, None)
        await self.check_course_access(user, answer, None)

        return await super().soft_delete(id)


    async def create_bulk(self, user:CurrentUser, answers: list[AnswerCreate]) -> List[Answer]:
      if not answers:
        raise ConflictError("Список ответов пуст")

      question_id = answers[0].question_id

      if any(a.question_id != question_id for a in answers):
        raise ConflictError("Все ответы должны относиться к одному вопросу")

      await self.find_question(question_id, False)
      await self.check_course_access_to_create(user, question_id)

      return await self.repo.create_bulk([a.model_dump() for a in answers])


    async def count_by_question(self, question_id: UUID, delete_flg: bool | None) -> int:
        await self.find_question(question_id, delete_flg)
        res = await self.repo.count_by_question(question_id, delete_flg)

        if res == 0:
          raise NotFoundError(f"Ответы не найдены")

        return res


async def get_answer_service(
    repo: AnswerRepository = Depends(get_answer_repository),
    question_repo: QuestionRepository = Depends(get_question_repository)
) -> AnswerService:
    return AnswerService(repo, question_repo)
