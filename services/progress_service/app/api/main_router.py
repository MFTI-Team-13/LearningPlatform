# from fastapi import APIRouter
#
# from app.modules.progress.router import router as progress_router
#
# main_router = APIRouter()
#
# main_router.include_router(progress_router, prefix="/progress", tags=["Progress"])
#
# __all__ = ["main_router"]
# app/api/main_router.py
# app/api/main_router.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from fastapi import APIRouter

from app.modules.progress.courses.router import router as courses_router
from app.modules.progress.lessons.router import router as lessons_router

try:
    from app.modules.progress.router import router as progress_router
    HAS_PROGRESS = True
except ImportError:
    HAS_PROGRESS = False

main_router = APIRouter()

if HAS_PROGRESS:
    main_router.include_router(progress_router, prefix="/progress", tags=["Progress"])

main_router.include_router(courses_router, prefix="/progress/courses", tags=["Courses"])
main_router.include_router(lessons_router, prefix="/progress/lessons", tags=["Lessons"])

__all__ = ["main_router"]
