from typing import List

from fastapi import APIRouter, Depends, Security
from uuid import UUID

from app.modules.courses.schemas_import import (
    TestCreate,
    TestUpdate,
    TestResponse
)
from app.modules.courses.services_import import (
    TestService,
    get_test_service
)
from app.modules.courses.exceptions import handle_errors
from app.common.deps.auth import get_current_user,CurrentUser
from .requre import require_roles

router = APIRouter()

@router.post("/create", response_model=TestResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def create_test(
    data: TestCreate,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.create_test(user, data))

@router.get("/list", response_model=List[TestResponse],dependencies=[Depends(require_roles("admin"))])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.post("/getById", response_model=TestResponse,dependencies=[Depends(require_roles("admin","teacher","student"))])
async def get_lesson_by_id(
    id: UUID,
    delete_flg: bool | None = None,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_id_test(user, id, delete_flg))

@router.post("/getByLesson", response_model=List[TestResponse],dependencies=[Depends(require_roles("admin","teacher","student"))])
async def list_by_course(
    lesson_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_lesson_id(user, lesson_id, delete_flg, skip, limit))


@router.get("/active", response_model=List[TestResponse],dependencies=[Depends(require_roles("admin","teacher","student"))])
async def list_active_tests(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(
        lambda: service.get_all_active(user,delete_flg, skip, limit)
    )


@router.get("/getByCourse", response_model=List[TestResponse],dependencies=[Depends(require_roles("admin","teacher","student"))])
async def get_tests_by_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(
        lambda: service.get_by_course_id(user, course_id, delete_flg, skip, limit)
    )


@router.put("/update", response_model=TestResponse,dependencies=[Depends(require_roles("admin","teacher"))])
async def update_test(
    test_id: UUID,
    data: TestUpdate,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.update_test(user, test_id, data))

@router.put("/activate", response_model=TestResponse,dependencies=[Depends(require_roles("admin","teacher"))])
async def activate_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.activate(user, test_id))

@router.put("/deactivate", response_model=TestResponse,dependencies=[Depends(require_roles("admin","teacher"))])
async def deactivate_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.deactivate(user, test_id))

@router.delete("/softDelete",dependencies=[Depends(require_roles("admin","teacher"))])
async def delete_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.soft_delete_test(user, test_id))

@router.delete("/hardDelete",dependencies=[Depends(require_roles("admin"))])
async def hard_delete_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.hard_delete(test_id))


