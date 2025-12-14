from __future__ import annotations

from uuid import UUID

from fastapi import Depends

from app.common.deps.auth import CurrentUser
from app.modules.courses.enums import CourseLevel
from app.modules.courses.exceptions import (
  AlreadyExistsError,
  ConflictError,
  ForbiddenError,
  NotFoundError,
)
from app.modules.courses.models_import import Course
from app.modules.courses.repositories.CourseRepository import (
  CourseRepository,
  get_course_repository,
)
from app.modules.courses.schemas.CourseScheme import CourseCreate, CourseUpdate


class CourseService:
  def __init__(self, repo: CourseRepository):
    self.repo = repo

  async def create_course(self, author_id: UUID, in_data: CourseCreate) -> Course:
    if await self.repo.exists_title(in_data.title):
      raise AlreadyExistsError("Курс с таким названием уже существует")
    return await self.repo.create(author_id=author_id, data=in_data)

  async def get_course(
    self, user: CurrentUser, course_id: UUID, include_deleted: bool = False
  ) -> Course:
    course = await self.repo.get_for_user(
      user=user,
      course_id=course_id,
      include_deleted=include_deleted,
      include_lessons=False,
    )
    if course is None:
      raise NotFoundError("Курс не найден или нет доступа")
    return course

  async def list_courses(
    self,
    user: CurrentUser,
    q: str | None,
    title: str | None,
    author_id: UUID | None,
    level: CourseLevel | None,
    published: bool | None,
    include_deleted: bool,
    include_lessons: bool,
    skip: int,
    limit: int,
  ) -> list[Course]:
    return await self.repo.list_for_user(
      user=user,
      q=q,
      title=title,
      author_id=author_id,
      level=level,
      published=published,
      include_deleted=include_deleted,
      include_lessons=include_lessons,
      skip=skip,
      limit=limit,
    )

  async def update_course(self, user: CurrentUser, course_id: UUID, patch: CourseUpdate) -> Course:
    roles = set(user.roles)

    course = await self.repo.get_for_user(
      user=user,
      course_id=course_id,
      include_deleted=True,
      include_lessons=False,
    )
    if course is None:
      raise NotFoundError("Курс не найден или нет доступа")

    if "teacher" in roles and course.author_id != user.id:
      raise ForbiddenError()

    if "admin" not in roles and "teacher" not in roles:
      raise ForbiddenError()

    if patch.title is not None and patch.title != course.title:
      if await self.repo.exists_title(patch.title):
        raise AlreadyExistsError("Курс с таким названием уже существует")

    if patch.is_published is True and course.delete_flg:
      raise ConflictError("Нельзя опубликовать удалённый курс")

    updated = await self.repo.patch(course_id=course_id, patch=patch)
    if updated is None:
      raise NotFoundError("Курс не найден")
    return updated

  async def delete_course(self, user: CurrentUser, course_id: UUID, hard: bool) -> bool:
    roles = set(user.roles)

    course = await self.repo.get_for_user(
      user=user,
      course_id=course_id,
      include_deleted=True,
      include_lessons=False,
    )
    if course is None:
      raise NotFoundError("Курс не найден или нет доступа")

    if hard:
      if "admin" not in roles:
        raise ForbiddenError()
      return await self.repo.hard_delete(course_id)

    if "teacher" in roles and course.author_id != user.id:
      raise ForbiddenError()

    if "admin" not in roles and "teacher" not in roles:
      raise ForbiddenError()

    if course.is_published:
      await self.repo.patch(course_id=course_id, patch=CourseUpdate(is_published=False))

    return await self.repo.soft_delete(course_id)


async def get_course_service(
  repo: CourseRepository = Depends(get_course_repository),
) -> CourseService:
  return CourseService(repo)
