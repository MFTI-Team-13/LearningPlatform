from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.roles.models import Role
from app.modules.users.models import User


@pytest.mark.roles
class TestRolesList:
    async def test_list_roles_success_no_auth(
        self, client: AsyncClient, admin_role: Role
    ):
        response = await client.get("/roles/")
        assert response.status_code == 200
        data = response.json()
        print(f"Response: {data}")  # Debug
        assert data["result"] is True
        assert "roles" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_roles_content(
        self,
        client: AsyncClient,
        admin_role: Role,
        student_role: Role,
    ):
        response = await client.get("/roles/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["roles"]) >= 2

        role_slugs = [r["slug"] for r in data["roles"]]
        assert admin_role.slug in role_slugs
        assert student_role.slug in role_slugs

    async def test_list_roles_returns_all_fields(
        self, client: AsyncClient, admin_role: Role
    ):
        response = await client.get("/roles/")
        assert response.status_code == 200
        data = response.json()

        roles = data["roles"]
        assert len(roles) > 0

        first_role = roles[0]
        assert "id" in first_role
        assert "slug" in first_role
        assert "name" in first_role
        assert "description" in first_role
        assert "is_system" in first_role
        assert "created_at" in first_role
        assert "updated_at" in first_role


@pytest.mark.roles
class TestRoleCreate:
    async def test_create_role_success(
        self, client: AsyncClient, auth_headers_admin: dict, db_session: AsyncSession
    ):
        slug = f"moderator_{uuid.uuid4().hex[:6]}"
        payload = {
            "slug": slug,
            "name": "Moderator",
            "description": "Forum moderator role",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["result"] is True
        assert "role" in data
        assert data["role"]["slug"] == slug
        assert data["role"]["name"] == "Moderator"
        assert data["role"]["is_system"] is False

        role = await db_session.scalar(
            select(Role).where(Role.slug == slug)
        )
        assert role is not None
        assert role.name == "Moderator"

    async def test_create_role_duplicate_slug(
        self, client: AsyncClient, auth_headers_admin: dict, admin_role: Role
    ):
        payload = {
            "slug": admin_role.slug,
            "name": "Duplicate Admin",
            "description": "This should fail",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "role_exists" in str(data["detail"])

    async def test_create_role_missing_fields(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        payload = {"slug": "incomplete"}
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_create_role_invalid_slug_too_short(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        payload = {
            "slug": "x",
            "name": "Invalid Role",
            "description": "Slug too short",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_create_role_invalid_slug_too_long(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        payload = {
            "slug": "x" * 51,
            "name": "Invalid Role",
            "description": "Slug too long",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_create_role_unauthorized_student(
        self, client: AsyncClient, auth_headers_student: dict
    ):
        payload = {
            "slug": "unauthorized",
            "name": "Unauthorized",
            "description": "Should not be created",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 403

    async def test_create_role_unauthenticated(self, client: AsyncClient):
        payload = {
            "slug": "unauthenticated",
            "name": "Unauthenticated",
            "description": "Should fail",
            "is_system": False,
        }
        response = await client.post("/roles/", json=payload)
        assert response.status_code == 401

    async def test_create_role_slug_case_normalization(
        self, client: AsyncClient, auth_headers_admin: dict, db_session: AsyncSession
    ):
        slug = f"MyRole_{uuid.uuid4().hex[:6]}"
        payload = {
            "slug": slug,
            "name": "My Role",
            "description": "Case test",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"]["slug"] == slug.lower()

    async def test_create_role_boundary_name_length(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        slug = f"long_name_{uuid.uuid4().hex[:6]}"
        payload = {
            "slug": slug,
            "name": "x" * 100,
            "description": "Testing max name length",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 201

    async def test_create_role_name_too_long(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        payload = {
            "slug": "toolong",
            "name": "x" * 101,
            "description": "Name exceeds limit",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422


@pytest.mark.roles
class TestRoleGet:
    async def test_get_role_success(
        self, client: AsyncClient, admin_role: Role
    ):
        response = await client.get(f"/roles/{admin_role.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "role" in data
        assert data["role"]["id"] == str(admin_role.id)
        assert data["role"]["slug"] == admin_role.slug

    async def test_get_role_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/roles/{fake_id}")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "role_not_found" in data["detail"]

    async def test_get_role_invalid_id(self, client: AsyncClient):
        response = await client.get("/roles/invalid-uuid")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid_role_id" in data["detail"]

    async def test_get_role_no_auth_required(
        self, client: AsyncClient, admin_role: Role
    ):
        response = await client.get(f"/roles/{admin_role.id}")
        assert response.status_code == 200


@pytest.mark.roles
class TestRoleUpdate:
    async def test_update_role_success(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        payload = {
            "name": "Updated Teacher",
            "description": "Updated description",
        }
        response = await client.patch(
            f"/roles/{teacher_role.id}",
            json=payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert data["role"]["name"] == "Updated Teacher"
        assert data["role"]["description"] == "Updated description"

        # Re-fetch the role from the database to verify
        teacher_role = await db_session.merge(teacher_role)
        await db_session.refresh(teacher_role)
        assert teacher_role.name == "Updated Teacher"

    async def test_update_role_partial(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        original_name = teacher_role.name
        payload = {"description": "Only description updated"}
        response = await client.patch(
            f"/roles/{teacher_role.id}",
            json=payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"]["name"] == original_name
        assert data["role"]["description"] == "Only description updated"

    async def test_update_role_not_found(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        fake_id = str(uuid.uuid4())
        payload = {"name": "Does not exist"}
        response = await client.patch(
            f"/roles/{fake_id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 404

    async def test_update_role_duplicate_slug(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_role: Role,
        teacher_role: Role,
    ):
        payload = {"slug": admin_role.slug}
        response = await client.patch(
            f"/roles/{teacher_role.id}",
            json=payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == 409
        data = response.json()
        assert "role_exists" in data["detail"]

    async def test_update_role_unauthorized_student(
        self, client: AsyncClient, auth_headers_student: dict, teacher_role: Role
    ):
        payload = {"name": "Unauthorized update"}
        response = await client.patch(
            f"/roles/{teacher_role.id}",
            json=payload,
            headers=auth_headers_student,
        )
        assert response.status_code == 403

    async def test_update_role_unauthenticated(
        self, client: AsyncClient, teacher_role: Role
    ):
        payload = {"name": "No auth"}
        response = await client.patch(
            f"/roles/{teacher_role.id}", json=payload
        )
        assert response.status_code == 401

    async def test_update_role_validation_invalid_name(
        self, client: AsyncClient, auth_headers_admin: dict, teacher_role: Role
    ):
        payload = {"name": ""}
        response = await client.patch(
            f"/roles/{teacher_role.id}",
            json=payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == 422

    async def test_update_role_all_fields(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        slug = f"updated_slug_{uuid.uuid4().hex[:6]}"
        payload = {
            "slug": slug,
            "name": "Updated Name",
            "description": "Updated Description",
            "is_system": True,
        }
        response = await client.patch(
            f"/roles/{teacher_role.id}",
            json=payload,
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"]["slug"] == slug
        assert data["role"]["name"] == "Updated Name"
        assert data["role"]["is_system"] is True


@pytest.mark.roles
class TestRoleDelete:
    async def test_delete_role_success(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        role_id = teacher_role.id
        response = await client.delete(
            f"/roles/{role_id}", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "role_deleted" in data["message"]

        deleted_role = await db_session.get(Role, role_id)
        assert deleted_role is None

    async def test_delete_role_not_found(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        fake_id = str(uuid.uuid4())
        response = await client.delete(
            f"/roles/{fake_id}", headers=auth_headers_admin
        )
        assert response.status_code == 404

    async def test_delete_role_with_users_assigned(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        # Create a user with the teacher role
        teacher_role = await db_session.merge(teacher_role)
        username = f"test_teacher_{uuid.uuid4().hex[:6]}"
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password="hashed",
            role=teacher_role,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.delete(
            f"/roles/{teacher_role.id}", headers=auth_headers_admin
        )
        assert response.status_code == 400
        data = response.json()
        assert "role_in_use" in data["detail"]

    async def test_delete_system_role(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        db_session: AsyncSession,
    ):
        system_role = Role(slug=f"system_{uuid.uuid4().hex[:6]}", name="System Role", is_system=True)
        db_session.add(system_role)
        await db_session.commit()
        await db_session.refresh(system_role)

        response = await client.delete(
            f"/roles/{system_role.id}", headers=auth_headers_admin
        )
        assert response.status_code == 400
        data = response.json()
        assert "role_protected" in data["detail"]

    async def test_delete_role_unauthorized_student(
        self, client: AsyncClient, auth_headers_student: dict, teacher_role: Role
    ):
        response = await client.delete(
            f"/roles/{teacher_role.id}", headers=auth_headers_student
        )
        assert response.status_code == 403

    async def test_delete_role_unauthenticated(
        self, client: AsyncClient, teacher_role: Role
    ):
        response = await client.delete(f"/roles/{teacher_role.id}")
        assert response.status_code == 401


@pytest.mark.roles
class TestRoleEdgeCases:
    async def test_role_with_null_description(
        self, client: AsyncClient, auth_headers_admin: dict, db_session: AsyncSession
    ):
        slug = f"no_desc_{uuid.uuid4().hex[:6]}"
        payload = {
            "slug": slug,
            "name": "No Description Role",
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"]["description"] is None

    async def test_role_update_empty_payload(
        self, client: AsyncClient, auth_headers_admin: dict, teacher_role: Role
    ):
        original_name = teacher_role.name
        response = await client.patch(
            f"/roles/{teacher_role.id}", json={}, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"]["name"] == original_name

    async def test_role_description_max_length(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        slug = f"long_desc_{uuid.uuid4().hex[:6]}"
        payload = {
            "slug": slug,
            "name": "Long Description",
            "description": "x" * 255,
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 201

    async def test_role_description_too_long(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        payload = {
            "slug": "toolong_desc",
            "name": "Too Long Description",
            "description": "x" * 256,
            "is_system": False,
        }
        response = await client.post(
            "/roles/", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422
