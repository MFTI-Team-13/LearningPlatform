from datetime import datetime
from uuid import UUID
from typing import Dict, Type

from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.courses.models_import import *


class CascadeDeleteRepository:
  def __init__(self, db: AsyncSession):
    self.db = db
    self.course_dependencies: Dict[Type, object] = {
      CourseUser: CourseUser.course_id,
      CourseReview: CourseReview.course_id,
      Lesson: Lesson.course_id,
    }
    self.lesson_dependencies: Dict[Type, object] = {
      Test: Test.lesson_id,
    }
    self.test_dependencies: Dict[Type, object] = {
      Question: Question.test_id,
    }
    self.question_dependencies: Dict[Type, object] = {
      Answer: Answer.question_id,
    }

  async def _soft_delete_by_id(
        self,
        model: Type,
        obj_id: UUID,
        delete_flg: bool = True,
    ):
        stmt = (
            update(model)
            .where(model.id == obj_id)
            .values(
                delete_flg=delete_flg,
                update_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)

  async def _soft_delete_by_fk(
    self,
    model,
    fk_column,
    fk_id: UUID,
    delete_flg: bool = True
  ):
    stmt = (
      update(model)
      .where(fk_column == fk_id)
      .values(
        delete_flg=delete_flg,
        update_at=datetime.utcnow()
      )
    )

    await self.db.execute(stmt)

  async def delete_question(self, question_id: UUID):
      await self._soft_delete_by_id(Question, question_id)

      for model, fk in self.question_dependencies.items():
        await self._soft_delete_by_fk(model, fk, question_id)

  async def delete_test(self, test_id: UUID):
      await self._soft_delete_by_id(Test, test_id)

      question_ids = await self.db.scalars(
        select(Question.id).where(
          Question.test_id == test_id,
          Question.delete_flg == False
        )
      )

      for question_id in question_ids:
        await self.delete_question(question_id)


  async def delete_lesson(self, lesson_id: UUID):
            await self._soft_delete_by_id(Lesson, lesson_id)

            test_ids = await self.db.scalars(
                select(Test.id).where(
                    Test.lesson_id == lesson_id,
                    Test.delete_flg == False
                )
            )

            for test_id in test_ids:
                await self.delete_test(test_id)
  async def delete_course(self, course_id: UUID):
            # курс
            await self._soft_delete_by_id(Course, course_id)

            # простые зависимости курса
            for model, fk in self.course_dependencies.items():
                if model is Lesson:
                    continue
                await self._soft_delete_by_fk(model, fk, course_id)

            # уроки курса (глубокий каскад)
            lesson_ids = await self.db.scalars(
                select(Lesson.id).where(
                    Lesson.course_id == course_id,
                    Lesson.delete_flg == False
                )
            )

            for lesson_id in lesson_ids:
                await self.delete_lesson(lesson_id)


