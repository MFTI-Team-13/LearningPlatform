from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security
from starlette import status

from app.common.deps.auth import CurrentUser, get_current_user
from app.modules.courses.enums import CourseLevel
from app.modules.courses.exceptions import handle_errors
from app.modules.courses.schemas_import import (
  CourseCreate,
  CourseResponse,
  CourseUpdate,  # сделаем его PATCH-совместимым
)
from app.modules.courses.services_import import CourseService, get_course_service

router = APIRouter()

CurrentUserDep = Annotated[CurrentUser, Security(get_current_user)]
CourseServiceDep = Annotated[CourseService, Depends(get_course_service)]


def require_roles(*allowed_roles: str):
  async def role_checker(user: CurrentUserDep):
    if set(user.roles).intersection(allowed_roles):
      return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

  return role_checker


@router.post(
  "",
  response_model=CourseResponse,
  dependencies=[Depends(require_roles("admin", "teacher"))],
)
async def create_course(
  data: CourseCreate,
  user: CurrentUserDep,
  service: CourseServiceDep,
):
  return await handle_errors(lambda: service.create_course(user.id, data))


@router.get("", response_model=list[CourseResponse])
async def list_courses(
  user: CurrentUserDep,
  service: CourseServiceDep,
  q: str | None = None,
  title: str | None = None,
  author_id: UUID | None = None,
  level: CourseLevel | None = None,
  published: bool | None = None,
  include_deleted: bool = False,
  include_lessons: bool = False,
  skip: int = 0,
  limit: int = 20,
):
  return await handle_errors(
    lambda: service.list_courses(
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
  )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
  course_id: UUID,
  user: CurrentUser = Security(get_current_user),
  service: CourseService = Depends(get_course_service),
  include_deleted: bool = False,
):
  return await handle_errors(
    lambda: service.get_course(user, course_id, include_deleted=include_deleted)
  )


@router.patch(
  "/{course_id}",
  response_model=CourseResponse,
  dependencies=[Depends(require_roles("admin", "teacher"))],
)
async def patch_course(
  course_id: UUID,
  data: CourseUpdate,
  user: CurrentUserDep,
  service: CourseServiceDep,
):
  return await handle_errors(lambda: service.update_course(user, course_id, data))


@router.delete(
  "/{course_id}",
  response_model=bool,
)
async def delete_course(
  user: CurrentUserDep,
  service: CourseServiceDep,
  course_id: UUID,
  hard: bool = False,
):
  if hard and "admin" not in set(user.roles):
    raise HTTPException(status_code=403, detail="Недостаточно прав для hard delete")

  return await handle_errors(lambda: service.delete_course(user, course_id, hard=hard))
