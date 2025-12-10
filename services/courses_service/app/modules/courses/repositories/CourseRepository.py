from typing import Any, Optional, List
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Course
from app.modules.courses.enums import CourseLevel
from app.common.db.session import get_session


class CourseRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def get_by_id(self, course_id: UUID) -> Optional[Course]:
      result = await self.db.execute(
          select(Course).where(
              and_(
                  Course.id == course_id,
                  Course.delete_flg == False
              )
          )
      )
      return result.scalar_one_or_none()

  async def get_by_title(self, title: str) -> Optional[Course]:
      result = await self.db.execute(
          select(Course).where(
              and_(
                Course.title == title,
                Course.delete_flg == False
              )
          )
       )
      return result.scalar_one_or_none()

  async def exists_by_title(self, title: str) -> bool:
      course = await self.get_by_title(title)
      return course is not None

  async def get_all(self,skip: int = 0,limit: int = 100,include_deleted: bool = False) -> List[Course]:
      query = select(Course)

      if not include_deleted:
          query = query.where(Course.delete_flg == False)

      query = query.offset(skip).limit(limit)

      result = await self.db.execute(query)
      return result.scalars().all()

  async def get_by_author(self,author_id: UUID,skip: int = 0,limit: int = 100) -> List[Course]:

      result = await self.db.execute(
          select(Course).where(
              and_(
                Course.author_id == author_id,
                Course.delete_flg == False
              )
          )
          .offset(skip)
          .limit(limit)
      )
      return result.scalars().all()

  async def get_by_level(self,level: CourseLevel,skip: int = 0,limit: int = 100) -> List[Course]:
      result = await self.db.execute(
          select(Course).where(
              and_(
                Course.level == level,
                Course.delete_flg == False
              )
          )
          .offset(skip)
          .limit(limit)
      )
      return result.scalars().all()

  async def get_published(self,skip: int = 0,limit: int = 100) -> List[Course]:
      result = await self.db.execute(
          select(Course).where(
              and_(
                Course.is_published == True,
                Course.delete_flg == False
              )
          )
          .offset(skip)
          .limit(limit)
      )
      return result.scalars().all()

  async def create(self, course_data: dict) -> Course:
      course = Course(**course_data)
      self.db.add(course)
      await self.db.commit()
      await self.db.refresh(course)
      return course

  async def update(self, course_id: UUID, course_data: dict) -> Optional[Course]:
      course = await self.get_by_id(course_id)

      if not course:
          return None

      for key, value in course_data.items():
          if hasattr(course, key):
            setattr(course, key, value)

      course.updated_at = datetime.utcnow()
      await self.db.commit()
      await self.db.refresh(course)
      return course

  async def soft_delete(self, course_id: UUID) -> bool:
      course = await self.get_by_id(course_id)

      if not course:
          return False

      course.delete_flg = True
      await self.db.commit()
      return True

  async def hard_delete(self, course_id: UUID) -> bool:
      course = await self.get_by_id(course_id)

      if not course:
          return False

      await self.db.delete(course)
      await self.db.commit()
      return True

  async def publish(self, course_id: UUID) -> bool:
      course = await self.get_by_id(course_id)

      if not course:
          return False

      course.is_published = True
      await self.db.commit()
      return True

  async def unpublish(self, course_id: UUID) -> bool:
      course = await self.get_by_id(course_id)

      if not course:
          return False

      course.is_published = False
      await self.db.commit()
      return True

  async def search(self,search_term: str,skip: int = 0,limit: int = 100) -> List[Course]:
      result = await self.db.execute(
          select(Course).where(
              and_(
                  or_(
                    Course.title.ilike(f"%{search_term}%"),
                    Course.description.ilike(f"%{search_term}%")
                  ),
                  Course.delete_flg == False
              )
          )
          .offset(skip)
          .limit(limit)
      )
      return result.scalars().all()

  async def count(self, include_deleted: bool = False) -> int:
      query = select(Course)

      if not include_deleted:
          query = query.where(Course.delete_flg == False)

      result = await self.db.execute(query)
      return len(result.scalars().all())

  async def get_with_lessons(self, course_id: UUID) -> Optional[Course]:
      result = await self.db.execute(
          select(Course).where(
              and_(
                Course.id == course_id,
                Course.delete_flg == False
              )
          )
      )
      return result.scalar_one_or_none()


async def get_course_repository(
  db: AsyncSession = Depends(get_session),
) -> CourseRepository:
  return CourseRepository(db)
