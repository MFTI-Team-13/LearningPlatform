from typing import Optional, List
from datetime import datetime

from uuid import UUID
from fastapi import Depends
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Test,Lesson,Course,CourseUser
from app.common.db.session import get_session
from .CascadeDeleteRepository import CascadeDeleteRepository


class TestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cascade_delete = CascadeDeleteRepository(db)

    async def create(self, test_data: dict) -> Test:
        test = Test(**test_data)
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def get_by_id(self, id: UUID, delete_flg: bool) -> Optional[Test]:
        query = select(Test).where(Test.id == id)

        if delete_flg is not None:
            query = query.where(Test.delete_flg == delete_flg)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_lesson_id(self, lesson_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> List[Test]:
        query = select(Test).where(Test.lesson_id == lesson_id)

        if delete_flg is not None:
            query = query.where(Test.delete_flg == delete_flg)

        query = (
            query.offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all(self, delete_flg: bool, skip: int = 0, limit: int = 100) -> List[Test]:
        query = select(Test)

        if delete_flg is not None:
            query = query.where(Test.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def activate(self, test_id: UUID) -> Optional[Test]:
        test = await self.get_by_id(test_id, False)

        if not test:
            return None

        test.is_active = True
        await self.db.commit()
        return test

    async def deactivate(self, test_id: UUID) -> Optional[Test]:
        test = await self.get_by_id(test_id, None)

        if not test:
            return None

        test.is_active = False
        await self.db.commit()
        return test

    async def get_all_active(self, delete_flg: bool, skip: int = 0, limit: int = 100) -> List[Test]:
        query = select(Test).where(Test.is_active == True)

        if delete_flg is not None:
            query = query.where(Test.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_course_id(self, course_id: UUID,delete_flg:bool, skip: int = 0, limit: int = 100) -> List[Test]:
        query = (
            select(Test)
            .join(Lesson, Test.lesson_id == Lesson.id)
            .where(Lesson.course_id == course_id)
        )

        if delete_flg is not None:
            query = query.where(
                and_(
                  Test.delete_flg == delete_flg,
                  Lesson.delete_flg == delete_flg
                )
            )

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, test_id: UUID, test_data: dict) -> Optional[Test]:
        test = await self.get_by_id(test_id, False)

        if not test:
            return None

        for key, value in test_data.items():
            if hasattr(test, key):
                setattr(test, key, value)

        test.update_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def soft_delete(self, test_id: UUID) -> bool:
        test = await self.get_by_id(test_id,delete_flg = False)

        if not test:
            return False

        try:
          await self.cascade_delete.delete_test(test_id)
          await self.db.commit()
          return True
        except Exception as e:
          await self.db.rollback()
          raise

    async def hard_delete(self, test_id: UUID) -> bool:
        test = await self.get_by_id(test_id,None)

        if not test:
            return False

        await self.db.delete(test)
        await self.db.commit()
        return True

    async def search(self, search_term: str,delete_flg: bool | None, skip: int = 0, limit: int = 100) -> List[Test]:
        query = select(Test).where(
            or_(
                Test.title.ilike(f"%{search_term}%"),
                Test.description.ilike(f"%{search_term}%")
            )
        )
        if delete_flg is not None:
            query = query.where(Test.delete_flg == delete_flg)

        query = (
            query.offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assigned_to_create_by_user(self, user_id: UUID, lesson_id: UUID, type: str):
        query = (
            select(Lesson)
            .join(Course, Course.id == Lesson.course_id)
            .where(
                and_(
                    Course.delete_flg == False,
                    Course.is_published == True,

                    Lesson.delete_flg == False,
                    Lesson.id == lesson_id
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
            query = (
                  query
                  .join(CourseUser, CourseUser.course_id == Course.id)
                  .where(
                    and_(
                        CourseUser.user_id == user_id,
                        CourseUser.is_active == True,
                        CourseUser.delete_flg == False
                    )
                )
            )
        return query

    async def get_assigned_to_user(self,user_id: UUID,test_id: UUID,type:str)-> Optional[Test]:
        query = (
            select(Test)
            .join(Lesson, Lesson.id == Test.lesson_id)
            .join(Course, Course.id == Lesson.course_id)
            .where(
                and_(
                  Course.delete_flg == False,
                  Course.is_published == True,

                  Lesson.delete_flg == False,

                  Test.id == test_id,
                  Test.is_active == True,
                  Test.delete_flg == False,
                )
            )
        )
        query = await self.subquery(query, user_id, type)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()


async def get_test_repository(
    db: AsyncSession = Depends(get_session),
) -> TestRepository:
    return TestRepository(db)
