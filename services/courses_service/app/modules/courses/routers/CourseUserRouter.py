from uuid import UUID

from fastapi import APIRouter, Depends, Security

from app.common.deps.auth import CurrentUser, get_current_user
from app.modules.courses.exceptions import handle_errors
from app.modules.courses.schemas_import import (
  CourseUserCreate,
  CourseUserResponse,
)
from app.modules.courses.services_import import CourseUserService, get_course_user_service

from .requre import require_roles

router = APIRouter()


@router.post(
  "/create", response_model=CourseUserResponse, dependencies=[Depends(require_roles("admin"))]
)
async def create_course_user(
  data: CourseUserCreate,
  service: CourseUserService = Depends(get_course_user_service),
  user: CurrentUser = Security(get_current_user),
):
  return await handle_errors(lambda: service.create_relation(user, data))


@router.get(
  "/list", response_model=list[CourseUserResponse], dependencies=[Depends(require_roles("admin"))]
)
async def list_courses(
  delete_flg: bool | None = None,
  skip: int = 0,
  limit: int = 20,
  service: CourseUserService = Depends(get_course_user_service),
):
  return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))


@router.post("/getById", response_model=CourseUserResponse)
async def get_course_user_by_id(
  id: UUID,
  delete_flg: bool | None = None,
  service: CourseUserService = Depends(get_course_user_service),
  user: CurrentUser = Security(get_current_user),
):
  return await handle_errors(lambda: service.get_by_id_rel(user, id, delete_flg))


@router.post(
  "/getByCourse",
  response_model=list[CourseUserResponse],
  dependencies=[Depends(require_roles("admin", "teacher"))],
)
async def get_by_course(
  course_id: UUID,
  delete_flg: bool | None = None,
  skip: int = 0,
  limit: int = 50,
  service: CourseUserService = Depends(get_course_user_service),
  user: CurrentUser = Security(get_current_user),
):
  return await handle_errors(
    lambda: service.get_by_course_id(user, course_id, delete_flg, skip, limit)
  )


@router.post(
  "/getByUser",
  response_model=list[CourseUserResponse],
  dependencies=[Depends(require_roles("admin"))],
)
async def get_by_user(
  user_id: UUID,
  delete_flg: bool | None = None,
  skip: int = 0,
  limit: int = 50,
  service: CourseUserService = Depends(get_course_user_service),
):
  return await handle_errors(lambda: service.get_by_user_id(user_id, delete_flg, skip, limit))


@router.post(
  "/getByCourseAndUser",
  response_model=CourseUserResponse,
  dependencies=[Depends(require_roles("admin", "student"))],
)
async def get_by_course_and_user(
  course_id: UUID,
  user_id: UUID | None = None,
  delete_flg: bool | None = None,
  service: CourseUserService = Depends(get_course_user_service),
  user: CurrentUser = Security(get_current_user),
):
  if ("admin" in user.roles and user_id is None) or "student" in user.roles:
    user_id = user.id
  return await handle_errors(
    lambda: service.get_by_course_and_user_id(user, course_id, user_id, delete_flg)
  )


@router.post(
  "/getActiveByUser",
  response_model=list[CourseUserResponse],
  dependencies=[Depends(require_roles("admin", "student"))],
)
async def get_active_by_user(
  user_id: UUID | None = None,
  delete_flg: bool | None = None,
  skip: int = 0,
  limit: int = 50,
  service: CourseUserService = Depends(get_course_user_service),
  user: CurrentUser = Security(get_current_user),
):
  if ("admin" in user.roles and user_id is None) or "student" in user.roles:
    user_id = user.id
  return await handle_errors(
    lambda: service.get_active_by_user_id(user, user_id, delete_flg, skip, limit)
  )


@router.put(
  "/activate", response_model=CourseUserResponse, dependencies=[Depends(require_roles("admin"))]
)
async def activate_course_user(
  id: UUID, service: CourseUserService = Depends(get_course_user_service)
):
  return await handle_errors(lambda: service.activate(id))


@router.put(
  "/deactivate", response_model=CourseUserResponse, dependencies=[Depends(require_roles("admin"))]
)
async def deactivate_course_user(
  id: UUID, service: CourseUserService = Depends(get_course_user_service)
):
  return await handle_errors(lambda: service.deactivate(id))


@router.delete("/softDelete", dependencies=[Depends(require_roles("admin"))])
async def soft_delete_course_user(
  id: UUID,
  service: CourseUserService = Depends(get_course_user_service),
):
  return await handle_errors(lambda: service.soft_delete(id))


@router.delete("/hardDelete", dependencies=[Depends(require_roles("admin"))])
async def hard_delete_course_user(
  id: UUID,
  service: CourseUserService = Depends(get_course_user_service),
):
  return await handle_errors(lambda: service.hard_delete(id))


@router.post("/getWithCourse", dependencies=[Depends(require_roles("admin", "student"))])
async def get_with_course_and_course_user(
  user_id: UUID | None = None,
  course_id: UUID | None = None,
  delete_flg: bool | None = None,
  service: CourseUserService = Depends(get_course_user_service),
  user: CurrentUser = Security(get_current_user),
):
  try:
    return await handle_errors(
      lambda: service.get_with_courseUser_and_course(user, user_id, course_id, delete_flg)
    )
  except Exception as e:
    print(f"Error in router: {e}")
    print(f"Result type: {type(result) if 'result' in locals() else 'N/A'}")
    raise
