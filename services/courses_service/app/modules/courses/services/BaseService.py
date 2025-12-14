from uuid import UUID

from app.modules.courses.exceptions import ConflictError, NotFoundError


class BaseService:
    def __init__(self, repo):
        self.repo = repo

    async def create(self, in_data):
        return await self.repo.create(in_data)

    async def get_all(self, delete_flg:bool | None, skip: int, limit: int):
        res = await self.repo.get_all(delete_flg, skip, limit)
        if not res:
            raise NotFoundError("Объекты не найден")
        return res

    async def get_by_id(self, id: UUID, delete_flg:bool | None):
        res = await self.repo.get_by_id(id, delete_flg)
        if res is None:
            raise NotFoundError("Объект не найден")
        return res


    async def update(self, id: UUID, in_data):
        await self.get_by_id(id, False)
        update_dict = {k: v for k, v in in_data.model_dump().items() if v is not None}
        if not update_dict:
            raise UpdateEmptyError()

        return await self.repo.update(id, update_dict)

    async def soft_delete(self, id: UUID) -> bool:
        obj = await self.get_by_id(id, None)

        if obj.delete_flg:
            raise ConflictError("Объект уже удалён (soft delete)")

        return await self.repo.soft_delete(id)

    async def hard_delete(self, id: UUID) -> bool:
        await self.get_by_id(id, None)
        res = await self.repo.hard_delete(id)
        return res
