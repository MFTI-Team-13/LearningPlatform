import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from unittest.mock import AsyncMock

from app.modules.courses.routers.CourseRouter import router
from app.common.deps.auth import get_current_user
from app.modules.courses.services_import import get_course_service
from datetime import datetime
from uuid import uuid4
from app.modules.courses.schemas_import import CourseResponse
from app.modules.courses.enums import CourseLevel

class FakeUser:
    def __init__(self, roles: list[str]):
        self.id: UUID = uuid4()
        self.roles: list[str] = roles


@pytest.fixture
def course_response() -> CourseResponse:
    return CourseResponse.model_construct(
        id=uuid4(),
        title="Test course",
    )




@pytest.fixture
def admin_user() -> FakeUser:
    return FakeUser(["admin"])

@pytest.fixture
def mock_course_service(course_response: CourseResponse) -> AsyncMock:
    service = AsyncMock()

    service.create_course.return_value = course_response
    service.get_by_id_course.return_value = course_response
    service.get_by_title.return_value = course_response
    service.update_course.return_value = course_response

    service.get_all.return_value = [course_response]
    service.get_by_user.return_value = [course_response]

    service.soft_delete_course.return_value = True
    service.hard_delete.return_value = True

    return service

# @pytest.fixture
# def mock_course_service() -> AsyncMock:
#     service: AsyncMock = AsyncMock()
#     service.create_course.return_value = {"id": uuid4(), "title": "Test"}
#     service.get_by_id_course.return_value = {"id": uuid4(), "title": "Test"}
#     service.get_by_title.return_value = {"id": uuid4(), "title": "Test"}
#     service.get_all.return_value = []
#     service.get_by_user.return_value = []
#     service.update_course.return_value = {"id": uuid4(), "title": "Updated"}
#     service.soft_delete_course.return_value = True
#     service.hard_delete.return_value = True
#     return service


@pytest.fixture
def app(
    admin_user: FakeUser,
    mock_course_service: AsyncMock,
) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/courses")

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_course_service] = lambda: mock_course_service

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client
