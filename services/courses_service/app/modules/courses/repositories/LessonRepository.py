from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_session
from app.modules.courses.enums import ContentType
from app.modules.courses.models_import import Lesson


class LessonRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, lesson_data: dict) -> Lesson:
        lesson = Lesson(**lesson_data)
        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def get_by_id(self, id: UUID,  delete_flg: bool | None) -> Lesson | None:
        query = select(Lesson).where(Lesson.id == id)

        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_course_id(self, course_id: UUID, delete_flg: bool | None, skip: int, limit: int) -> list[Lesson]:
        query = select(Lesson).where(Lesson.course_id == course_id)

        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        query = (
            query.order_by(Lesson.order_index)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_course_and_order(self, course_id: UUID, order_index: int, delete_flg: bool | None) -> Lesson | None:
        query = (
            select(Lesson)
            .where(
                and_(
                  Lesson.course_id == course_id,
                  Lesson.order_index == order_index
                )
            )
        )

        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, delete_flg: bool | None, skip: int, limit: int) -> list[Lesson]:
        query = select(Lesson)

        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_content_type(self, content_type: ContentType,delete_flg: bool | None, skip: int, limit: int) -> list[Lesson]:
        query = select(Lesson).where(Lesson.content_type == content_type)

        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_max_order_index(self, course_id: UUID, delete_flg: bool | None) -> int:
        query = select(func.max(Lesson.order_index)).where(Lesson.course_id == course_id)

        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        result = await self.db.execute(query)
        max_order = result.scalar()
        return max_order if max_order is not None else -1

    async def update(self, lesson_id: UUID, lesson_data: dict) -> Lesson | None:
        lesson = await self.get_by_id(lesson_id, False)

        if not lesson:
            return None

        for key, value in lesson_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        lesson.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def soft_delete(self, lesson_id: UUID) -> bool:
        lesson = await self.get_by_id(lesson_id, delete_flg = False)

        if not lesson:
            return False

        lesson.delete_flg = True
        lesson.updated_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def hard_delete(self, lesson_id: UUID) -> bool:
        lesson = await self.get_by_id(lesson_id,None)

        if not lesson:
            return False

        await self.db.delete(lesson)
        await self.db.commit()
        return True

    async def search_in_course(self, course_id: UUID, search_term: str, delete_flg: bool | None,skip: int, limit: int) -> list[Lesson]:
        query = select(Lesson).where(
            and_(
                Lesson.course_id == course_id,
                or_(
                    Lesson.title.ilike(f"%{search_term}%"),
                    Lesson.short_description.ilike(f"%{search_term}%"),
                    Lesson.text_content.ilike(f"%{search_term}%")
                )
            )
        )
        if delete_flg is not None:
            query = query.where(Lesson.delete_flg == delete_flg)

        query = (
            query.order_by(Lesson.order_index)
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.scalars().all()


async def get_lesson_repository(
    db: AsyncSession = Depends(get_session),
) -> LessonRepository:
    return LessonRepository(db)
