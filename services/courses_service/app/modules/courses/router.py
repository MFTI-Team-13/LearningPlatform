# from fastapi import APIRouter,Depends, HTTPException, status
# from learning_platform_common.utils import ResponseUtils
# from app.modules.courses.schemas_import import CourseCreate,CourseResponse
# from app.modules.courses.services_import import CourseService,get_course_service
# from app.common.db.session import create_tables
# from typing import List
# import logging
#
# router = APIRouter()
# logger = logging.getLogger(__name__)
#
#
# @router.get("/")
# async def root():
#   return ResponseUtils.success("ok")
#
#
# @router.post("/course/create", response_model=CourseResponse)
# async def create_course(
#   data: CourseCreate,
#   courses: CourseService = Depends(get_course_service)
# ):
#   try:
#     course = await courses.create(data)
#     return course
#
#   except HTTPException as e:
#     logger.warning(f"Ошибка при создании курса: {e.detail}")
#     raise e
#
#   except Exception as e:
#     logger.error(f"Непредвиденная ошибка при создании курса: {e}", exc_info=True)
#     raise HTTPException(
#       status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#       detail="Произошла непредвиденная ошибка на стороне сервера. "
#              "Мы уже работаем над её устранением."
#     )
#
# @router.get("/course/list", response_model=List[CourseResponse])
# async def get_all_courses(
#     skip: int = 0,
#     limit: int = 100,
#     include_deleted: bool = False,
#     courses: CourseService = Depends(get_course_service)
# ):
#     try:
#         result = await courses.get_all(skip=skip, limit=limit, include_deleted=include_deleted)
#         return result
#
#     except HTTPException as e:
#         logger.warning(f"Ошибка при получении списка курсов: {e.detail}")
#         raise e
#
#     except Exception as e:
#         logger.error(f"Непредвиденная ошибка при получении списка курсов: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Не удалось получить список курсов из-за внутренней ошибки сервера."
#         )
#
#
