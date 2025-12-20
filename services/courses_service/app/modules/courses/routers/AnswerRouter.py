from typing import List

from fastapi import APIRouter, Depends, Security
from uuid import UUID

from app.modules.courses.schemas_import import (
    AnswerCreate,
    AnswerUpdate,
    AnswerResponse
)
from app.modules.courses.services_import import (
    AnswerService,
    get_answer_service
)
from app.modules.courses.exceptions import handle_errors
from app.common.deps.auth import get_current_user,CurrentUser
from .requre import require_roles

router = APIRouter()


@router.post("/create", response_model=AnswerResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def create_answer(
    data: AnswerCreate,
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.create_answer(user,data))


@router.post("/createBulk", response_model=List[AnswerResponse], dependencies=[Depends(require_roles("admin","teacher"))])
async def create_answers_bulk(
    answers: List[AnswerCreate],
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.create_bulk(user,answers))

@router.get("/list", response_model=List[AnswerResponse], dependencies=[Depends(require_roles("admin"))])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: AnswerService = Depends(get_answer_service),
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.post("/getById", response_model=AnswerResponse, dependencies=[Depends(require_roles("admin","teacher","student"))])
async def get_answer_by_id(
    answer_id: UUID,
    delete_flg: bool | None = None,
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.get_by_id_answer(user,answer_id, delete_flg))


@router.post("/getByQuestionAndOrder", response_model=AnswerResponse, dependencies=[Depends(require_roles("admin"))])
async def get_by_question_and_order(
    question_id: UUID,
    order_index: int,
    delete_flg: bool | None = None,
    service: AnswerService = Depends(get_answer_service),
):
    return await handle_errors(
        lambda: service.get_by_question_and_order(question_id, order_index, delete_flg)
    )


@router.post("/getByQuestionId", response_model=List[AnswerResponse], dependencies=[Depends(require_roles("admin","teacher","student"))])
async def get_by_question_id(
    question_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 100,
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(
        lambda: service.get_by_question_id(user,question_id, delete_flg, skip, limit)
    )


@router.post("/getCorrectByQuestion", response_model=List[AnswerResponse], dependencies=[Depends(require_roles("admin","teacher"))])
async def get_correct_answers_by_question(
    question_id: UUID,
    is_correct: bool | None = None,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 100,
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(
        lambda: service.get_correct_answers_by_question(user,question_id, is_correct, delete_flg, skip, limit)
    )


@router.post("/maxOrderIndex", response_model=int, dependencies=[Depends(require_roles("admin"))])
async def get_max_order_index(
    question_id: UUID,
    delete_flg: bool | None = None,
    service: AnswerService = Depends(get_answer_service)
):
    return await handle_errors(lambda: service.get_max_order_index(question_id, delete_flg))


@router.post("/count", response_model=int, dependencies=[Depends(require_roles("admin"))])
async def count_by_question(
    question_id: UUID,
    delete_flg: bool | None = None,
    service: AnswerService = Depends(get_answer_service)
):
    return await handle_errors(lambda: service.count_by_question(question_id, delete_flg))


@router.put("/update", response_model=AnswerResponse, dependencies=[Depends(require_roles("admin","teacher"))])
async def update_answer(
    answer_id: UUID,
    data: AnswerUpdate,
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.update_answer(user,answer_id, data))


@router.delete("/softDelete", response_model=bool, dependencies=[Depends(require_roles("admin","teacher"))])
async def soft_delete_answer(
    answer_id: UUID,
    service: AnswerService = Depends(get_answer_service),
    user: CurrentUser = Security(get_current_user)
):
    return await handle_errors(lambda: service.soft_delete_answer(user,answer_id))


@router.delete("/hardDelete", response_model=bool, dependencies=[Depends(require_roles("admin"))])
async def hard_delete_answer(
    answer_id: UUID,
    service: AnswerService = Depends(get_answer_service)
):
    return await handle_errors(lambda: service.hard_delete(answer_id))
