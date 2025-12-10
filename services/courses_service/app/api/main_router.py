from fastapi import APIRouter

from app.modules.courses.routers.CourseRouter import router as courses_router

main_router = APIRouter()

main_router.include_router(courses_router, prefix="/courses", tags=["Courses"])

__all__ = ["main_router"]
