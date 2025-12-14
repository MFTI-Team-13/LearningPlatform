from typing import List

from fastapi import APIRouter, Depends,Security
from uuid import UUID

from app.modules.courses.schemas_import import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseWithLessonsResponse
)
from app.modules.courses.services_import import CourseService, get_course_service
from app.modules.courses.exceptions import handle_errors
from app.modules.courses.enums import CourseLevel
from app.common.deps.auth import require_role,get_current_user,CurrentUser

router = APIRouter(prefix="/course")

def require_roles(*allowed_roles):
    async def role_checker(user = Depends(get_current_user)):
        user_roles = set(user.roles)
        if user_roles.intersection(allowed_roles):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return role_checker

@router.post("/create", response_model=CourseResponse, dependencies=[Depends(require_roles("admin", "teacher"))])
async def create_course(
    data: CourseCreate,
    user: CurrentUser = Security(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.create_course(user.id, data))


@router.post("/getById", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    user: CurrentUser = Security(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.get_by_id_course(user, course_id, delete_flg))

@router.post("/getByTitle", response_model=CourseResponse)
async def get_course(
    title: str,
    delete_flg: bool | None = None,
    user: CurrentUser = Security(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.get_by_title(user, title, delete_flg))


@router.get("/list", response_model=List[CourseResponse])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    user: CurrentUser = Security(get_current_user),
    service: CourseService = Depends(get_course_service),
):

    return await handle_errors(lambda: service.get_all_course(user, delete_flg, skip, limit))


@router.post("/getByAuthor", response_model=list[CourseResponse], dependencies=[Depends(require_roles("admin", "teacher"))])
async def get_by_author(
    author_id: UUID | None = None,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service),
    user: CurrentUser = Security(get_current_user)
):
    if ("admin" in user.roles and author_id is None) or "teacher" in user.roles:
        author_id = user.id

    return await handle_errors(lambda: service.get_by_author(user, author_id, delete_flg, skip, limit))

@router.post("/getPublished", response_model=list[CourseResponse])
async def get_published(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_published(user,delete_flg,skip, limit))

@router.post("/getByLevel", response_model=list[CourseResponse])
async def get_by_level(
    level: CourseLevel,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_level(user, level,delete_flg, skip, limit))

@router.put("/publish", response_model=CourseResponse, dependencies=[Depends(require_roles("admin", "teacher"))])
async def publish_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.publish(user, course_id))

@router.put("/unpublish", response_model=CourseResponse, dependencies=[Depends(require_roles("admin", "teacher"))])
async def unpublish_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.unpublish(user, course_id))
@router.put("/update", response_model=CourseResponse, dependencies=[Depends(require_roles("admin", "teacher"))])
async def update_course(
    course_id: UUID,
    data: CourseUpdate,
    user: CurrentUser = Security(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.update_course(user, course_id, data))

@router.delete("/softDelete", response_model=bool, dependencies=[Depends(require_roles("admin", "teacher"))])
async def soft_delete_course(
    course_id: UUID,
    user: CurrentUser = Security(get_current_user),
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.soft_delete_course(user, course_id))

@router.delete("/hardDelete",response_model=bool, dependencies=[Depends(require_roles("admin"))])
async def hard_delete_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.hard_delete(course_id))

@router.get("/listWithLessons", response_model=List[CourseWithLessonsResponse])
async def list_courses_with_lessons(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.get_all_with_lessons(delete_flg, skip, limit))

