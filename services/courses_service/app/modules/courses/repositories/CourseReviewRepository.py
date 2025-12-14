from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_session
from app.modules.courses.models_import import CourseReview


class CourseReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, review_data: dict) -> CourseReview:
        review = CourseReview(**review_data)
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def get_all(self, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> list[CourseReview]:
        query = select(CourseReview)

        if delete_flg is not None:
            query = query.where(CourseReview.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, review_id: UUID, review_data: dict) -> CourseReview | None:
        review = await self.get_by_id(review_id, False)

        if not review:
            return None

        for key, value in review_data.items():
            if hasattr(review, key):
                setattr(review, key, value)

        review.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def soft_delete(self, review_id: UUID) -> bool:
        review = await self.get_by_id(review_id, False)

        if not review:
          return False

        review.delete_flg = True
        review.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def hard_delete(self, review_id: UUID) -> bool:
        review = await self.get_by_id(review_id, None)

        if not review:
          return False

        await self.db.delete(review)
        await self.db.commit()
        return True

    async def get_by_id(self, id: UUID, delete_flg: bool | None) -> CourseReview | None:
        query = select(CourseReview).where(CourseReview.id == id)

        if delete_flg is not None:
            query = query.where(CourseReview.delete_flg == delete_flg)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_course_id(self, course_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> list[CourseReview]:
        query = select(CourseReview).where(CourseReview.course_id == course_id)

        if delete_flg is not None:
            query = query.where(CourseReview.delete_flg == delete_flg)

        query = (
            query.offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_user_id(self, user_id: UUID, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> list[CourseReview]:
        query = select(CourseReview).where(CourseReview.user_id == user_id)

        if delete_flg is not None:
            query = query.where(CourseReview.delete_flg == delete_flg)

        query = (
            query.offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_course_and_user_id(self, course_id: UUID, user_id: UUID, delete_flg: bool | None) -> CourseReview | None:
        query = select(CourseReview).where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.user_id == user_id
                )
            )


        if delete_flg is not None:
            query = query.where(CourseReview.delete_flg == delete_flg)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_average_rating(self, course_id: UUID) -> float:
        result = await self.db.execute(
            select(func.avg(CourseReview.rating))
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.is_published == True,
                    CourseReview.delete_flg == False
                )
            )
        )
        avg_rating = result.scalar()
        return float(avg_rating) if avg_rating is not None else 0.0

    async def count_by_course(self, course_id: UUID, is_published: bool | None) -> int:
        query = select(func.count(CourseReview.id)).where(
            and_(
              CourseReview.course_id == course_id,
              CourseReview.delete_flg == False
            )
        )

        if is_published is not None:
            query = query.where(CourseReview.is_published == is_published)

        result = await self.db.execute(query)
        return result.scalar()

    async def get_by_rating(self, course_id: UUID, rating: int, skip: int = 0, limit: int = 100) -> list[CourseReview]:
        result = await self.db.execute(
            select(CourseReview)
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.rating == rating,
                    CourseReview.is_published == True,
                    CourseReview.delete_flg == False
                )
            )
            .order_by(CourseReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_rating_distribution(self, course_id: UUID) -> dict:
        result = await self.db.execute(
            select(
                CourseReview.rating,
                func.count(CourseReview.id).label('count')
            )
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.is_published == True,
                    CourseReview.delete_flg == False
                )
            )
            .group_by(CourseReview.rating)
            .order_by(CourseReview.rating)
        )

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for row in result.all():
            distribution[row.rating] = row.count

        return distribution

    async def search_in_comments(self, course_id: UUID, search_term: str, delete_flg: bool | None, skip: int = 0, limit: int = 100) -> list[CourseReview]:
        query = select(CourseReview).where(
            and_(
                CourseReview.course_id == course_id,
                CourseReview.comment.ilike(f"%{search_term}%")
            )
        )

        if not delete_flg:
            query = query.where(
                and_(
                  CourseReview.is_published == True,
                  CourseReview.delete_flg == False
                )
            )
        elif delete_flg:
            query = query.where(
                and_(
                  CourseReview.is_published == False,
                  CourseReview.delete_flg == True
                )
            )

        query = (
            query.order_by(CourseReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)

        return result.scalars().all()

    async def publish(self, id: UUID) -> CourseReview | None:
        courseReview = await self.get_by_id(id, False)

        if not courseReview:
            return None

        courseReview.is_published = True
        await self.db.commit()
        return courseReview

    async def unpublish(self, id: UUID) -> CourseReview | None:
        courseReview = await self.get_by_id(id, None)

        if not courseReview:
            return None

        courseReview.is_published = False
        await self.db.commit()
        return courseReview


async def get_course_review_repository(
    db: AsyncSession = Depends(get_session),
) -> CourseReviewRepository:
    return CourseReviewRepository(db)
