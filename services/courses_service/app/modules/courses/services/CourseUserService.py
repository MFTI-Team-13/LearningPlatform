from typing import Optional, List

from fastapi import Depends, HTTPException
from uuid import UUID

from .BaseService import BaseService
from .BaseAccessCheckerCourse import BaseAccessCheckerCourse
from app.modules.courses.models_import import CourseUser
from app.modules.courses.repositories_import import (
    CourseUserRepository,
    get_course_user_repository,
    CourseRepository,
    get_course_repository
)
from app.modules.courses.schemas.CourseUserScheme import (
    CourseUserCreate,CourseResponse, CourseUserWithCourseResponse
)
from app.modules.courses.exceptions import (
    NotFoundError,
    ConflictError
)
from app.common.deps.auth import CurrentUser

class CourseUserService(BaseService,BaseAccessCheckerCourse):

    def __init__(self, repo: CourseUserRepository, course_repo: CourseRepository):
        BaseService.__init__(self, repo)
        BaseAccessCheckerCourse.__init__(self, course_repo)
        self.repo = repo
        self.course_repo = course_repo

    async def find_course(self, user:CurrentUser, course_id: UUID, delete_flg:bool | None):
        course_exists = await self.course_repo.get_by_id(course_id, delete_flg=None)

        if not course_exists:
            raise NotFoundError("Курс не существует")
        if delete_flg == False and course_exists.delete_flg == True:
            raise NotFoundError("Курс не найден")
        await self.check_course_access(user, course_exists, None)
        return course_exists

    async def create_relation(self, user:CurrentUser, in_data: CourseUserCreate) -> CourseUser:
        await self.find_course(user,in_data.course_id, delete_flg=False)
        return await self.create(in_data.model_dump())

    async def get_by_id_rel(self,user:CurrentUser, id: UUID, delete_flg:bool | None):
        res = await self.get_by_id(id, delete_flg)
        if "student" in user.roles and (res.delete_flg == True or res.is_active == False):
          raise NotFoundError(f"Назначенные курсы не найдены")

        await self.check_course_access(user, None, res.course_id)
        return res

    async def get_by_course_id(self, user:CurrentUser,course_id: UUID, delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        if "teacher" in user.roles:
            delete_flg = False

        await self.find_course(user, course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_id(course_id, delete_flg, skip, limit)

        if not res:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_by_user_id(self, user_id: UUID, delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:

        res = await self.repo.get_by_user_id(user_id, delete_flg, skip, limit)

        if not res:
            raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_with_courseUser_and_course(self,user:CurrentUser, user_id: UUID,course_id: UUID|None, delete_flg:bool | None) -> List[CourseUser]:
        if user_id is None:
            user_id = user.id

        if "student" in user.roles:
            delete_flg = False

        if course_id is not None:
            await self.find_course(user,course_id, delete_flg=delete_flg)

        res = await self.repo.get_with_courseUser_and_course(user_id, course_id,delete_flg)


        if not res:
            raise NotFoundError(f"Назначенные курсы не найдены")


        result_list = []
        for course_user, course in res:
          if "student" in user.roles and (course_user.is_active == False or course.is_published == False):
            continue

          course_user.course = course
          result_list.append(
            CourseUserWithCourseResponse.model_validate(course_user)
          )
        if not result_list:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return result_list

    async def get_by_course_and_user_id(self, user:CurrentUser,course_id: UUID, user_id: UUID, delete_flg:bool | None) -> Optional[CourseUser]:
        if user_id is None:
          user_id = user.id

        await self.find_course(user, course_id, delete_flg=delete_flg)

        res = await self.repo.get_by_course_and_user_id(course_id, user_id, delete_flg)
        if not res:
            raise NotFoundError(f"Назначенные курсы не найдены")

        if "student" in user.roles and (res.delete_flg == True or res.is_active == False):
          raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def get_active_by_user_id(self, user:CurrentUser,user_id: UUID, delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        if user_id is None:
            user_id = user.id
        if "student" in user.roles:
            delete_flg = False

        res = await self.repo.get_active_by_user_id(user_id, delete_flg,skip, limit)

        if not res:
          raise NotFoundError(f"Назначенные курсы не найдены")

        courses_id = set([rel.course_id for rel in res])
        allowed_courses = await self.filter_courses_access(user, None, courses_id)
        allowed_course_ids = [course.id for course in allowed_courses if course.is_published]

        filtered_rel = [
          rel for rel in res
          if rel.course_id in allowed_course_ids
        ]

        if not filtered_rel:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return filtered_rel

    async def get_all_active(self, is_active:bool,delete_flg:bool | None,skip: int, limit: int) -> List[CourseUser]:
        res =  await self.repo.get_active(is_active, delete_flg, skip, limit)

        if not res:
          raise NotFoundError(f"Назначенные курсы не найдены")

        return res

    async def activate(self, id: UUID):
        courseUser = await self.get_by_id(id, None)

        if courseUser.delete_flg:
          raise ConflictError("Нельзя активировать удалённое назначение")

        if courseUser.is_active:
            raise ConflictError("Назначенный курс уже активен для пользователя")

        return await self.repo.activate(id)

    async def deactivate(self, id: UUID):
        courseUser = await self.get_by_id(id, None)

        if not courseUser.is_active:
          raise ConflictError("Назначенный курс уже не активен для пользователя")

        return await self.repo.deactivate(id)

async def get_course_user_service(
  repo: CourseUserRepository = Depends(get_course_user_repository),
  course_repo: CourseRepository = Depends(get_course_repository)
) -> CourseUserService:
  return CourseUserService(repo, course_repo)
