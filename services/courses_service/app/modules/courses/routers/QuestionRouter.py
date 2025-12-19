from typing import List

from fastapi import APIRouter, Depends, Security
from uuid import UUID

from app.modules.courses.schemas_import import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse
)
from app.modules.courses.services_import import (
    QuestionService,
    get_question_service
)
from app.modules.courses.exceptions import handle_errors
from app.modules.courses.enums import QuestionType
from app.common.deps.auth import get_current_user,CurrentUser
from .requre import require_roles

router = APIRouter(prefix="/question", tags=["Questions"])

@router.post("/create", response_model=QuestionResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def create_question(
    data: QuestionCreate,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.create_question(user,data))

@router.put("/update", response_model=QuestionResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def update_question(
    question_id: UUID,
    data: QuestionUpdate,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.update_question(user,question_id, data))

@router.get("/list", response_model=List[QuestionResponse], dependencies=[Depends(require_roles("admin"))])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: QuestionService = Depends(get_question_service),
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.post("/getById", response_model=QuestionResponse, dependencies=[Depends(require_roles("admin","teacher","student"))])
async def get_by_id(
    question_id: UUID,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_id_question(user,question_id, delete_flg))

@router.post("/getByTestId", response_model=List[QuestionResponse])
async def get_by_test_id(
    test_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_test_id(user,test_id, delete_flg, skip, limit))

@router.post("/getByTestAndOrder", response_model=QuestionResponse, dependencies=[Depends(require_roles("admin"))])
async def get_by_test_and_order(
    test_id: UUID,
    order_index: int,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_test_and_order(user,test_id,order_index, delete_flg))

@router.post("/getByType", response_model=List[QuestionResponse], dependencies=[Depends(require_roles("admin"))])
async def get_by_type(
    question_type: QuestionType,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_by_question_type(question_type, delete_flg, skip, limit))

@router.post("/maxOrderIndex", response_model=int, dependencies=[Depends(require_roles("admin","teacher"))])
async def get_max_order_index(
    test_id: UUID,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_max_order_index(user,test_id, delete_flg))

@router.post("/search", response_model=List[QuestionResponse], dependencies=[Depends(require_roles("admin"))])
async def search_in_test(
    test_id: UUID,
    query: str,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.search_in_test(user,test_id, query, delete_flg, skip, limit))

@router.post("/createBulk", response_model=List[QuestionResponse], dependencies=[Depends(require_roles("admin","teacher"))])
async def create_bulk(
    data: List[QuestionCreate],
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.create_bulk(user,data))

@router.post("/totalScore", response_model=int)
async def get_total_score(
    test_id: UUID,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_total_score_by_test(user,test_id, delete_flg))

@router.delete("/softDelete", dependencies=[Depends(require_roles("admin","teacher"))])
async def delete_test(
    id: UUID,
    service: QuestionService = Depends(get_question_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.soft_delete_question(user,id))

@router.delete("/hardDelete", dependencies=[Depends(require_roles("admin"))])
async def hard_delete_test(
    test_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.hard_delete(test_id))
