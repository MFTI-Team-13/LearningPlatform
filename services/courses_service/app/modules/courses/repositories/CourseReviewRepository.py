from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from fastapi import Depends
from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import CourseReview
from app.common.db.session import get_session


class CourseReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, delete_flg:bool = True) -> Optional[CourseReview]:
        result = await self.db.execute(
            select(CourseReview).where(
                and_(
                    CourseReview.id == id,
                    CourseReview.delete_flg == delete_flg
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_course_and_user(self, course_id: UUID, user_id: UUID) -> Optional[CourseReview]:
        result = await self.db.execute(
            select(CourseReview).where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_course_id(self, course_id: UUID, skip: int = 0, limit: int = 100,
                                                         only_published: bool = True) -> List[CourseReview]:
        query = select(CourseReview).where(CourseReview.course_id == course_id)

        if only_published:
            query = query.where(CourseReview.is_published == True)

        result = await self.db.execute(
            query.order_by(CourseReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[CourseReview]:
        result = await self.db.execute(
            select(CourseReview)
            .where(CourseReview.user_id == user_id)
            .order_by(CourseReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_rating(self, course_id: UUID, rating: int, skip: int = 0, limit: int = 100) -> List[CourseReview]:
        result = await self.db.execute(
            select(CourseReview)
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.rating == rating,
                    CourseReview.is_published == True
                )
            )
            .order_by(CourseReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, review_data: dict) -> CourseReview:
        review = CourseReview(**review_data)
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def update(self, review_id: UUID, review_data: dict) -> Optional[CourseReview]:
        review = await self.get_by_id(review_id)

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
        review = await self.get_by_id(review_id)

        if not review:
          return False

        review.delete_flg = True
        review.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def hard_delete(self, review_id: UUID) -> bool:
        review = await self.get_by_id(review_id)

        if not review:
          return False

        await self.db.delete(review)
        await self.db.commit()
        return True

    async def count_by_course(self, course_id: UUID, only_published: bool = True) -> int:
        query = select(func.count(CourseReview.id)).where(CourseReview.course_id == course_id)

        if only_published:
            query = query.where(CourseReview.is_published == True)

        result = await self.db.execute(query)
        return result.scalar()

    async def get_average_rating(self, course_id: UUID) -> float:
        result = await self.db.execute(
            select(func.avg(CourseReview.rating))
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.is_published == True
                )
            )
        )
        avg_rating = result.scalar()
        return float(avg_rating) if avg_rating is not None else 0.0

    async def get_rating_distribution(self, course_id: UUID) -> dict:
        result = await self.db.execute(
            select(
                CourseReview.rating,
                func.count(CourseReview.id).label('count')
            )
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.is_published == True
                )
            )
            .group_by(CourseReview.rating)
            .order_by(CourseReview.rating)
        )

        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for row in result.all():
            distribution[row.rating] = row.count

        return distribution

    async def toggle_publish(self, review_id: UUID) -> bool:
        review = await self.get_by_id(review_id)

        if not review:
            return False

        review.is_published = not review.is_published
        await self.db.commit()
        return True

    async def search_in_comments(self, course_id: UUID, search_term: str,
                                                             skip: int = 0, limit: int = 100) -> List[CourseReview]:
        result = await self.db.execute(
            select(CourseReview)
            .where(
                and_(
                    CourseReview.course_id == course_id,
                    CourseReview.comment.ilike(f"%{search_term}%"),
                    CourseReview.is_published == True
                )
            )
            .order_by(CourseReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_reviews(self, days: int = 7, limit: int = 50) -> List[CourseReview]:
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(CourseReview)
            .where(
                and_(
                    CourseReview.created_at >= cutoff_date,
                    CourseReview.is_published == True
                )
            )
            .order_by(CourseReview.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_course_review_repository(
    db: AsyncSession = Depends(get_session),
) -> CourseReviewRepository:
    return CourseReviewRepository(db)
