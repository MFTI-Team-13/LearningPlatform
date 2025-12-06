from fastapi import Depends, HTTPException
from uuid import UUID

from app.modules.courses.repositories_import import CourseReviewRepository, get_course_review_repository
from app.modules.courses.schemas.CourseReviewScheme import (
    CourseReviewCreate,
    CourseReviewUpdate,
    CourseReviewResponse
)
from .BaseService import BaseService


class CourseReviewService(BaseService):

    def __init__(self, repo: CourseReviewRepository):
        super().__init__(repo)
        self.repo = repo

    async def create(self, in_data: CourseReviewCreate) -> CourseReviewResponse:
        return await super().create(in_data)

    async def get_by_id(self, review_id: UUID) -> CourseReviewResponse:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(404, "Отзыв не найден")
        return review

    async def get_by_course_and_user(
        self,
        course_id: UUID,
        user_id: UUID
    ) -> CourseReviewResponse:
        res = await self.repo.get_by_course_and_user(course_id, user_id)
        if not res:
            raise HTTPException(404, "Отзыв не найден")
        return res

    async def get_by_course_id(
        self,
        course_id: UUID,
        skip: int,
        limit: int
    ) -> list[CourseReviewResponse]:
        return await self.repo.get_by_course_id(course_id, skip, limit)

    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int,
        limit: int
    ) -> list[CourseReviewResponse]:
        return await self.repo.get_by_user_id(user_id, skip, limit)

    async def get_by_rating(
        self,
        rating: int,
        skip: int,
        limit: int
    ) -> list[CourseReviewResponse]:
        return await self.repo.get_by_rating(rating, skip, limit)

    async def count_by_course(self, course_id: UUID) -> int:
        return await self.repo.count_by_course(course_id)

    async def get_average_rating(self, course_id: UUID) -> float:
        return await self.repo.get_average_rating(course_id)

    async def get_rating_distribution(self, course_id: UUID) -> dict[int, int]:
        return await self.repo.get_rating_distribution(course_id)

    async def toggle_publish(self, review_id: UUID) -> CourseReviewResponse:
        review = await self.get_by_id(review_id)
        new_state = not review.is_published
        return await self.repo.set_publish_state(review_id, new_state)

    async def search_in_comments(
        self,
        course_id: UUID,
        query: str,
        skip: int,
        limit: int
    ) -> list[CourseReviewResponse]:
        return await self.repo.search_in_comments(course_id, query, skip, limit)

    async def get_recent_reviews(
        self,
        limit: int
    ) -> list[CourseReviewResponse]:
        return await self.repo.get_recent_reviews(limit)

    async def soft_delete(self, id: UUID) -> CourseReviewResponse:
        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID) -> None:
        return await self.repo.hard_delete(id)


async def get_course_review_service(
    repo: CourseReviewRepository = Depends(get_course_review_repository)
) -> CourseReviewService:
    return CourseReviewService(repo)
