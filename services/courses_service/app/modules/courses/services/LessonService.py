# services/lesson_service.py

from fastapi import Depends, HTTPException, status
from uuid import UUID
from app.modules.courses.repositories_import import LessonRepository, get_lesson_repository
from app.modules.courses.schemas.LessonScheme import LessonCreate, LessonUpdate
from .BaseService import BaseService


class LessonService(BaseService):

    def __init__(self, repo: LessonRepository):
        super().__init__(repo)
        self.repo: LessonRepository = repo

    async def create(self, in_data: LessonCreate):
        if in_data.order_index is None:
            max_order = await self.repo.get_max_order_index(in_data.course_id)
            in_data.order_index = (max_order or 0) + 1

        return await super().create(in_data)

    async def get_by_course_and_order(self, course_id: UUID, order_index: int):
        lesson = await self.repo.get_by_course_and_order(course_id, order_index)
        if not lesson:
            raise HTTPException(404, "Урок с таким порядком не найден")
        return lesson

    async def get_by_course_id(self, course_id: UUID, skip: int = 0, limit: int = 100):
        res = await self.repo.get_by_course_id(course_id, skip, limit)
        return res

    async def get_by_content_type(self, content_type, skip: int, limit: int):
        return await self.repo.get_by_content_type(content_type, skip, limit)

    async def get_max_order_index(self, course_id: UUID) -> int:
        return await self.repo.get_max_order_index(course_id)

    async def search_in_course(self, course_id: UUID, query: str, skip: int, limit: int):
        return await self.repo.search_in_course(course_id, query, skip, limit)

    async def count_by_course(self, course_id: UUID) -> int:
        return await self.repo.count_by_course(course_id)

    async def reorder_lessons(self, course_id: UUID, new_order: list[UUID]):
        if not new_order:
            raise HTTPException(400, "Новый порядок уроков не может быть пустым")

        lessons = await self.repo.get_by_course_id(course_id, skip=0, limit=5000)
        lesson_ids = {lesson.id for lesson in lessons}

        for lid in new_order:
            if lid not in lesson_ids:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Урок {lid} не принадлежит курсу {course_id}"
                )

        return await self.repo.reorder_lessons(course_id, new_order)

    async def soft_delete(self, id: UUID):
        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        return await self.repo.hard_delete(id)


async def get_lesson_service(
    repo: LessonRepository = Depends(get_lesson_repository),
) -> LessonService:
    return LessonService(repo)
