from uuid import UUID

from fastapi import Depends

from app.modules.courses.exceptions import ConflictError, NotFoundError
from app.modules.courses.models_import import CourseReview
from app.modules.courses.repositories_import import (
    CourseRepository,
    CourseReviewRepository,
    get_course_repository,
    get_course_review_repository,
)
from app.modules.courses.schemas.CourseReviewScheme import CourseReviewCreate

from .BaseService import BaseService


class CourseReviewService(BaseService):

    def __init__(self, repo: CourseReviewRepository, course_repo: CourseRepository):
        super().__init__(repo)
        self.repo = repo
        self.course_repo = course_repo

    async def find_course(self, course_id: UUID, delete_flg:bool | None):
        course_exists = await self.course_repo.get_by_id(course_id, delete_flg=None)

        if not course_exists:
            raise NotFoundError("Курс для отзыва не существует")
        if delete_flg == False and course_exists.delete_flg == True:
            raise NotFoundError("Курс не найден")

        return course_exists

    async def create(self, in_data: CourseReviewCreate) -> CourseReview:
        await self.find_course(in_data.course_id, delete_flg=False)
        return await super().create(in_data)

    async def get_by_user_id(self, user_id: UUID, delete_flg:bool | None, skip: int, limit: int) -> list[CourseReview]:
        res = await self.repo.get_by_user_id(user_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError("Отзывы не найдены")

        return res

    async def get_by_course_id(self, course_id: UUID, delete_flg:bool | None, skip: int, limit: int) -> list[CourseReview]:
        await self.find_course(course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError("Отзывы не найдены")

        return res


    async def get_by_course_and_user_id(self,course_id: UUID,user_id: UUID, delete_flg:bool | None) -> CourseReview | None:
        await self.find_course(course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_and_user_id(course_id, user_id, delete_flg)
        if not res:
            raise NotFoundError("Отзывы не найдены")

        return res

    async def soft_delete(self, id: UUID) -> bool:
        courseReview = await self.get_by_id(id, None)

        if courseReview.is_published:
          await self.repo.unpublish(id)

        return await super().soft_delete(id)

    async def get_by_rating(self,course_id: UUID,rating: int,skip: int,limit: int) -> list[CourseReview]:
        await self.find_course(course_id, delete_flg=False)
        res = await self.repo.get_by_rating(course_id, rating, skip, limit)

        if not res:
            raise NotFoundError(f"Отзывы не найдены c рейтингом: {rating}")

        return res

    async def count_by_course(self, course_id: UUID, is_published: bool | None) -> int:
        await self.find_course(course_id, delete_flg=False)
        res = await self.repo.count_by_course(course_id, is_published)

        if res == 0:
            raise NotFoundError("Отзывы не найдены")

        return res

    async def get_average_rating(self, course_id: UUID) -> float:
        await self.find_course(course_id, delete_flg=False)
        res = await self.repo.get_average_rating(course_id)

        if res == 0.0:
            raise NotFoundError("Отзывы не найдены")

        return res

    async def get_rating_distribution(self, course_id: UUID) -> dict[int, int]:
        await self.find_course(course_id, delete_flg=False)
        dist = await self.repo.get_rating_distribution(course_id)

        if all(v == 0 for v in dist.values()):
            raise NotFoundError("Отзывы не найдены")

        return dist

    async def search_in_comments(self,course_id: UUID,query: str,delete_flg: bool | None,skip: int,limit: int) -> list[CourseReview]:
        await self.find_course(course_id, delete_flg=delete_flg)
        res = await self.repo.search_in_comments(course_id, query,delete_flg, skip, limit)

        if not res:
            raise NotFoundError("Отзывы не найдены")

        return res

    async def publish(self, id: UUID) -> CourseReview | None:
        courseReview = await self.get_by_id(id,None)

        if courseReview.delete_flg:
            raise ConflictError("Нельзя опубликовать удалённый отзыв")

        if courseReview.is_published:
            raise ConflictError("Отзыв уже опубликован")

        return await self.repo.publish(id)

    async def unpublish(self, id: UUID) -> CourseReview | None:
        courseReview = await self.get_by_id(id,None)

        if not courseReview.is_published:
            raise ConflictError("Отзыв уже скрыт")

        return await self.repo.unpublish(id)

async def get_course_review_service(
  repo: CourseReviewRepository = Depends(get_course_review_repository),
  course_repo: CourseRepository = Depends(get_course_repository)
) -> CourseReviewService:
  return CourseReviewService(repo, course_repo)
