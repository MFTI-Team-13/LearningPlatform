from typing import List

from fastapi import APIRouter, Depends
from uuid import UUID

from app.modules.courses.schemas_import import (
    CourseUserCreate,
    CourseUserUpdate,
    CourseUserResponse,
    CourseUserWithCourseResponse,
CourseUserListResponse
)
from app.modules.courses.services_import import (
    CourseUserService,
    get_course_user_service
)
from app.modules.courses.exceptions import handle_errors

router = APIRouter(prefix="/courseUser")


@router.post("/create", response_model=CourseUserResponse)
async def create_course_user(
    data: CourseUserCreate,
    service: CourseUserService = Depends(get_course_user_service)
):
    return await handle_errors(lambda: service.create(data))

@router.get("/list", response_model=List[CourseUserResponse])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseUserService = Depends(get_course_user_service)
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))


@router.post("/getById", response_model=CourseUserResponse)
async def get_course_user_by_id(
    id: UUID,
    delete_flg: bool | None = None,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.get_by_id(id, delete_flg))


@router.post("/getByCourse", response_model=List[CourseUserResponse])
async def get_by_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.get_by_course_id(course_id, delete_flg, skip, limit))


@router.post("/getByUser", response_model=List[CourseUserResponse])
async def get_by_user(
    user_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.get_by_user_id(user_id, delete_flg, skip, limit))


@router.post("/getByCourseAndUser", response_model=CourseUserResponse)
async def get_by_course_and_user(
    course_id: UUID,
    user_id: UUID,
    delete_flg: bool | None = None,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.get_by_course_and_user_id(course_id, user_id, delete_flg))


@router.post("/getActiveByUser", response_model=List[CourseUserResponse])
async def get_active_by_user(
    user_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.get_active_by_user_id(user_id, delete_flg, skip, limit))


@router.put("/activate")
async def activate_course_user(
    id: UUID,
    service: CourseUserService = Depends(get_course_user_service)
):
    return await handle_errors(lambda: service.activate(id))


@router.put("/deactivate")
async def deactivate_course_user(
    id: UUID,
    service: CourseUserService = Depends(get_course_user_service)
):
    return await handle_errors(lambda: service.deactivate(id))


@router.delete("/softDelete")
async def soft_delete_course_user(
    id: UUID,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.soft_delete(id))


@router.delete("/hardDelete")
async def hard_delete_course_user(
    id: UUID,
    service: CourseUserService = Depends(get_course_user_service),
):
    return await handle_errors(lambda: service.hard_delete(id))

@router.post("/getWithCourse")
async def get_with_course_and_course_user(
    user_id:UUID,
    course_id:UUID|None = None,
    delete_flg:bool|None = None,
    service: CourseUserService = Depends(get_course_user_service)
):
    try:
      return await handle_errors(
        lambda: service.get_with_courseUser_and_course(
            user_id=user_id,
            course_id=course_id,
            delete_flg=delete_flg
        )
      )
    except Exception as e:
        # Для дебага: выводим ошибку
        print(f"Error in router: {e}")
        print(f"Result type: {type(result) if 'result' in locals() else 'N/A'}")
        raise
