from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_session
from app.modules.courses.enums import QuestionType
from app.modules.courses.models_import import Question


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, question_data: dict) -> Question:
        question = Question(**question_data)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def create_bulk(self, questions_data: list[dict]) -> list[Question]:
        questions = [Question(**data) for data in questions_data]
        self.db.add_all(questions)
        await self.db.commit()

        for question in questions:
          await self.db.refresh(question)

        return questions

    async def get_by_id(self, id: UUID, delete_flg: bool) -> Question | None:
        query = select(Question).where(Question.id == id)

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_test_id(self, test_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> list[Question]:
        query = select(Question).where(Question.test_id == test_id)

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        query = (
            query.order_by(Question.order_index)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_test_and_order(self, test_id: UUID, order_index: int, delete_flg: bool | None) -> Question | None:
        query = (
            select(Question)
            .where(
                and_(
                    Question.test_id == test_id,
                    Question.order_index == order_index
                )
            )
        )

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, delete_flg: bool, skip: int = 0, limit: int = 100) -> list[Question]:
        query = select(Question)

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_question_type(self, question_type: QuestionType,delete_flg: bool, skip: int = 0, limit: int = 100) -> list[Question]:
        query = select(Question).where(Question.question_type == question_type)

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_max_order_index(self, test_id: UUID, delete_flg: bool | None) -> int:
        query = select(func.max(Question.order_index)).where(Question.test_id == test_id)

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        result = await self.db.execute(query)
        max_order = result.scalar()
        return max_order if max_order is not None else -1

    async def search_in_test(self, test_id: UUID, search_term: str, delete_flg: bool | None,skip: int, limit: int ) -> list[Question]:
        query = select(Question).where(
            and_ (
                Question.test_id == test_id,
                Question.text.ilike(f"%{search_term}%")
            )
        )

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)
        query = query.offset(skip).limit(limit)
        query = query.order_by(Question.order_index)

        result = await self.db.execute(query)
        return result.scalars().all()


    async def get_total_score_by_test(self, test_id: UUID, delete_flg: bool | None ) -> int:
        query = select(func.sum(Question.score)).where(Question.test_id == test_id)

        if delete_flg is not None:
            query = query.where(Question.delete_flg == delete_flg)

        result = await self.db.execute(query)
        total_score = result.scalar()
        return total_score if total_score is not None else -1

    async def update(self, question_id: UUID, question_data: dict) -> Question | None:
        question = await self.get_by_id(question_id, False)

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
        question = await self.get_by_id(question_id, delete_flg=False)

        if not question:
            return False

        question.delete_flg = True
        question.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def hard_delete(self, question_id: UUID) -> bool:
        question = await self.get_by_id(question_id, None)

        if not question:
            return False

        await self.db.delete(question)
        await self.db.commit()
        return True


async def get_question_repository(
    db: AsyncSession = Depends(get_session),
) -> QuestionRepository:
    return QuestionRepository(db)
