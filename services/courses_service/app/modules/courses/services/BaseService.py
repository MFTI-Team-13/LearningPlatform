from uuid import UUID
from fastapi import HTTPException, status
from app.modules.courses.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ConflictError
)

class BaseService:
    def __init__(self, repo):
        self.repo = repo

    async def create(self, in_data):
        return await self.repo.create(in_data.model_dump())

    async def get_all(self, delete_flg:bool, skip: int, limit: int):
        res = await self.repo.get_all(delete_flg, skip, limit)
        print(delete_flg)
        if not res:
            raise NotFoundError(f"Объекты не найден")
        return res

    async def get_by_id(self, id: UUID, delete_flg:bool):
        res = await self.repo.get_by_id(id, delete_flg)
        if res is None:
            raise NotFoundError(f"Объект не найден")
        return res


    async def update(self, id: UUID, in_data):
        await self.get_by_id(id, False)
        update_dict = {k: v for k, v in in_data.model_dump().items() if v is not None}
        if not update_dict:
          raise UpdateEmptyError()

        return await self.repo.update(id, update_dict)

    async def soft_delete(self, id: UUID):
        course = await self.get_by_id(id, None)

        if course.delete_flg:
            raise ConflictError("Курс уже удалён (soft delete)")

        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID):
        res = await self.repo.hard_delete(id)

        if not res:
          raise NotFoundError()

        return res
