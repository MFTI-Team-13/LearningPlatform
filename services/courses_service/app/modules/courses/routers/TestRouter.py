from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.courses.exceptions import handle_errors
from app.modules.courses.schemas_import import TestCreate, TestResponse, TestUpdate
from app.modules.courses.services_import import TestService, get_test_service

router = APIRouter(prefix="/test")

@router.post("/create", response_model=TestResponse)
async def create_test(
    data: TestCreate,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.create(data))

@router.get("/list", response_model=list[TestResponse])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.post("/getById", response_model=TestResponse)
async def get_lesson_by_id(
    id: UUID,
    delete_flg: bool | None = None,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.get_by_id(id, delete_flg))

@router.post("/getByLesson", response_model=list[TestResponse])
async def list_by_course(
    lesson_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.get_by_lesson_id(lesson_id, delete_flg, skip, limit))


@router.get("/active", response_model=list[TestResponse])
async def list_active_tests(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(
        lambda: service.get_all_active(delete_flg, skip, limit)
    )


@router.get("/getByCourse", response_model=list[TestResponse])
async def get_tests_by_course(
    course_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(
        lambda: service.get_by_course_id(course_id, delete_flg, skip, limit)
    )


@router.get("/search", response_model=list[TestResponse])
async def search_tests(
    query: str,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(
        lambda: service.search(query, delete_flg, skip, limit)
    )

@router.put("/update", response_model=TestResponse)
async def update_test(
    test_id: UUID,
    data: TestUpdate,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.update(test_id, data))

@router.put("/activate", response_model=TestResponse)
async def activate_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.activate(test_id))

@router.put("/deactivate", response_model=TestResponse)
async def deactivate_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.deactivate(test_id))

@router.delete("/softDelete")
async def delete_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.soft_delete(test_id))

@router.delete("/hardDelete")
async def hard_delete_test(
    test_id: UUID,
    service: TestService = Depends(get_test_service)
):
    return await handle_errors(lambda: service.hard_delete(test_id))


