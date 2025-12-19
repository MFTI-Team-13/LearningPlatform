from typing import List,Optional
from uuid import UUID
from app.common.deps.auth import CurrentUser
from app.modules.courses.models_import import Course
from app.modules.courses.exceptions import (
    ForbiddenError
)


class BaseAccessCheckerCourse:
    def __init__(self, course_base_repo):
        self.course_base_repo = course_base_repo

    async def check_course_access_to_create(self, user: CurrentUser, obj_id:UUID):
        roles = set(user.roles)

        if "admin" in roles:
            return True

        elif "teacher" in roles:
            assigned = await self.course_base_repo.get_assigned_to_create_by_user(user.id, obj_id,"teacher")

            if assigned:
                return True
            raise ForbiddenError()

        elif "student" in roles:
            assigned = await self.course_base_repo.get_assigned_to_create_by_user(user.id, obj_id,"student")

            if assigned:
                return True
            raise ForbiddenError()

        raise ForbiddenError()

    async def check_course_access(self, user: CurrentUser, obj, obj_id):
        roles = set(user.roles)

        if obj is None:
          obj = await self.course_base_repo.get_by_id(obj_id, delete_flg=None)

        print(roles)
        if "admin" in roles:
            return obj

        elif "teacher" in roles:
            if hasattr(obj, "author_id") and obj.author_id == user.id and obj.delete_flg == False:
                return obj
            elif not hasattr(obj, "author_id"):
              assigned = await self.course_base_repo.get_assigned_to_user(user.id, obj.id,"teacher")

              if assigned:
                return obj
              raise ForbiddenError()
            raise ForbiddenError()

        elif "student" in roles:
            assigned = await self.course_base_repo.get_assigned_to_user(user.id, obj.id,"student")

            if assigned:
                return obj
            raise ForbiddenError()

        raise ForbiddenError()


    async def filter_courses_access(self, user: CurrentUser, objs, objs_id):
        allowed = []
        if objs_id:
          for obj_id in objs_id:
              try:
                  checked = await self.check_course_access(user, None, obj_id)
                  allowed.append(checked)
              except ForbiddenError:
                  continue
        if objs:
          for obj in objs:
              try:
                  checked = await self.check_course_access(user, obj,None)
                  allowed.append(checked)
              except ForbiddenError:
                  continue


        return allowed
