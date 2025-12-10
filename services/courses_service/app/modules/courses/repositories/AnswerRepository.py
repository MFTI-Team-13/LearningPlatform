from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Answer
from app.common.db.session import get_session


class AnswerRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def get_by_id(self, id: UUID, delete_flg:bool = True) -> Optional[Answer]:
    result = await self.db.execute(
      select(Answer).where(
        and_(
          Answer.id == id,
          Answer.delete_flg == delete_flg
        )
      )
    )
    return result.scalar_one_or_none()

  async def get_by_question_and_order(self, question_id: UUID, order_index: int) -> Optional[Answer]:
    result = await self.db.execute(
      select(Answer).where(
        and_(
          Answer.question_id == question_id,
          Answer.order_index == order_index
        )
      )
    )
    return result.scalar_one_or_none()

  async def get_by_question_id(self, question_id: UUID, skip: int = 0, limit: int = 100) -> List[Answer]:
    result = await self.db.execute(
      select(Answer)
      .where(Answer.question_id == question_id)
      .order_by(Answer.order_index)
      .offset(skip)
      .limit(limit)
    )
    return result.scalars().all()

  async def get_correct_answers_by_question(self, question_id: UUID) -> List[Answer]:
    result = await self.db.execute(
      select(Answer)
      .where(
        and_(
          Answer.question_id == question_id,
          Answer.is_correct == True
        )
      )
      .order_by(Answer.order_index)
    )
    return result.scalars().all()

  async def create(self, answer_data: dict) -> Answer:
    answer = Answer(**answer_data)
    self.db.add(answer)
    await self.db.commit()
    await self.db.refresh(answer)
    return answer

  async def create_bulk(self, answers_data: List[dict]) -> List[Answer]:
    answers = [Answer(**data) for data in answers_data]
    self.db.add_all(answers)
    await self.db.commit()

    for answer in answers:
      await self.db.refresh(answer)

    return answers

  async def update(self, answer_id: UUID, answer_data: dict) -> Optional[Answer]:
    answer = await self.get_by_id(answer_id)

    if not answer:
      return None

    for key, value in answer_data.items():
      if hasattr(answer, key):
        setattr(answer, key, value)

    answer.updated_at = datetime.utcnow()
    await self.db.commit()
    await self.db.refresh(answer)
    return answer

  async def soft_delete(self, answer_id: UUID) -> bool:
      answer = await self.get_by_id(answer_id)

      if not answer:
          return False

      answer.delete_flg = True
      answer.updated_at = datetime.utcnow()
      await self.db.commit()
      return True

  async def hard_delete(self, answer_id: UUID) -> bool:
      answer = await self.get_by_id(answer_id)

      if not answer:
          return False

      await self.db.delete(answer)
      await self.db.commit()
      return True

  async def get_max_order_index(self, question_id: UUID) -> int:
    result = await self.db.execute(
      select(func.max(Answer.order_index))
      .where(Answer.question_id == question_id)
    )
    max_order = result.scalar()
    return max_order if max_order is not None else -1

  async def reorder_answers(self, question_id: UUID, start_index: int) -> None:
    answers = await self.get_by_question_id(question_id)
    answers_to_reorder = [a for a in answers if a.order_index >= start_index]

    for answer in sorted(answers_to_reorder, key=lambda x: x.order_index):
      answer.order_index += 1
      await self.db.flush()

    await self.db.commit()

  async def count_by_question(self, question_id: UUID) -> int:
    result = await self.db.execute(
      select(func.count(Answer.id))
      .where(Answer.question_id == question_id)
    )
    return result.scalar()

  async def count_correct_answers_by_question(self, question_id: UUID) -> int:
    result = await self.db.execute(
      select(func.count(Answer.id))
      .where(
        and_(
          Answer.question_id == question_id,
          Answer.is_correct == True
        )
      )
    )
    return result.scalar()


async def get_answer_repository(
  db: AsyncSession = Depends(get_session),
) -> AnswerRepository:
  return AnswerRepository(db)
