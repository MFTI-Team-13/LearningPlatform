from typing import Optional, List
from datetime import datetime

from fastapi import Depends
from uuid import UUID
from sqlalchemy import select, update,and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Course, CourseUser,Lesson,CourseReview
from app.modules.courses.enums import CourseLevel
from app.common.db.session import get_session
from .CascadeDeleteRepository import CascadeDeleteRepository


class CourseRepository:
  def __init__(self, db: AsyncSession):
    self.db = db
    self.cascade_delete = CascadeDeleteRepository(db)

  async def create(self, course_data: dict) -> Course:
      course = Course(**course_data)
      self.db.add(course)
      await self.db.commit()
      await self.db.refresh(course)
      return course


  async def get_by_id(self, id: UUID, delete_flg:bool) -> Optional[Course]:
      query = select(Course).where(Course.id == id)

      if delete_flg is not None:
          query = query.where(Course.delete_flg == delete_flg)

      result = await self.db.execute(query)

      return result.scalar_one_or_none()

  async def get_by_title(self, title: str,delete_flg:bool) -> Optional[Course]:
      query = select(Course).where(Course.title == title)

      if delete_flg is not None:
          query = query.where(Course.delete_flg == delete_flg)

      result = await self.db.execute(query)
      return result.scalar_one_or_none()

  async def get_all(self,delete_flg: bool, skip: int,limit: int) -> List[Course]:
      query = select(Course)

      if delete_flg is not None:
          query = query.where(Course.delete_flg == delete_flg)

      query = query.offset(skip).limit(limit)

      result = await self.db.execute(query)
      return result.scalars().all()

  async def get_by_user(self,author_id: UUID | None,user_id: UUID | None,is_published:bool | None,level: CourseLevel | None,delete_flg:bool|None,skip: int,limit: int) -> List[Course]:
      query = select(Course)

      if author_id is not None:
          query = query.where(Course.author_id == author_id)

      if user_id is not None:
          query = (query
              .join(CourseUser,
                  and_(
                      CourseUser.course_id == Course.id,
                      CourseUser.user_id == user_id,
                      CourseUser.delete_flg == False,
                      CourseUser.is_active == True
                  )
              )
          )
      if is_published is not None:
          query = query.where(Course.is_published == is_published)

      if level is not None:
          query = query.where(Course.level == level)

      if delete_flg is not None:
          query = query.where(Course.delete_flg == delete_flg)

      query = query.offset(skip).limit(limit)

      result = await self.db.execute(query)

      return result.scalars().all()

  async def get_assigned_to_user(self, user_id: UUID, course_id:UUID, type:str = None):
      query = (
          select(Course)
          .join(CourseUser, CourseUser.course_id == Course.id)
          .where(
              and_(
                  CourseUser.user_id == user_id,
                  CourseUser.is_active == True,
                  Course.delete_flg == False,
                  CourseUser.delete_flg == False,
                  Course.is_published == True,
                  Course.id == course_id
              )
          )
      )
      result = await self.db.execute(query)
      return result.scalar_one_or_none()

  async def update(self, course_id: UUID, course_data: dict) -> Optional[Course]:
      course = await self.get_by_id(course_id,False)

      if not course:
          return None

      for key, value in course_data.items():
          if hasattr(course, key):
            setattr(course, key, value)

      course.update_at = datetime.utcnow()
      await self.db.commit()
      await self.db.refresh(course)
      return course

  async def soft_delete(self, course_id: UUID) -> bool:
      course = await self.get_by_id(course_id, delete_flg = False)

      if not course:
          return False

      try:
        await self.cascade_delete.delete_course(course_id)
        await self.db.commit()
        return True
      except Exception as e:
        await self.db.rollback()
        raise

  async def hard_delete(self, course_id: UUID) -> bool:
      course = await self.get_by_id(course_id, None)

      if not course:
          return False

      await self.db.delete(course)
      await self.db.commit()
      return True

  async def unpublish(self, course_id: UUID) -> Optional[Course]:
      course = await self.get_by_id(course_id,None)

      if not course:
          return None

      course.is_published = False
      await self.db.commit()
      return course


async def get_course_repository(
  db: AsyncSession = Depends(get_session),
) -> CourseRepository:
  return CourseRepository(db)
