from typing import Optional, List
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models_import import Lesson
from app.modules.courses.enums import ContentType
from app.common.db.session import get_session


class LessonRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, lesson_id: UUID) -> Optional[Lesson]:
        result = await self.db.execute(
            select(Lesson).where(Lesson.id == lesson_id)
        )
        return result.scalar_one_or_none()

    async def get_by_course_and_order(self, course_id: UUID, order_index: int) -> Optional[Lesson]:
        result = await self.db.execute(
            select(Lesson).where(
                and_(
                    Lesson.course_id == course_id,
                    Lesson.order_index == order_index
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_course_id(self, course_id: UUID, skip: int = 0, limit: int = 100) -> List[Lesson]:
        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.order_index)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_content_type(self, content_type: ContentType, skip: int = 0, limit: int = 100) -> List[Lesson]:
        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.content_type == content_type)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, lesson_data: dict) -> Lesson:
        lesson = Lesson(**lesson_data)
        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def update(self, lesson_id: UUID, lesson_data: dict) -> Optional[Lesson]:
        lesson = await self.get_by_id(lesson_id)

        if not lesson:
            return None

        for key, value in lesson_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def soft_delete(self, lesson_id: UUID) -> bool:
        lesson = await self.get_by_id(lesson_id)

        if not lesson:
            return False

        lesson.delete_flg = True
        await self.db.commit()
        return True

    async def hard_delete(self, lesson_id: UUID) -> bool:
        lesson = await self.get_by_id(lesson_id)

        if not lesson:
            return False

        await self.db.delete(lesson)
        await self.db.commit()
        return True

    async def get_max_order_index(self, course_id: UUID) -> int:
        result = await self.db.execute(
            select(func.max(Lesson.order_index))
            .where(Lesson.course_id == course_id)
        )
        max_order = result.scalar()
        return max_order if max_order is not None else -1

    async def reorder_lessons(self, course_id: UUID, start_index: int) -> None:
        lessons = await self.get_by_course_id(course_id)
        lessons_to_reorder = [l for l in lessons if l.order_index >= start_index]

        for lesson in sorted(lessons_to_reorder, key=lambda x: x.order_index):
            lesson.order_index += 1
            await self.db.flush()

        await self.db.commit()

    async def search_in_course(self, course_id: UUID, search_term: str) -> List[Lesson]:
        result = await self.db.execute(
            select(Lesson)
            .where(
                and_(
                    Lesson.course_id == course_id,
                    or_(
                        Lesson.title.ilike(f"%{search_term}%"),
                        Lesson.short_description.ilike(f"%{search_term}%"),
                        Lesson.text_content.ilike(f"%{search_term}%")
                    )
                )
            )
            .order_by(Lesson.order_index)
        )
        return result.scalars().all()

    async def count_by_course(self, course_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Lesson.id))
            .where(Lesson.course_id == course_id)
        )
        return result.scalar()


async def get_lesson_repository(
    db: AsyncSession = Depends(get_session),
) -> LessonRepository:
    return LessonRepository(db)
