from typing import List, Optional
from datetime import datetime

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, desc
from sqlalchemy.orm import selectinload
from fastapi import Depends

from app.modules.courses.models_import import CourseUser,Course
from app.common.db.session import get_session



class CourseUserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, course_data_data: dict) -> CourseUser:
        course_student = CourseUser(**course_data_data)
        self.db.add(course_student)
        await self.db.commit()
        await self.db.refresh(course_student)
        return course_student

    async def get_by_id(self, id: UUID, delete_flg: bool | None) -> Optional[CourseUser]:
        query = select(CourseUser).where(CourseUser.id == id)

        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_course_id(self, course_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> List[CourseUser]:
        query = select(CourseUser).where(CourseUser.course_id == course_id)

        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        query = (
            query.offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> List[CourseUser]:
        query = select(CourseUser).where(CourseUser.user_id == user_id)

        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        query = (
            query.offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_course_and_user_id(self, course_id: UUID, user_id: UUID, delete_flg: bool | None) -> Optional[CourseUser]:
        query = select(CourseUser).where(
            and_(
                CourseUser.course_id == course_id,
                CourseUser.user_id == user_id
            )
        )


        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_by_user_id(self, user_id: UUID, delete_flg: bool | None, skip: int, limit: int) ->List[CourseUser]:
        query = select(CourseUser).where(
            and_(
                CourseUser.is_active == True,
                CourseUser.user_id == user_id
            )
        )

        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        query = (query.order_by(desc(CourseUser.create_at))
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_with_courseUser_and_course(self,user_id: UUID,course_id: UUID | None,delete_flg: bool | None) -> List[CourseUser]:
        query = (
          select(CourseUser, Course)
          .join(Course)
          .where(
            and_(CourseUser.user_id == user_id,
                 CourseUser.course_id == Course.id
        )
          )
          )

        if delete_flg is not None:
          query = query.where(
            and_(CourseUser.delete_flg == delete_flg,
                 Course.delete_flg == delete_flg
            )
          )

        if course_id is not None:
          query = query.where(CourseUser.course_id == course_id)

        result = await self.db.execute(query)
        return result.all()

    async def update(self, id: UUID, course_student_data: dict) -> Optional[CourseUser]:
        course_student = await self.get_by_id(id, False)

        if not course_student:
            return None

        for key, value in course_student_data.items():
            if hasattr(course_student, key):
              setattr(course_student, key, value)

        course_student.update_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(course_student)
        return course_student

    async def soft_delete(self, course_student_id: UUID) -> bool:
        course_student = await self.get_by_id(course_student_id, None)

        if not course_student:
            return False

        course_student.delete_flg = True
        course_student.is_active = False
        course_student.update_at = datetime.utcnow()

        await self.db.commit()
        return True

    async def hard_delete(self, course_student_id: UUID) -> bool:
        course_student = await self.get_by_id(course_student_id, None)

        if not course_student:
            return False

        await self.db.delete(course_student)
        await self.db.commit()
        return True

    async def activate(self, id: UUID) -> Optional[CourseUser]:
        course_student = await self.get_by_id(id, False)

        if not course_student:
            return None

        course_student.is_active = True
        await self.db.commit()
        return course_student

    async def deactivate(self, id: UUID) -> Optional[CourseUser]:
        course_student = await self.get_by_id(id, None)

        if not course_student:
            return None

        course_student.is_active = False
        await self.db.commit()
        return course_student

    async def get_all(self, delete_flg: bool | None, skip: int, limit: int) -> List[CourseUser]:
        query = select(CourseUser)

        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_active(self, is_active:bool, delete_flg: bool | None, skip: int, limit: int) -> List[CourseUser]:
        query = select(CourseUser).where(CourseUser.is_active == is_active)

        if delete_flg is not None:
            query = query.where(CourseUser.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

async def get_course_user_repository(
  db: AsyncSession = Depends(get_session),
) -> CourseUserRepository:
  return CourseUserRepository(db)
