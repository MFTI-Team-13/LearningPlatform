
from fastapi import APIRouter, Depends
from uuid import UUID
from typing import List
from app.middleware.auth import require_roles
from learning_platform_common.utils import ResponseUtils
from app.modules.courses.schemas.CourseScheme import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseWithLessonsResponse
)
from app.modules.courses.services_import import CourseService, get_course_service
from app.modules.courses.exceptions import NotFoundError, AlreadyExistsError,handle_errors
from app.modules.courses.enums import CourseLevel

router = APIRouter(prefix="/course")

@router.post("/create", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.create(data))

@router.post("/getById", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.get_by_id(course_id,delete_flg))

@router.post("/getByTitle", response_model=CourseResponse)
async def get_course(
    title: str,
    delete_flg: bool | None = None,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.get_by_title(title,delete_flg))


@router.get("/list", response_model=List[CourseResponse])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.get("/auth", dependencies=[Depends(require_roles("admin", "teacher"))])
async def root():
  return ResponseUtils.success("ok")


@router.put("/update", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    data: CourseUpdate,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.update(course_id, data))

@router.delete("/softDelete")
async def soft_delete_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.soft_delete(course_id))

@router.delete("/hardDelete")
async def hard_delete_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.hard_delete(course_id))

@router.post("/getByAuthor", response_model=list[CourseResponse])
async def get_by_author(
    author_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.get_by_author(author_id, delete_flg, skip, limit))

@router.post("/getPublished", response_model=list[CourseResponse])
async def get_published(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.get_published(delete_flg,skip, limit))

@router.post("/getByLevel", response_model=list[CourseResponse])
async def get_by_level(
    level: CourseLevel,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.get_by_level(level,delete_flg, skip, limit))

@router.put("/publish", response_model=CourseResponse)
async def publish_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.publish(course_id))

@router.put("/unpublish", response_model=CourseResponse)
async def unpublish_course(
    course_id: UUID,
    service: CourseService = Depends(get_course_service),
):
    return await handle_errors(lambda: service.unpublish(course_id))

@router.get("/listWithLessons", response_model=List[CourseWithLessonsResponse])
async def list_courses_with_lessons(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: CourseService = Depends(get_course_service)
):
    return await handle_errors(lambda: service.get_all_with_lessons(delete_flg, skip, limit))

