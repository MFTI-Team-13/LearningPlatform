from typing import Optional, List

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.models_import import CourseReview
from app.modules.courses.repositories_import import (
    CourseReviewRepository,
    get_course_review_repository,
    CourseRepository,
    get_course_repository
)
from app.modules.courses.schemas.CourseReviewScheme import CourseReviewCreate,CourseReviewUpdate
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)
from app.common.deps.auth import CurrentUser


class CourseReviewService(BaseService,BaseAccessCheckerCourse):

    def __init__(self, repo: CourseReviewRepository, course_repo: CourseRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, course_repo)
        self.repo = repo
        self.course_repo = course_repo

    async def find_course(self, user:CurrentUser,course_id: UUID, delete_flg:bool | None):
        course_exists = await self.course_repo.get_by_id(course_id, delete_flg=None)

        if not course_exists:
            raise NotFoundError("Курс для отзыва не существует")
        if delete_flg == False and course_exists.delete_flg == True:
            raise NotFoundError("Курс не найден")

        await self.check_course_access(user, course_exists, None)

        return course_exists

    async def create_review(self, user:CurrentUser, in_data: CourseReviewCreate) -> CourseReview:
        await self.find_course(user, in_data.course_id, delete_flg=False)
        data = in_data.model_dump()
        data["user_id"] = user.id
        return await self.create(data)

    async def get_by_id_review(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        res = await self.get_by_id(id, delete_flg)
        if "student" in user.roles and res.delete_flg == True:
          raise NotFoundError(f"Отзывы не найдены")

        await self.check_course_access(user, None, res.course_id)
        return res

    async def get_by_user_id(self, user:CurrentUser, user_id: UUID|None, delete_flg:bool | None, skip: int, limit: int) -> List[CourseReview]:
        if user_id is None:
            user_id = user.id
        res = await self.repo.get_by_user_id(user_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Отзывы не найдены")

        if "student" in user.roles:
          list_id = [review.course_id for review in res if review.delete_flg == False]
          reviews = [review for review in res if review.delete_flg == False]

          if not list_id:
            raise NotFoundError("Отзывы не найдены")

        else:
          list_id = [review.course_id for review in res]
          reviews = [review for review in res]

        courses = await self.filter_courses_access(user, None,list_id)
        allowed_course_ids = [course.id for course in courses]

        filtered_reviews = [
          r for r in reviews if r.course_id in allowed_course_ids
        ]
        return filtered_reviews

    async def get_by_course_id(self, user:CurrentUser, course_id: UUID, delete_flg:bool | None, skip: int, limit: int) -> List[CourseReview]:
        if "student" in user.roles or "teacher" in user.roles:
            delete_flg = False

        await self.find_course(user, course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Отзывы не найдены")

        return res


    async def get_by_course_and_user_id(self,user:CurrentUser,course_id: UUID,user_id: UUID | None, delete_flg:bool | None) -> Optional[CourseReview]:
        if "student" in user.roles:
            delete_flg = False

        await self.find_course(user,course_id, delete_flg=delete_flg)

        if user_id is None:
            user_id = user.id

        res = await self.repo.get_by_course_and_user_id(course_id, user_id, delete_flg)
        if not res:
            raise NotFoundError(f"Отзывы не найдены")

        return res

    async def soft_delete_review(self, user:CurrentUser, id: UUID) -> bool:
        course_review = await self.get_by_id(id, None)

        if course_review.delete_flg == True and "student" in user.roles:
            raise NotFoundError("Отзыв не найдены")

        await self.check_course_access(user, None, course_review.course_id)

        if course_review.is_published:
          await self.repo.unpublish(id)

        return await self.soft_delete(id)

    async def get_by_rating(self,user:CurrentUser,course_id: UUID,rating: int,skip: int,limit: int) -> List[CourseReview]:
        await self.find_course(user,course_id, delete_flg=False)

        res = await self.repo.get_by_rating(course_id, rating, skip, limit)

        if not res:
            raise NotFoundError(f"Отзывы не найдены c рейтингом: {rating}")

        if "student" in user.roles or "teacher" in user.roles:
            filtered_reviews = [review for review in res if not review.delete_flg]

            if not filtered_reviews:
              raise NotFoundError("Отзывы не найдены")
            else:
              return filtered_reviews

        return res

    async def count_by_course(self, user:CurrentUser,course_id: UUID, is_published: bool | None) -> int:
        await self.find_course(user, course_id, delete_flg=False)
        if "student" in user.roles or "teacher" in user.roles:
          is_published = True
        res = await self.repo.count_by_course(course_id, is_published)

        if res == 0:
            raise NotFoundError(f"Отзывы не найдены")

        return res

    async def get_average_rating(self, user:CurrentUser,course_id: UUID) -> float:
        await self.find_course(user, course_id, delete_flg=False)
        res = await self.repo.get_average_rating(course_id)

        if res == 0.0:
            raise NotFoundError(f"Отзывы не найдены")

        return res

    async def get_rating_distribution(self, user:CurrentUser,course_id: UUID) -> dict[int, int]:
        await self.find_course(user, course_id, delete_flg=False)
        dist = await self.repo.get_rating_distribution(course_id)

        if all(v == 0 for v in dist.values()):
            raise NotFoundError("Отзывы не найдены")

        return dist

    async def search_in_comments(self,user:CurrentUser,course_id: UUID,query: str,delete_flg: bool | None,skip: int,limit: int) -> List[CourseReview]:
        await self.find_course(user, course_id, delete_flg=False)
        if "student" in user.roles or "teacher" in user.roles:
            delete_flg = False
        res = await self.repo.search_in_comments(course_id, query,delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Отзывы не найдены")

        return res

    async def publish(self, user:CurrentUser,id: UUID) -> Optional[CourseReview]:
        courseReview = await self.get_by_id(id,None)

        if courseReview.user_id != user.id and "student" in user.roles:
            raise NotFoundError("Отзыв не найдены")

        await self.check_course_access(user, None, courseReview.course_id)

        if courseReview.delete_flg:
            raise ConflictError("Нельзя опубликовать удалённый отзыв")

        if courseReview.is_published:
            raise ConflictError("Отзыв уже опубликован")

        return await self.repo.publish(id)

    async def unpublish(self, user:CurrentUser, id: UUID) -> Optional[CourseReview]:
        courseReview = await self.get_by_id(id,None)

        if courseReview.user_id != user.id and "student" in user.roles:
          raise NotFoundError("Отзыв не найдены")

        await self.check_course_access(user, None, courseReview.course_id)

        if not courseReview.is_published:
            raise ConflictError("Отзыв уже скрыт")

        return await self.repo.unpublish(id)

    async def update_review(self, user:CurrentUser, id: UUID, in_data: CourseReviewUpdate) -> CourseReview:
      courseReview = await self.get_by_id(id, False)

      if courseReview.user_id != user.id and "student" in user.roles:
        raise NotFoundError("Отзыв не найдены")

      await self.check_course_access(user, None, courseReview.course_id)


      return await self.update(id, in_data)


async def get_course_review_service(
  repo: CourseReviewRepository = Depends(get_course_review_repository),
  course_repo: CourseRepository = Depends(get_course_repository)
) -> CourseReviewService:
  return CourseReviewService(repo, course_repo)
