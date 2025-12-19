from typing import List,Optional

from fastapi import Depends
from uuid import UUID

from .BaseService import BaseService
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.models_import import Course
from app.modules.courses.enums import CourseLevel
from app.modules.courses.repositories_import import CourseRepository, get_course_repository
from app.modules.courses.schemas.CourseScheme import (
    CourseCreate,
    CourseUpdate
)
from app.modules.courses.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ConflictError
)
from app.common.deps.auth import CurrentUser



class CourseService(BaseService, BaseAccessCheckerCourse):
    def __init__(self, repo: CourseRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, repo)
        self.repo: CourseRepository = repo


    async def create_course(self, author_id:UUID, in_data: CourseCreate) -> Course:
        if await self.find_by_title(in_data.title, None):
            raise AlreadyExistsError("Курс с таким названием уже существует")

        dict_model = in_data.model_dump()
        dict_model['author_id'] = author_id
        return await self.create(dict_model)

    async def get_by_id_course(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        if "teacher" in user.roles or "student" in user.roles:
            delete_flg = False

        res = await self.get_by_id(id, delete_flg)

        course = await self.check_course_access(user, res, None)

        return course

    async def find_by_title(self, title: str, delete_flg: bool | None) -> Optional[Course]:
        return await self.repo.get_by_title(title, delete_flg)

    async def get_by_title(self, user:CurrentUser, title: str, delete_flg: bool | None) -> Course:
        res = await self.find_by_title(title, delete_flg)

        if res is None:
            raise NotFoundError("Курс с таким названием не найден")

        course = await self.check_course_access(user, res, None)
        return course

    async def get_by_user(self, user:CurrentUser, author_id: UUID | None,user_id: UUID | None,is_published:bool | None,level: CourseLevel | None, delete_flg:bool | None, skip: int, limit: int) -> List[Course]:
        if "admin" in user.roles and author_id is None and user_id is None:
            author_id = user.id

        if "teacher" in user.roles:
            author_id = user.id
            user_id = None
            delete_flg = False

        if "student" in user.roles:
            author_id = None
            user_id = user.id
            delete_flg = False
            is_published = True

        res = await self.repo.get_by_user(author_id,user_id,is_published,level, delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Курсы не найдены")

        return res


    async def update_course(self, user:CurrentUser, id: UUID, in_data: CourseUpdate) -> Course:
        course = await self.get_by_id(id, None)

        if course.delete_flg:
          raise ConflictError(f"Нельзя изменить удаленный курс")

        course = await self.check_course_access(user, course, None)

        if in_data.title and in_data.title != course.title:
            if await self.find_by_title(in_data.title, None):
                raise AlreadyExistsError("Курс с таким названием уже существует")

        return await self.update(id, in_data)

    async def soft_delete_course(self,user:CurrentUser,id: UUID):
      course = await self.get_by_id(id, None)

      if course.delete_flg:
        raise ConflictError(f"Курс уже удален")

      course = await self.check_course_access(user,course, None)

      if course.is_published:
        await self.repo.unpublish(id)

      return await self.soft_delete(id)



async def get_course_service(
    repo: CourseRepository = Depends(get_course_repository)
) -> CourseService:
    return CourseService(repo)
