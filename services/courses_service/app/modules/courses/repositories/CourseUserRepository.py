from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, desc
from fastapi import Depends

from app.modules.courses.models_import import CourseUser
from app.common.db.session import get_session



class CourseUserRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def get_by_id(self, id: UUID) -> Optional[CourseUser]:
    result = await self.db.execute(
      select(CourseUser).where(CourseUser.id == id)
    )
    return result.scalar_one_or_none()

  async def get_by_course_id(self, course_id: str) -> List[CourseUser]:
    result = await self.db.execute(
      select(CourseUser).where(CourseUser.course_id == course_id)
    )
    return result.scalars().all()

  async def get_by_user_id(self, user_id: UUID) -> List[CourseUser]:
    result = await self.db.execute(
      select(CourseUser)
      .where(CourseUser.user_id == user_id)
      .order_by(desc(CourseUser.created_at))
    )
    return result.scalars().all()

  async def get_by_course_and_user(self, course_id: UUID, user_id: UUID) -> Optional[CourseUser]:
    result = await self.db.execute(
      select(CourseUser).where(and_(
        CourseUser.course_id == course_id,
        CourseUser.user_id == user_id
      ))
    )
    return result.scalar_one_or_none()

  async def get_active_by_user_id(self, user_id: UUID) -> List[CourseUser]:
    result = await self.db.execute(
      select(CourseUser)
      .where(and_(
        CourseUser.user_id == user_id,
        CourseUser.is_active == True
      ))
      .order_by(desc(CourseUser.created_at))
    )
    return result.scalars().all()

  async def create(self, course_data_data: dict) -> CourseUser:
      course_student = CourseUser(**course_data_data)
      self.db.add(course_student)
      await self.db.commit()
      await self.db.refresh(course_student)
      return course_student

  async def update(self, id: UUID, course_student_data: dict) -> Optional[CourseUser]:
    course_student = await self.get_by_id(id)

    if not course_student:
      return None

    for key, value in course_student_data.items():
      if hasattr(course_student, key):
        setattr(course_student, key, value)

    course_student.updated_at = datetime.utcnow()
    await self.db.commit()
    await self.db.refresh(course_student)
    return course_student

  async def hard_delete(self, id: UUID) -> bool:
    course_student = await self.get_by_id(id)
    if not course_student:
      return False

    await self.db.delete(course_student)
    await self.db.commit()
    return True

  async def activate(self, id: UUID) -> bool:
    course_student = await self.get_by_id(id)

    if not course_student:
      return False

    course_student.is_active = True
    await self.db.commit()
    return True

  async def unactivate(self, id: UUID) -> bool:
    course_student = await self.get_by_id(id)

    if not course_student:
      return False

    course_student.is_active = False
    await self.db.commit()
    return True

  async def get_all(self, skip: int = 0, limit: int = 100) -> List[CourseUser]:
    result = await self.db.execute(
      select(CourseUser)
      .order_by(desc(CourseUser.created_at))
      .offset(skip)
      .limit(limit)
    )
    return result.scalars().all()

  async def get_active(self, skip: int = 0, limit: int = 100) -> List[CourseUser]:
    result = await self.db.execute(
      select(CourseUser)
      .where(CourseUser.is_active == True)
      .order_by(desc(CourseUser.created_at))
      .offset(skip)
      .limit(limit)
    )
    return result.scalars().all()

async def get_course_user_repository(
  db: AsyncSession = Depends(get_session),
) -> CourseUserRepository:
  return CourseUserRepository(db)
