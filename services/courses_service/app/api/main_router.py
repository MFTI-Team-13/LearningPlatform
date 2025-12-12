from fastapi import APIRouter

from app.modules.courses.routers.CourseRouter import router as courses_router
from app.modules.courses.routers.LessonRouter import router as lesson_router
from app.modules.courses.routers.TestRouter import router as test_router
from app.modules.courses.routers.QuestionRouter import router as question_router
from app.modules.courses.routers.AnswerRouter import router as answer_router
from app.modules.courses.routers.CourseReviewRouter import router as course_review_router
from app.modules.courses.routers.CourseUserRouter import router as course_user_router

main_router = APIRouter()

main_router.include_router(courses_router, prefix="/courses", tags=["Courses"])
main_router.include_router(lesson_router, prefix="/lesson", tags=["Lessons"])
main_router.include_router(test_router, prefix="/test", tags=["Tests"])
main_router.include_router(question_router, prefix="/question", tags=["Questions"])
main_router.include_router(answer_router, prefix="/answer", tags=["Answer"])
main_router.include_router(course_review_router, prefix="/courseReview", tags=["CourseReviews"])
main_router.include_router(course_user_router, prefix="/courseUser", tags=["CourseUsers"])

__all__ = ["main_router"]
