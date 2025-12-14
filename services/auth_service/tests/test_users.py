from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.roles.models import Role
from app.modules.users.models import User, UserProfile


@pytest.mark.users
class TestUsersList:
    async def test_list_users_success_admin(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
        student_user: User,
    ):
        response = await client.get("/users/", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    async def test_list_users_unauthorized_student(
        self, client: AsyncClient, auth_headers_student: dict
    ):
        response = await client.get("/users/", headers=auth_headers_student)
        assert response.status_code == 403

    async def test_list_users_unauthenticated(self, client: AsyncClient):
        response = await client.get("/users/")
        assert response.status_code == 401

    async def test_list_users_pagination_default(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
        student_user: User,
    ):
        response = await client.get("/users/", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 20
        assert data["offset"] == 0

    async def test_list_users_pagination_custom(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get(
            "/users/?limit=5&offset=1", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 1

    async def test_list_users_pagination_limit_validation(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get("/users/?limit=101", headers=auth_headers_admin)
        assert response.status_code == 422

        response = await client.get("/users/?limit=0", headers=auth_headers_admin)
        assert response.status_code == 422

    async def test_list_users_search_by_username(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
        student_user: User,
    ):
        response = await client.get(
            f"/users/?q={admin_user.username[:5]}", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        usernames = [u["login"] for u in data["items"]]
        assert admin_user.username in usernames

    async def test_list_users_search_by_email(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
    ):
        response = await client.get(
            f"/users/?q={admin_user.email[:5]}", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        emails = [u["email"] for u in data["items"]]
        assert admin_user.email in emails

    async def test_list_users_filter_by_role(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
        admin_role: Role,
    ):
        response = await client.get(
            f"/users/?role_ids[]={admin_role.id}", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert data["total"] >= 1

        for user in data["items"]:
            assert user["role"] == admin_role.slug

    async def test_list_users_order_by_email(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
        student_user: User,
    ):
        response = await client.get(
            "/users/?order_by=email&order=asc", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert len(data["items"]) >= 2

        emails = [u["email"] for u in data["items"]]
        assert emails == sorted(emails)

    async def test_list_users_order_by_created_at(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get(
            "/users/?order_by=created_at&order=desc", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True

    async def test_list_users_order_by_verified(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get(
            "/users/?order_by=verified&order=desc", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True

    async def test_list_users_invalid_order_by(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get(
            "/users/?order_by=invalid", headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_list_users_invalid_order(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get(
            "/users/?order=invalid", headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_list_users_includes_profile_data(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        admin_user: User,
    ):
        response = await client.get("/users/", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()

        users = data["items"]
        assert len(users) > 0

        admin_user_data = next(
            (u for u in users if u["id"] == str(admin_user.id)), None
        )
        assert admin_user_data is not None
        assert "display_name" in admin_user_data
        assert admin_user_data["display_name"] is not None


@pytest.mark.users
class TestUserGetById:
    async def test_get_user_success(
        self, client: AsyncClient, auth_headers_admin: dict, admin_user: User
    ):
        response = await client.get(
            f"/users/{admin_user.id}", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "user" in data
        assert data["user"]["id"] == str(admin_user.id)
        assert data["user"]["email"] == admin_user.email

    async def test_get_user_not_found(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        fake_id = uuid.uuid4()
        response = await client.get(f"/users/{fake_id}", headers=auth_headers_admin)
        assert response.status_code == 404
        data = response.json()
        assert "user_not_found" in data["detail"]

    async def test_get_user_invalid_uuid(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get("/users/invalid-uuid", headers=auth_headers_admin)
        assert response.status_code == 422

    async def test_get_user_unauthorized_student(
        self, client: AsyncClient, auth_headers_student: dict, admin_user: User
    ):
        response = await client.get(
            f"/users/{admin_user.id}", headers=auth_headers_student
        )
        assert response.status_code == 403

    async def test_get_user_unauthenticated(self, client: AsyncClient, admin_user: User):
        response = await client.get(f"/users/{admin_user.id}")
        assert response.status_code == 401

    async def test_get_user_includes_all_fields(
        self, client: AsyncClient, auth_headers_admin: dict, admin_user: User
    ):
        response = await client.get(
            f"/users/{admin_user.id}", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "is_active" in user
        assert "is_verified" in user
        assert "must_change_password" in user
        assert "role" in user
        assert "created_at" in user
        assert "updated_at" in user
        assert "last_login" in user
        assert "display_name" in user
        assert "login" in user


@pytest.mark.users
class TestUserUpdate:
    async def test_update_user_email(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        new_email = "newemail@test.com"
        payload = {"email": new_email}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert data["user"]["email"] == new_email

        updated_user = await db_session.scalar(
            select(User).execution_options(populate_existing=True).where(User.id == student_user.id)
        )
        assert updated_user is not None
        assert updated_user.email == new_email

    async def test_update_user_role(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        payload = {"role_id": str(teacher_role.id)}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert data["user"]["role"] == teacher_role.slug

        updated_user = await db_session.scalar(
            select(User).execution_options(populate_existing=True).where(User.id == student_user.id)
        )
        assert updated_user is not None
        assert updated_user.role_id == teacher_role.id

    async def test_update_user_is_active(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        payload = {"is_active": False}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_active"] is False

        updated_user = await db_session.scalar(
            select(User).execution_options(populate_existing=True).where(User.id == student_user.id)
        )
        assert updated_user is not None
        assert updated_user.is_active is False

    async def test_update_user_is_verified(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        unverified_user: User,
        db_session: AsyncSession,
    ):
        payload = {"is_verified": True, "first_name": "Verified", "last_name": "User"}
        response = await client.patch(
            f"/users/{unverified_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_verified"] is True

        updated_user = await db_session.scalar(
            select(User).execution_options(populate_existing=True).where(User.id == unverified_user.id)
        )
        assert updated_user is not None
        assert updated_user.is_verified is True

    async def test_update_user_must_change_password(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        payload = {"must_change_password": True}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["must_change_password"] is True

        updated_user = await db_session.scalar(
            select(User).execution_options(populate_existing=True).where(User.id == student_user.id)
        )
        assert updated_user is not None
        assert updated_user.must_change_password is True

    async def test_update_user_profile_fields(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        payload = {
            "first_name": "NewFirst",
            "last_name": "NewLast",
            "middle_name": "NewMiddle",
            "display_name": "New Display",
        }
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert data["user"]["display_name"] == "New Display"

        updated_user = await db_session.scalar(
            select(User)
            .options(selectinload(User.profile))
            .execution_options(populate_existing=True)
            .where(User.id == student_user.id)
        )
        assert updated_user is not None
        profile = updated_user.profile
        assert profile is not None
        assert profile.first_name == "NewFirst"
        assert profile.last_name == "NewLast"
        assert profile.middle_name == "NewMiddle"
        assert profile.display_name == "New Display"

    async def test_update_user_creates_profile_if_missing(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        unverified_user: User,
        db_session: AsyncSession,
    ):
        user_row = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.id == unverified_user.id)
        )
        assert user_row is not None
        if user_row.profile:
            await db_session.delete(user_row.profile)
            await db_session.commit()

        payload = {"first_name": "Created", "last_name": "Profile"}
        response = await client.patch(
            f"/users/{unverified_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200

        updated_user = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.id == unverified_user.id)
        )
        assert updated_user is not None
        assert updated_user.profile is not None
        assert updated_user.profile.first_name == "Created"

    async def test_update_user_not_found(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        fake_id = uuid.uuid4()
        payload = {"email": "notfound@test.com"}
        response = await client.patch(
            f"/users/{fake_id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 404

    async def test_update_user_invalid_role_id_format(
        self, client: AsyncClient, auth_headers_admin: dict, student_user: User
    ):
        payload = {"role_id": "not-a-uuid"}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 400
        data = response.json()
        assert "invalid_role_id_format" in data["detail"]

    async def test_update_user_role_not_found(
        self, client: AsyncClient, auth_headers_admin: dict, student_user: User
    ):
        fake_role_id = str(uuid.uuid4())
        payload = {"role_id": fake_role_id}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 400
        data = response.json()
        assert "role_not_found" in data["detail"]

    async def test_update_user_unauthorized_student(
        self, client: AsyncClient, auth_headers_student: dict, admin_user: User
    ):
        payload = {"email": "hacker@test.com"}
        response = await client.patch(
            f"/users/{admin_user.id}", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 403

    async def test_update_user_unauthenticated(
        self, client: AsyncClient, student_user: User
    ):
        payload = {"email": "noauth@test.com"}
        response = await client.patch(f"/users/{student_user.id}", json=payload)
        assert response.status_code == 401

    async def test_update_user_partial_profile(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        user_before = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.id == student_user.id)
        )
        assert user_before is not None
        assert user_before.profile is not None
        original_first_name = user_before.profile.first_name
        payload = {"last_name": "OnlyLastName"}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200

        user_after = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.id == student_user.id)
        )
        assert user_after is not None
        assert user_after.profile is not None
        assert user_after.profile.first_name == original_first_name
        assert user_after.profile.last_name == "OnlyLastName"

    async def test_update_user_invalid_email_format(
        self, client: AsyncClient, auth_headers_admin: dict, student_user: User
    ):
        payload = {"email": "not-an-email"}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_update_user_empty_first_name(
        self, client: AsyncClient, auth_headers_admin: dict, student_user: User
    ):
        payload = {"first_name": ""}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422

    async def test_update_user_empty_last_name(
        self, client: AsyncClient, auth_headers_admin: dict, student_user: User
    ):
        payload = {"last_name": ""}
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 422


@pytest.mark.users
class TestUserEdgeCases:
    async def test_list_users_no_results_with_filter(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        response = await client.get(
            "/users/?q=nonexistentuser12345", headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_list_users_offset_beyond_total(
        self, client: AsyncClient, auth_headers_admin: dict
    ):
        base_response = await client.get("/users/?limit=1", headers=auth_headers_admin)
        assert base_response.status_code == 200
        base_data = base_response.json()
        total = int(base_data["total"])

        response = await client.get(f"/users/?offset={total + 1}", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == total
        assert len(data["items"]) == 0

    async def test_update_user_multiple_fields_at_once(
        self,
        client: AsyncClient,
        auth_headers_admin: dict,
        student_user: User,
        teacher_role: Role,
        db_session: AsyncSession,
    ):
        payload = {
            "email": "multifiel@test.com",
            "role_id": str(teacher_role.id),
            "is_active": False,
            "is_verified": False,
            "must_change_password": True,
            "first_name": "Multi",
            "last_name": "Field",
            "display_name": "Multi Field User",
        }
        response = await client.patch(
            f"/users/{student_user.id}", json=payload, headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "multifiel@test.com"
        assert data["user"]["role"] == teacher_role.slug
        assert data["user"]["is_active"] is False
        assert data["user"]["is_verified"] is False
        assert data["user"]["must_change_password"] is True
        assert data["user"]["display_name"] == "Multi Field User"
