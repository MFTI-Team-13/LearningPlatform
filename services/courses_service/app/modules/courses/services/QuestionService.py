from typing import List, Optional

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.models_import import Question
from app.modules.courses.repositories_import import (
    QuestionRepository,
    get_question_repository,
    TestRepository,
    get_test_repository
)
from app.modules.courses.schemas.QuestionScheme import QuestionCreate,QuestionUpdate
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)
from app.common.deps.auth import CurrentUser


class QuestionService(BaseService, BaseAccessCheckerCourse):

    def __init__(self, repo: QuestionRepository, test_repo: TestRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, test_repo)
        self.repo = repo
        self.test_repo = test_repo

    async def find_test(self, user:CurrentUser, test_id: UUID, delete_flg:bool | None)  -> bool:
        test_exists = await self.test_repo.get_by_id(test_id, delete_flg=None)

        if not test_exists:
            raise NotFoundError("Тест не существует")
        if delete_flg == False and test_exists.delete_flg == True:
            raise NotFoundError("Тест не найден")

        await self.check_course_access(user, test_exists, None)

        return True

    async def create_question(self, user:CurrentUser, in_data: QuestionCreate) -> Question:
        await self.find_test(user, in_data.test_id, False)

        max_order = await self.repo.get_max_order_index(in_data.test_id,None)
        in_data.order_index = max_order + 1

        return await super().create(in_data.model_dump())

    async def get_by_id_question(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        res = await self.get_by_id(id, delete_flg)

        await self.check_course_access(user, None, res.test_id)
        return res

    async def get_by_test_id(self, user:CurrentUser, test_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> List[Question]:
        if "student" in user.roles or "teacher" in user.roles:
            delete_flg = False

        await self.find_test(user, test_id, delete_flg)

        question = await self.repo.get_by_test_id(test_id, delete_flg, skip, limit)

        if not question:
            raise NotFoundError("Вопросы не найдены")

        return question

    async def get_by_test_and_order(self, user:CurrentUser, test_id: UUID, order_index: int,delete_flg: bool | None) -> Optional[Question]:
        await self.find_test(user, test_id, delete_flg)
        question = await self.repo.get_by_test_and_order(test_id, order_index,delete_flg)

        if not question:
          raise NotFoundError("Вопрос с таким порядком не найден")

        return question

    async def get_by_question_type(self, question_type,delete_flg: bool, skip: int, limit: int) -> List[Question]:
        question = await self.repo.get_by_question_type(question_type,delete_flg, skip, limit)

        if not question:
            raise NotFoundError("Вопросы не найдены")

        return question

    async def get_max_order_index(self, user:CurrentUser, test_id: UUID, delete_flg: bool | None) -> int:
        await self.find_test(user, test_id, delete_flg)

        max_index = await self.repo.get_max_order_index(test_id, delete_flg)

        if max_index == -1:
          raise NotFoundError("У теста курса нет вопросов")

        return max_index

    async def search_in_test(self, user:CurrentUser, test_id: UUID, query: str,delete_flg: bool | None, skip: int, limit: int) -> List[Question]:

        await self.find_test(user, test_id, delete_flg)
        questions = await self.repo.search_in_test(test_id,query,delete_flg, skip, limit)

        if not questions:
            raise NotFoundError("Вопросы не найдены")

        return questions

    async def create_bulk(self, user:CurrentUser,questions: list[QuestionCreate]) -> List[Question]:
        if not questions:
            raise ConflictError("Список вопросов пуст")

        test_id = questions[0].test_id

        if any(q.test_id != test_id for q in questions):
          raise ConflictError("Все вопросы должны относиться к одному тесту")

        await self.find_test(user, test_id, False)

        return await self.repo.create_bulk([q.model_dump() for q in questions])

    async def get_total_score_by_test(self, user:CurrentUser,test_id: UUID, delete_flg: bool | None ) -> int:
        if "student" in user.roles or "teacher" in user.roles:
            delete_flg = False
        await self.find_test(user, test_id, delete_flg)
        result = await self.repo.get_total_score_by_test(test_id,delete_flg)

        if result == -1:
            raise NotFoundError("Вопросы не найдены")

        return result

    async def get_with_answers(self, id: UUID):
        res = await self.repo.get_with_answers(id)
        if not res:
            raise HTTPException(404, "Вопрос или ответы не найдены")
        return res

    async def update_question(self, user:CurrentUser, id: UUID, in_data: QuestionUpdate) -> Question:
        await self.get_by_id_question(user, id, False)

        return await self.update(id, in_data)

    async def soft_delete_question(self, user:CurrentUser,id: UUID):
      await self.get_by_id_question(user, id, False)

      return await self.soft_delete(id)



async def get_question_service(
    repo: QuestionRepository = Depends(get_question_repository),
    test_repo: TestRepository = Depends(get_test_repository)
) -> QuestionService:
    return QuestionService(repo,test_repo)
