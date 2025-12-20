from uuid import UUID

from fastapi import APIRouter, Depends, Security

from app.common.deps.auth import CurrentUser, get_current_user
from app.modules.courses.enums import CourseLevel
from app.modules.courses.exceptions import handle_errors
from app.modules.courses.schemas_import import CourseCreate, CourseResponse, CourseUpdate
from app.modules.courses.services_import import CourseService, get_course_service

from .requre import require_roles

router = APIRouter()


# teacher
@router.post(
  "/create",
  response_model=CourseResponse,
  dependencies=[Depends(require_roles("admin", "teacher"))],
)
async def create_course(
  data: CourseCreate,
  user: CurrentUser = Security(get_current_user),
  service: CourseService = Depends(get_course_service),
):
  return await handle_errors(lambda: service.create_course(user.id, data))


@router.post(
  "/getById",
  response_model=CourseResponse,
  dependencies=[Depends(require_roles("admin", "teacher", "student"))],
)
async def get_course(
  course_id: UUID,
  delete_flg: bool | None = None,
  user: CurrentUser = Security(get_current_user),
  service: CourseService = Depends(get_course_service),
):
  return await handle_errors(lambda: service.get_by_id_course(user, course_id, delete_flg))


@router.get(
  "/getByTitle",
  response_model=CourseResponse,
  dependencies=[Depends(require_roles("admin", "teacher", "student"))],
)
async def get_course(
  title: str,
  delete_flg: bool | None = None,
  user: CurrentUser = Security(get_current_user),
  service: CourseService = Depends(get_course_service),
):
  return await handle_errors(lambda: service.get_by_title(user, title, delete_flg))


@router.get(
  "/list", response_model=list[CourseResponse], dependencies=[Depends(require_roles("admin"))]
)
async def list_courses(
  delete_flg: bool | None = None,
  skip: int = 0,
  limit: int = 20,
  service: CourseService = Depends(get_course_service),
):
  return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))


@router.post(
  "/getByUser",
  response_model=list[CourseResponse],
  dependencies=[Depends(require_roles("admin", "teacher", "student"))],
)
async def get_by_author(
  author_id: UUID | None = None,
  user_id: UUID | None = None,
  is_published: bool | None = None,
  level: CourseLevel | None = None,
  delete_flg: bool | None = None,
  skip: int = 0,
  limit: int = 20,
  service: CourseService = Depends(get_course_service),
  user: CurrentUser = Security(get_current_user),
):
  return await handle_errors(
    lambda: service.get_by_user(
      user, author_id, user_id, is_published, level, delete_flg, skip, limit
    )
  )


@router.put(
  "/update",
  response_model=CourseResponse,
  dependencies=[Depends(require_roles("admin", "teacher"))],
)
async def update_course(
  course_id: UUID,
  data: CourseUpdate,
  user: CurrentUser = Security(get_current_user),
  service: CourseService = Depends(get_course_service),
):
  return await handle_errors(lambda: service.update_course(user, course_id, data))


@router.delete(
  "/softDelete", response_model=bool, dependencies=[Depends(require_roles("admin", "teacher"))]
)
async def soft_delete_course(
  course_id: UUID,
  user: CurrentUser = Security(get_current_user),
  service: CourseService = Depends(get_course_service),
):
  return await handle_errors(lambda: service.soft_delete_course(user, course_id))


@router.delete("/hardDelete", response_model=bool, dependencies=[Depends(require_roles("admin"))])
async def hard_delete_course(course_id: UUID, service: CourseService = Depends(get_course_service)):
  return await handle_errors(lambda: service.hard_delete(course_id))
