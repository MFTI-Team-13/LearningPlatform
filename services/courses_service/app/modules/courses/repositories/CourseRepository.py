from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.db.session import get_session
from app.common.deps.auth import CurrentUser
from app.modules.courses.enums import CourseLevel
from app.modules.courses.models_import import Course, CourseUser
from app.modules.courses.schemas.CourseScheme import CourseCreate, CourseUpdate

AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]


class CourseRepository:
  def __init__(self, db: AsyncSessionDep):
    self.db = db

  def _course_options(self, include_lessons: bool):
    if include_lessons:
      return (selectinload(Course.lesson),)
    return tuple()

  async def exists_title(self, title: str) -> bool:
    q = select(exists().where(Course.title == title))
    res = await self.db.execute(q)
    return bool(res.scalar())

  async def create(self, author_id: UUID, data: CourseCreate) -> Course:
    course = Course(**data.model_dump(), author_id=author_id)
    self.db.add(course)
    await self.db.commit()
    await self.db.refresh(course)
    return course

  async def get_for_user(
    self,
    user: CurrentUser,
    course_id: UUID,
    include_deleted: bool = False,
    include_lessons: bool = False,
  ) -> Course | None:
    roles = set(user.roles)
    q = select(Course).options(*self._course_options(include_lessons)).where(Course.id == course_id)

    if "admin" in roles:
      if not include_deleted:
        q = q.where(Course.delete_flg.is_(False))
    elif "teacher" in roles:
      q = q.where(
        Course.author_id == user.id,
        Course.delete_flg.is_(False),
      )
    elif "student" in roles:
      q = q.join(CourseUser, CourseUser.course_id == Course.id).where(
        CourseUser.user_id == user.id,
        CourseUser.is_active.is_(True),
        CourseUser.delete_flg.is_(False),
        Course.is_published.is_(True),
        Course.delete_flg.is_(False),
      )
    else:
      return None

    res = await self.db.execute(q)
    return res.scalar_one_or_none()

  async def list_for_user(
    self,
    user: CurrentUser,
    q: str | None = None,
    title: str | None = None,
    author_id: UUID | None = None,
    level: CourseLevel | None = None,
    published: bool | None = None,
    include_deleted: bool = False,
    include_lessons: bool = False,
    skip: int = 0,
    limit: int = 20,
  ) -> list[Course]:
    roles = set(user.roles)
    stmt = select(Course).options(*self._course_options(include_lessons))

    if title is not None:
      stmt = stmt.where(Course.title == title)

    if author_id is not None:
      stmt = stmt.where(Course.author_id == author_id)

    if level is not None:
      stmt = stmt.where(Course.level == level)

    if published is not None:
      stmt = stmt.where(Course.is_published.is_(published))

    if q is not None:
      stmt = stmt.where(
        or_(
          Course.title.ilike(f"%{q}%"),
          Course.description.ilike(f"%{q}%"),
        )
      )

    if "admin" in roles:
      if not include_deleted:
        stmt = stmt.where(Course.delete_flg.is_(False))
    elif "teacher" in roles:
      stmt = stmt.where(
        Course.author_id == user.id,
        Course.delete_flg.is_(False),
      )
    elif "student" in roles:
      stmt = stmt.join(CourseUser, CourseUser.course_id == Course.id).where(
        CourseUser.user_id == user.id,
        CourseUser.is_active.is_(True),
        CourseUser.delete_flg.is_(False),
        Course.is_published.is_(True),
        Course.delete_flg.is_(False),
      )
    else:
      return []

    stmt = stmt.offset(skip).limit(limit)

    res = await self.db.execute(stmt)
    return res.scalars().unique().all()

  async def patch(self, course_id: UUID, patch: CourseUpdate) -> Course | None:
    res = await self.db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if course is None:
      return None

    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
      setattr(course, k, v)

    course.update_at = datetime.utcnow()
    await self.db.commit()
    await self.db.refresh(course)
    return course

  async def soft_delete(self, course_id: UUID) -> bool:
    res = await self.db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if course is None:
      return False

    course.delete_flg = True
    course.update_at = datetime.utcnow()
    await self.db.commit()
    return True

  async def hard_delete(self, course_id: UUID) -> bool:
    res = await self.db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if course is None:
      return False

    await self.db.delete(course)
    await self.db.commit()
    return True


async def get_course_repository(
  db: AsyncSession = Depends(get_session),
) -> CourseRepository:
  return CourseRepository(db)
