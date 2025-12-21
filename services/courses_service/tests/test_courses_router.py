import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_course(client: AsyncClient) -> None:
    response = await client.post(
        "/courses/create",
        json={"title": "New course", "level": "beginner"},
    )

    assert response.status_code == 200
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_course_by_id(client: AsyncClient) -> None:
    course_id = str(uuid4())

    response = await client.post(
        "/courses/getById",
        params={"course_id": course_id},
    )

    assert response.status_code == 200
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_course_by_title(client: AsyncClient) -> None:
    response = await client.get(
        "/courses/getByTitle",
        params={"title": "Python"},
    )

    assert response.status_code == 200
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_list_courses_admin_only(client: AsyncClient) -> None:
    response = await client.get("/courses/list")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_by_user(client: AsyncClient) -> None:
    response = await client.post(
        "/courses/getByUser",
        params={"author_id": str(uuid4())},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_course(client: AsyncClient) -> None:
    response = await client.put(
        "/courses/update",
        params={"course_id": str(uuid4())},
        json={"title": "Updated"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_soft_delete_course(client: AsyncClient) -> None:
    response = await client.delete(
        "/courses/softDelete",
        params={"course_id": str(uuid4())},
    )

    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.asyncio
async def test_hard_delete_course(client: AsyncClient) -> None:
    response = await client.delete(
        "/courses/hardDelete",
        params={"course_id": str(uuid4())},
    )

    assert response.status_code == 200
    assert response.json() is True
