import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from uuid import UUID, uuid4
from typing import AsyncGenerator
from unittest.mock import AsyncMock

from app.modules.courses.router import router
from app.common.deps.auth import get_current_user
from app.modules.courses.services_import import get_course_service


class FakeUser:
    """Фейковый пользователь для тестов"""

    def __init__(self, roles: list[str]):
        self.id: UUID = uuid4()
        self.roles: list[str] = roles


@pytest.fixture
def admin_user() -> FakeUser:
    return FakeUser(["admin"])


@pytest.fixture
def teacher_user() -> FakeUser:
    return FakeUser(["teacher"])


@pytest.fixture
def student_user() -> FakeUser:
    return FakeUser(["student"])


@pytest.fixture
def mock_course_service() -> AsyncMock:
    service: AsyncMock = AsyncMock()

    service.create_course.return_value = {"id": uuid4(), "title": "Test"}
    service.get_by_id_course.return_value = {"id": uuid4(), "title": "Test"}
    service.get_by_title.return_value = {"id": uuid4(), "title": "Test"}
    service.get_all.return_value = []
    service.get_by_user.return_value = []
    service.update_course.return_value = {"id": uuid4(), "title": "Updated"}
    service.soft_delete_course.return_value = True
    service.hard_delete.return_value = True

    return service


@pytest.fixture
def app(
    admin_user: FakeUser,
    mock_course_service: AsyncMock,
) -> FastAPI:
    app: FastAPI = FastAPI()
    app.include_router(router, prefix="/courses")

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_course_service] = lambda: mock_course_service

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
