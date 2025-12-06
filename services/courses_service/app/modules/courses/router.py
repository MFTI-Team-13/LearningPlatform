from fastapi import APIRouter,Depends
from learning_platform_common.utils import ResponseUtils
from app.modules.courses.schemas.CourseScheme import CourseCreate,CourseResponse
from app.modules.courses.services_import import CourseService,get_course_service
from app.common.db.session import create_tables
import asyncio

router = APIRouter()


@router.get("/")
async def root():
  return ResponseUtils.success("ok")


from fastapi import APIRouter, Depends, HTTPException, status
from learning_platform_common.utils import ResponseUtils
from app.modules.courses.schemas.CourseScheme import CourseCreate, CourseResponse
from app.modules.courses.services_import import CourseService, get_course_service
from app.modules.courses.services_import import UserService, get_user_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=CourseResponse)
async def create_course(
    data: CourseCreate,
    courses: CourseService = Depends(get_course_service),
    users: UserService = Depends(get_user_service),
):
    try:
        # -------- Проверка: существует ли пользователь-автор --------
        author = await users.get_by_id(data.author_id)
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Автор не найден"
            )

        # -------- Создание курса --------
        course = await courses.create(data)
        return course

    except HTTPException as e:
        # Перехватываем только наши намеренные ошибки
        logger.warning(f"Handled error creating course: {e.detail}")
        raise e

    except Exception as e:
        # Логируем все непредвиденные ошибки
        logger.error(f"Unexpected error creating course: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла внутренняя ошибка сервиса"
        )

