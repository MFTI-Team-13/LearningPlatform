from typing import List

from fastapi import APIRouter, Depends
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

router = APIRouter(prefix="/question", tags=["Questions"])

@router.post("/create", response_model=QuestionResponse)
async def create_question(
    data: QuestionCreate,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.create(data))

@router.put("/update", response_model=QuestionResponse)
async def update_question(
    question_id: UUID,
    data: QuestionUpdate,
    service: QuestionService = Depends(get_question_service),
):
    return await handle_errors(lambda: service.update(question_id, data))

@router.get("/list", response_model=List[QuestionResponse])
async def list_courses(
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    service: QuestionService = Depends(get_question_service),
):
    return await handle_errors(lambda: service.get_all(delete_flg, skip, limit))

@router.post("/getById", response_model=QuestionResponse)
async def get_by_id(
    question_id: UUID,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_by_id(question_id, delete_flg))

@router.post("/getByTestId", response_model=List[QuestionResponse])
async def get_by_test_id(
    test_id: UUID,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_by_test_id(test_id, delete_flg, skip, limit))

@router.post("/getByTestAndOrder", response_model=QuestionResponse)
async def get_by_test_and_order(
    test_id: UUID,
    order_index: int,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_by_test_and_order(test_id, order_index, delete_flg))

@router.post("/getByType", response_model=List[QuestionResponse])
async def get_by_type(
    question_type: QuestionType,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_by_question_type(question_type, delete_flg, skip, limit))

@router.post("/maxOrderIndex", response_model=int)
async def get_max_order_index(
    test_id: UUID,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_max_order_index(test_id, delete_flg))

@router.post("/search", response_model=List[QuestionResponse])
async def search_in_test(
    test_id: UUID,
    query: str,
    delete_flg: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.search_in_test(test_id, query, delete_flg, skip, limit))

@router.post("/createBulk", response_model=List[QuestionResponse])
async def create_bulk(
    data: List[QuestionCreate],
    service: QuestionService = Depends(get_question_service),
):
    return await handle_errors(lambda: service.create_bulk(data))

@router.post("/totalScore", response_model=int)
async def get_total_score(
    test_id: UUID,
    delete_flg: bool | None = None,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_total_score_by_test(test_id, delete_flg))

@router.delete("/softDelete")
async def delete_test(
    test_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.soft_delete(test_id))

@router.delete("/hardDelete")
async def hard_delete_test(
    test_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.hard_delete(test_id))

@router.get("/getWithAnswers", response_model=QuestionResponse)
async def get_with_answers(
    question_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    return await handle_errors(lambda: service.get_with_answers(question_id))
