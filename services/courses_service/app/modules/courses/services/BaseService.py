# services/base_service.py

from uuid import UUID
from fastapi import HTTPException, status


class BaseService:
    def __init__(self, repo):
        self.repo = repo

    async def create(self, in_data):
        return await self.repo.create(in_data.model_dump())

    async def get_all(self, skip: int, limit: int):
        res = await self.repo.get_all(skip=skip, limit=limit)
        if not res:
            raise HTTPException(status_code=404, detail="Объекты не найдены")
        return res

    async def get_by_id(self, id: UUID):
        res = await self.repo.get_by_id(id)
        if not res:
            raise HTTPException(status_code=404, detail="Объект не найден")
        return res

    async def update(self, id: UUID, in_data):
        await self.get_by_id(id)
        update_dict = {k: v for k, v in in_data.model_dump().items() if v is not None}
        return await self.repo.update(id, update_dict)

    async def delete(self, id: UUID):
        res = await self.repo.delete(id)
        if not res:
            raise HTTPException(status_code=404, detail="Объект не найден")
