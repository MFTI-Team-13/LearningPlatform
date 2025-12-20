from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_session
from app.modules.courses.models.Answer import Answer
from app.modules.courses.models.Course import Course
from app.modules.courses.models.CourseUser import CourseUser
from app.modules.courses.models.Lesson import Lesson
from app.modules.courses.models.Question import Question
from app.modules.courses.models.Test import Test

class AnswerRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create(self, answer_data: dict) -> Answer:
    answer = Answer(**answer_data)
    self.db.add(answer)
    await self.db.commit()
    await self.db.refresh(answer)
    return answer

  async def create_bulk(self, answers_data: list[dict]) -> list[Answer]:
    answers = [Answer(**data) for data in answers_data]
    self.db.add_all(answers)
    await self.db.commit()

    for answer in answers:
      await self.db.refresh(answer)

    return answers

  async def get_by_id(self, id: UUID, delete_flg: bool) -> Answer | None:
    query = select(Answer).where(Answer.id == id)

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    result = await self.db.execute(query)

    return result.scalar_one_or_none()

  async def get_by_question_id(
    self, question_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100
  ) -> list[Answer]:
    query = select(Answer).where(Answer.question_id == question_id)

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    query = query.offset(skip).limit(limit)

    result = await self.db.execute(query)
    return result.scalars().all()

  async def get_by_question_and_order(
    self, question_id: UUID, order_index: int, delete_flg: bool | None
  ) -> Answer | None:
    query = select(Answer).where(
      and_(Answer.question_id == question_id, Answer.order_index == order_index)
    )

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def get_all(self, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> list[Answer]:
    query = select(Answer)

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    query = query.offset(skip).limit(limit)

    result = await self.db.execute(query)
    return result.scalars().all()

  async def get_correct_answers_by_question(
    self,
    question_id: UUID,
    is_correct: bool | None,
    delete_flg: bool | None,
    skip: int = 0,
    limit: int = 100,
  ) -> list[Answer]:
    query = select(Answer).where(Answer.question_id == question_id)

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    if is_correct is not None:
      query = query.where(Answer.is_correct == is_correct)

    query = query.offset(skip).limit(limit)

    result = await self.db.execute(query)
    return result.scalars().all()

  async def update(self, answer_id: UUID, answer_data: dict) -> Answer | None:
    answer = await self.get_by_id(answer_id, False)

    if not answer:
      return None

    for key, value in answer_data.items():
      if hasattr(answer, key):
        setattr(answer, key, value)

    answer.update_at = datetime.utcnow()
    await self.db.commit()
    await self.db.refresh(answer)
    return answer

  async def soft_delete(self, answer_id: UUID) -> bool:
    answer = await self.get_by_id(answer_id, False)

    if not answer:
      return False

    answer.delete_flg = True
    answer.update_at = datetime.utcnow()
    await self.db.commit()
    return True

  async def hard_delete(self, answer_id: UUID) -> bool:
    answer = await self.get_by_id(answer_id, None)

    if not answer:
      return False

    await self.db.delete(answer)
    await self.db.commit()
    return True

  async def get_assigned_to_create_by_user(self, user_id: UUID, question_id: UUID, type: str):
    query = (
      select(Question)
      .join(Test, Test.id == Question.test_id)
      .join(Lesson, Lesson.id == Test.lesson_id)
      .join(Course, Course.id == Lesson.course_id)
      .where(
        and_(
          Course.delete_flg.is_(False),
          Course.is_published.is_(True),
          Lesson.delete_flg.is_(False),
          Test.is_active.is_(True),
          Test.delete_flg.is_(False),
          Question.delete_flg.is_(False),
          Question.id == question_id,
        )
      )
    )

    query = await self.subquery(query, user_id, type)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def subquery(self, query, user_id: UUID, type: str):
    if type == "teacher":
      query = query.where(Course.author_id == user_id)
    else:
      query = query.join(CourseUser, CourseUser.course_id == Course.id).where(
        and_(
          CourseUser.user_id == user_id,
          CourseUser.is_active == True,
          CourseUser.delete_flg == False,
        )
      )
    return query

  async def get_assigned_to_user(self, user_id: UUID, answer_id: UUID, type: str):
    query = (
      select(Answer)
      .join(Question, Question.id == Answer.question_id)
      .join(Test, Test.id == Question.test_id)
      .join(Lesson, Lesson.id == Test.lesson_id)
      .join(Course, Course.id == Lesson.course_id)
      .where(
        and_(
          Course.delete_flg == False,
          Course.is_published == True,
          Lesson.delete_flg == False,
          Test.is_active == True,
          Test.delete_flg == False,
          Question.delete_flg == False,
          Answer.id == answer_id,
          Answer.delete_flg == False,
        )
      )
    )

    query = await self.subquery(query, user_id, type)
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def count_by_question(self, question_id: UUID, delete_flg: bool | None) -> int:
    query = select(func.count(Answer.id)).where(Answer.question_id == question_id)

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    result = await self.db.execute(query)
    return result.scalar()

  async def get_max_order_index(self, question_id: UUID, delete_flg: bool | None) -> int:
    query = select(func.max(Answer.order_index)).where(Answer.question_id == question_id)

    if delete_flg is not None:
      query = query.where(Answer.delete_flg == delete_flg)

    result = await self.db.execute(query)
    max_order = result.scalar()
    return max_order if max_order is not None else -1


async def get_answer_repository(
  db: AsyncSession = Depends(get_session),
) -> AnswerRepository:
  return AnswerRepository(db)
