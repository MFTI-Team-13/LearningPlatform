from typing import Optional, List
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Test
from app.common.db.session import get_session


class TestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, test_id: UUID) -> Optional[Test]:
        result = await self.db.execute(
            select(Test).where(Test.id == test_id)
        )

        return result.scalar_one_or_none()

    async def get_by_lesson_id(self, lesson_id: UUID) -> Optional[Test]:
        result = await self.db.execute(
            select(Test).where(Test.lesson_id == lesson_id)
        )

        return result.scalar_one_or_none()

    async def get_all_active(self, skip: int = 0, limit: int = 100) -> List[Test]:
        result = await self.db.execute(
            select(Test)
              .where(Test.is_active == True)
              .offset(skip)
              .limit(limit)
        )
        return result.scalars().all()

    async def get_by_course_id(self, course_id: UUID, skip: int = 0, limit: int = 100) -> List[Test]:
        from models.lesson import Lesson

        result = await self.db.execute(
            select(Test).join(Lesson, Test.lesson_id == Lesson.id)
              .where(Lesson.course_id == course_id)
              .offset(skip)
              .limit(limit)
        )
        return result.scalars().all()

    async def create(self, test_data: dict) -> Test:
        test = Test(**test_data)
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def update(self, test_id: UUID, test_data: dict) -> Optional[Test]:
        test = await self.get_by_id(test_id)

        if not test:
            return None

        for key, value in test_data.items():
            if hasattr(test, key):
                setattr(test, key, value)

        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def hard_delete(self, test_id: UUID) -> bool:
        test = await self.get_by_id(test_id)

        if not test:
            return False

        await self.db.delete(test)
        await self.db.commit()
        return True

    async def activate(self, test_id: UUID) -> bool:
        test = await self.get_by_id(test_id)

        if not test:
            return False

        test.is_active = True
        await self.db.commit()
        return True

    async def deactivate(self, test_id: UUID) -> bool:
        test = await self.get_by_id(test_id)

        if not test:
            return False

        test.is_active = False
        await self.db.commit()
        return True

    async def search(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Test]:
        result = await self.db.execute(
            select(Test)
              .where(
                  or_(
                      Test.title.ilike(f"%{search_term}%"),
                      Test.description.ilike(f"%{search_term}%")
                  )
              )
              .offset(skip)
              .limit(limit)
        )
        return result.scalars().all()

    async def count_active_by_course(self, course_id: UUID) -> int:
        from models.lesson import Lesson

        result = await self.db.execute(
            select(Test)
              .join(Lesson, Test.lesson_id == Lesson.id)
              .where(
                  and_(
                      Lesson.course_id == course_id,
                      Test.is_active == True
                  )
              )
        )
        tests = result.scalars().all()
        return len(tests)


async def get_test_repository(
    db: AsyncSession = Depends(get_session),
) -> TestRepository:
    return TestRepository(db)
