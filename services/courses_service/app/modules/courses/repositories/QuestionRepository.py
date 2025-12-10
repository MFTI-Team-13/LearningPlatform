from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Question
from app.modules.courses.enums import QuestionType
from app.common.db.session import get_session


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, delete_flg:bool = True) -> Optional[Question]:
        result = await self.db.execute(
            select(Question).where(
              and_(
                Question.id == id,
                Question.delete_flg == delete_flg
              )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_test_and_order(self, test_id: UUID, order_index: int) -> Optional[Question]:
        result = await self.db.execute(
            select(Question).where(
                and_(
                    Question.test_id == test_id,
                    Question.order_index == order_index
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_test_id(self, test_id: UUID, skip: int = 0, limit: int = 100) -> List[Question]:
        result = await self.db.execute(
            select(Question)
            .where(Question.test_id == test_id)
            .order_by(Question.order_index)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_question_type(self, question_type: QuestionType, skip: int = 0, limit: int = 100) -> List[Question]:
        result = await self.db.execute(
            select(Question)
            .where(Question.question_type == question_type)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, question_data: dict) -> Question:
        question = Question(**question_data)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question


    async def create_bulk(self, questions_data: List[dict]) -> List[Question]:
      questions = [Question(**data) for data in questions_data]
      self.db.add_all(questions)
      await self.db.commit()

      for question in questions:
        await self.db.refresh(question)

      return questions

    async def update(self, question_id: UUID, question_data: dict) -> Optional[Question]:
        question = await self.get_by_id(question_id)

        if not question:
            return None

        for key, value in question_data.items():
            if hasattr(question, key):
                setattr(question, key, value)

        question.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def soft_delete(self, question_id: UUID) -> bool:
      question = await self.get_by_id(question_id)

      if not question:
        return False

      question.delete_flg = True
      question.updated_at = datetime.utcnow()
      await self.db.commit()
      return True

    async def hard_delete(self, question_id: UUID) -> bool:
      question = await self.get_by_id(question_id)

      if not question:
        return False

      await self.db.delete(question)
      await self.db.commit()
      return True

    async def get_max_order_index(self, test_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(Question.order_index))
            .where(Question.test_id == test_id)
        )
        max_order = result.scalar()
        return max_order if max_order is not None else -1

    async def reorder_questions(self, test_id: UUID, start_index: int) -> None:
        questions = await self.get_by_test_id(test_id)
        questions_to_reorder = [q for q in questions if q.order_index >= start_index]

        for question in sorted(questions_to_reorder, key=lambda x: x.order_index):
            question.order_index += 1
            await self.db.flush()

        await self.db.commit()

    async def search_in_test(self, test_id: UUID, search_term: str) -> List[Question]:
        result = await self.db.execute(
            select(Question)
            .where(
                and_(
                    Question.test_id == test_id,
                    Question.text.ilike(f"%{search_term}%")
                )
            )
            .order_by(Question.order_index)
        )
        return result.scalars().all()

    async def count_by_test(self, test_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Question.id))
            .where(Question.test_id == test_id)
        )
        return result.scalar()

    async def get_total_score_by_test(self, test_id: UUID) -> int:
        result = await self.db.execute(
            select(func.sum(Question.score))
            .where(Question.test_id == test_id)
        )
        total_score = result.scalar()
        return total_score if total_score is not None else 0


async def get_question_repository(
    db: AsyncSession = Depends(get_session),
) -> QuestionRepository:
    return QuestionRepository(db)
