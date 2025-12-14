from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.courses.exceptions import handle_errors
from app.modules.courses.schemas_import import (
    CourseReviewCreate,
    CourseReviewResponse,
    CourseReviewUpdate,
)
from app.modules.courses.services_import import CourseReviewService, get_course_review_service

router = APIRouter(prefix="/courseReview")


@router.post("/create", response_model=CourseReviewResponse)
async def create_review(
    data: CourseReviewCreate,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.create(data))


@router.post("/getById", response_model=CourseReviewResponse)
async def get_review_by_id(
    review_id: UUID,
    delete_flg: bool | None = None,
    service: CourseReviewService = Depends(get_course_review_service),
):
    return await handle_errors(lambda: service.get_by_id(review_id, delete_flg))


@router.post("/getByCourse", response_model=list[CourseReviewResponse])
async def get_by_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseReviewService = Depends(get_course_review_service),
):
    return await handle_errors(lambda: service.get_by_course_id(course_id, delete_flg, skip, limit))


@router.post("/getByUser", response_model=list[CourseReviewResponse])
async def get_by_user(
    user_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseReviewService = Depends(get_course_review_service),
):
    return await handle_errors(lambda: service.get_by_user_id(user_id, delete_flg, skip, limit))


@router.post("/getByCourseAndUser", response_model=CourseReviewResponse)
async def get_by_course_and_user(
    course_id: UUID,
    user_id: UUID,
    delete_flg: bool | None = None,
    service: CourseReviewService = Depends(get_course_review_service),
):
    return await handle_errors(lambda: service.get_by_course_and_user_id(course_id, user_id, delete_flg))


@router.post("/getByRating", response_model=list[CourseReviewResponse])
async def get_by_rating(
    course_id: UUID,
    rating: int,
    skip: int = 0,
    limit: int = 20,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.get_by_rating(course_id, rating, skip, limit))


@router.post("/count")
async def count_reviews(
    course_id: UUID,
    is_published: bool | None = None,
    service: CourseReviewService = Depends(get_course_review_service),
):
    return await handle_errors(lambda: service.count_by_course(course_id, is_published))


@router.post("/averageRating")
async def average_rating(
    course_id: UUID,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.get_average_rating(course_id))


@router.post("/ratingDistribution")
async def rating_distribution(
    course_id: UUID,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.get_rating_distribution(course_id))


@router.post("/search", response_model=list[CourseReviewResponse])
async def search_in_comments(
    course_id: UUID,
    query: str,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.search_in_comments(course_id, query, delete_flg, skip, limit))


@router.delete("/softDelete")
async def soft_delete_review(
    review_id: UUID,
    service: CourseReviewService = Depends(get_course_review_service),
):
    return await handle_errors(lambda: service.soft_delete(review_id))


@router.delete("/hardDelete")
async def hard_delete_review(
    review_id: UUID,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.hard_delete(review_id))

@router.put("/publish", response_model=CourseReviewResponse)
async def publish(
    id: UUID,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.publish(id))

@router.put("/unpublish", response_model=CourseReviewResponse)
async def unpublish(
    id: UUID,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.unpublish(id))

@router.get("/list", response_model=list[CourseReviewResponse])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.put("/update", response_model=CourseReviewResponse)
async def update_course(
    id: UUID,
    data: CourseReviewUpdate,
    service: CourseReviewService = Depends(get_course_review_service)
):
    return await handle_errors(lambda: service.update(id, data))
