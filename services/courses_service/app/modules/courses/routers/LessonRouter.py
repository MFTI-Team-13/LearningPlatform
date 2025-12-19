from typing import List

from fastapi import APIRouter, Depends, Security
from uuid import UUID

from app.modules.courses.enums import ContentType
from app.modules.courses.schemas_import import (
    LessonCreate,
    LessonUpdate,
    LessonResponse
)
from app.modules.courses.services_import import LessonService, get_lesson_service
from app.modules.courses.exceptions import handle_errors
from app.common.deps.auth import get_current_user,CurrentUser
from .requre import require_roles

router = APIRouter(prefix="/lesson")

@router.post("/create", response_model=LessonResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def create_lesson(
    data: LessonCreate,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.create_lesson(user,data))

@router.get("/list", response_model=List[LessonResponse], dependencies=[Depends(require_roles("admin"))])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: LessonService = Depends(get_lesson_service)
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.post("/getById", response_model=LessonResponse)
async def get_lesson_by_id(
    lesson_id: UUID,
    delete_flg: bool | None = None,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_id_lesson(user, lesson_id, delete_flg))

@router.post("/getByCourse", response_model=List[LessonResponse])
async def list_by_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_course_id(user, course_id, delete_flg, skip, limit))

@router.post("/getByCourseAndOrder", response_model=LessonResponse, dependencies=[Depends(require_roles("admin"))])
async def list_by_course(
    course_id: UUID,
    order_index:int,
    delete_flg: bool | None = None,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_course_and_order(user, course_id, order_index,delete_flg))

@router.post("/getByContentType", response_model=List[LessonResponse])
async def list_by_course(
    content_type: ContentType,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_content_type(user, content_type, delete_flg, skip, limit))

@router.post("/getMaxOrderIndex", response_model=int, dependencies=[Depends(require_roles("admin"))])
async def get_max_order_index(
    course_id: UUID,
    delete_flg: bool | None = None,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_max_order_index(user, course_id, delete_flg))

@router.put("/update", response_model=LessonResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def update_course(
    lesson_id: UUID,
    data: LessonUpdate,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.update_lesson(user, lesson_id, data))

@router.post("/search", response_model=List[LessonResponse])
async def search_lessons_in_course(
    course_id: UUID,
    query: str,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(
        lambda: service.search_in_course(user, course_id, query, delete_flg, skip, limit)
    )

@router.delete("/softDelete", dependencies=[Depends(require_roles("admin","teacher"))])
async def soft_delete_course(
    lesson_id: UUID,
    service: LessonService = Depends(get_lesson_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.soft_delete_lesson(user,lesson_id))

@router.delete("/hardDelete", dependencies=[Depends(require_roles("admin"))])
async def hard_delete_course(
    lesson_id: UUID,
    service: LessonService = Depends(get_lesson_service),
):
    return await handle_errors(lambda: service.hard_delete(lesson_id))
