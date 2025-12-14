from __future__ import annotations

import datetime as dt
import hashlib
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password, make_refresh_jwt, verify_password
from app.modules.auth.models import RefreshToken
from app.modules.roles.models import Role
from app.modules.users.models import User, UserProfile


@pytest.mark.auth
class TestRegister:
    async def test_register_success(
        self, client: AsyncClient, student_role: Role, db_session: AsyncSession
    ):
        payload = {
            "username": f"newuser_{uuid.uuid4().hex[:8]}",
            "password": "securepass123",
            "email": f"newuser_{uuid.uuid4().hex[:8]}@test.com",
            "first_name": "New",
            "last_name": "User",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["result"] is True
        assert "user_id" in data
        assert data["username"] == payload["username"]

        user = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.username == payload["username"])
        )
        assert user is not None
        assert user.email == payload["email"]
        assert verify_password(payload["password"], user.hashed_password)

        assert user.profile is not None
        assert user.profile.first_name == "New"
        assert user.profile.last_name == "User"
        assert user.profile.display_name == "New User"

    async def test_register_duplicate_username(
        self, client: AsyncClient, admin_user: User
    ):
        payload = {
            "username": admin_user.username,
            "password": "password123",
            "email": "different@test.com",
            "first_name": "Duplicate",
            "last_name": "User",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 409
        data = response.json()
        assert "username_taken" in data["detail"]

    async def test_register_missing_fields(self, client: AsyncClient):
        payload = {"username": "incomplete"}
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_password_too_short(self, client: AsyncClient):
        payload = {
            "username": "shortpass",
            "password": "short",
            "email": "short@test.com",
            "first_name": "Short",
            "last_name": "Pass",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_username_too_short(self, client: AsyncClient):
        payload = {
            "username": "ab",
            "password": "password123",
            "email": "short@test.com",
            "first_name": "Short",
            "last_name": "User",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        payload = {
            "username": "validuser",
            "password": "password123",
            "email": "not-an-email",
            "first_name": "Valid",
            "last_name": "User",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422

    async def test_register_without_middle_name(
        self, client: AsyncClient, student_role: Role, db_session: AsyncSession
    ):
        payload = {
            "username": f"nomiddle_{uuid.uuid4().hex[:8]}",
            "password": "password123",
            "email": f"nomiddle_{uuid.uuid4().hex[:8]}@test.com",
            "first_name": "No",
            "last_name": "Middle",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201

    async def test_register_with_middle_name(
        self, client: AsyncClient, student_role: Role, db_session: AsyncSession
    ):
        payload = {
            "username": f"withmiddle_{uuid.uuid4().hex[:8]}",
            "password": "password123",
            "email": f"withmiddle_{uuid.uuid4().hex[:8]}@test.com",
            "first_name": "With",
            "last_name": "Middle",
            "middle_name": "Name",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201

        user = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.username == payload["username"])
        )
        assert user.profile.middle_name == "Name"

    async def test_register_assigns_default_role(
        self, client: AsyncClient, student_role: Role, db_session: AsyncSession
    ):
        default_role = await db_session.scalar(
            select(Role).where(Role.slug == "student")
        )
        if not default_role:
            default_role = Role(slug="student", name="Student", is_system=True)
            db_session.add(default_role)
            await db_session.commit()

        payload = {
            "username": f"defaultrole_{uuid.uuid4().hex[:8]}",
            "password": "password123",
            "email": f"defaultrole_{uuid.uuid4().hex[:8]}@test.com",
            "first_name": "Default",
            "last_name": "Role",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201

        user = await db_session.scalar(
            select(User).where(User.username == payload["username"])
        )
        assert user.role.slug == "student"


@pytest.mark.auth
class TestLogin:
    async def test_login_success(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ):
        payload = {"username": admin_user.username, "password": "password123"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["message"] == "login_successful"

        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

        refresh_tokens = await db_session.scalars(
            select(RefreshToken).where(RefreshToken.user_id == admin_user.id)
        )
        assert len(list(refresh_tokens)) >= 1

    async def test_login_invalid_username(self, client: AsyncClient):
        payload = {"username": "nonexistent", "password": "password123"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert "invalid_credentials" in data["detail"]

    async def test_login_invalid_password(self, client: AsyncClient, admin_user: User):
        payload = {"username": admin_user.username, "password": "wrongpassword"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert "invalid_credentials" in data["detail"]

    async def test_login_inactive_user(
        self, client: AsyncClient, inactive_user: User
    ):
        payload = {"username": inactive_user.username, "password": "password123"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200

    async def test_login_updates_last_login(
        self, client: AsyncClient, student_user: User, db_session: AsyncSession
    ):
        before_login = student_user.last_login
        payload = {"username": student_user.username, "password": "password123"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200

        student_user = await db_session.merge(student_user)
        await db_session.refresh(student_user)
        assert student_user.last_login is not None
        if before_login:
            assert student_user.last_login > before_login

    async def test_login_missing_fields(self, client: AsyncClient):
        payload = {"username": "test"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 422

    async def test_login_creates_refresh_token_with_fingerprint(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ):
        payload = {"username": admin_user.username, "password": "password123"}
        headers = {"x-device-fingerprint": "test-fingerprint-123"}
        response = await client.post("/auth/login", json=payload, headers=headers)
        assert response.status_code == 200

        refresh_token = await db_session.scalar(
            select(RefreshToken)
            .where(RefreshToken.user_id == admin_user.id)
            .order_by(RefreshToken.created_at.desc())
        )
        assert refresh_token is not None
        assert refresh_token.fingerprint == "test-fingerprint-123"


@pytest.mark.auth
class TestRefresh:
    async def test_refresh_success(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ):
        refresh_id = uuid.uuid4()
        refresh_token = make_refresh_jwt(str(admin_user.id), str(refresh_id))

        refresh_entry = RefreshToken(
            id=refresh_id,
            user_id=admin_user.id,
            token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(days=30),
        )
        db_session.add(refresh_entry)
        await db_session.commit()

        payload = {"refresh_token": refresh_token}
        response = await client.post("/auth/refresh", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_missing_token(self, client: AsyncClient):
        response = await client.post("/auth/refresh", json={})
        assert response.status_code == 400
        data = response.json()
        assert "refresh_required" in data["detail"]

    async def test_refresh_invalid_token(self, client: AsyncClient):
        payload = {"refresh_token": "invalid.token.here"}
        response = await client.post("/auth/refresh", json=payload)
        assert response.status_code == 401

    async def test_refresh_revoked_token(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ):
        refresh_id = uuid.uuid4()
        refresh_token = make_refresh_jwt(str(admin_user.id), str(refresh_id))

        refresh_entry = RefreshToken(
            id=refresh_id,
            user_id=admin_user.id,
            token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(days=30),
            revoked_at=dt.datetime.now(dt.UTC),
        )
        db_session.add(refresh_entry)
        await db_session.commit()

        payload = {"refresh_token": refresh_token}
        response = await client.post("/auth/refresh", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert "refresh_invalid" in data["detail"]

    async def test_refresh_expired_token(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ):
        refresh_id = uuid.uuid4()
        refresh_token = make_refresh_jwt(str(admin_user.id), str(refresh_id))

        refresh_entry = RefreshToken(
            id=refresh_id,
            user_id=admin_user.id,
            token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            expires_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=1),
        )
        db_session.add(refresh_entry)
        await db_session.commit()

        payload = {"refresh_token": refresh_token}
        response = await client.post("/auth/refresh", json=payload)
        assert response.status_code == 401

    async def test_refresh_inactive_user(
        self, client: AsyncClient, inactive_user: User, db_session: AsyncSession
    ):
        refresh_id = uuid.uuid4()
        refresh_token = make_refresh_jwt(str(inactive_user.id), str(refresh_id))

        refresh_entry = RefreshToken(
            id=refresh_id,
            user_id=inactive_user.id,
            token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(days=30),
        )
        db_session.add(refresh_entry)
        await db_session.commit()

        payload = {"refresh_token": refresh_token}
        response = await client.post("/auth/refresh", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert "user_inactive" in data["detail"]

    async def test_refresh_from_cookie(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ):
        refresh_id = uuid.uuid4()
        refresh_token = make_refresh_jwt(str(admin_user.id), str(refresh_id))

        refresh_entry = RefreshToken(
            id=refresh_id,
            user_id=admin_user.id,
            token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(days=30),
        )
        db_session.add(refresh_entry)
        await db_session.commit()

        client.cookies.set("refresh_token", refresh_token)
        response = await client.post("/auth/refresh", json={})
        assert response.status_code == 200


@pytest.mark.auth
class TestGetCurrentUser:
    async def test_get_me_success(
        self, client: AsyncClient, auth_headers_admin: dict, admin_user: User
    ):
        response = await client.get("/auth/me", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "user" in data
        assert data["user"]["id"] == str(admin_user.id)
        assert data["user"]["email"] == admin_user.email

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_get_me_inactive_user(
        self, client: AsyncClient, inactive_user: User
    ):
        from app.core.security import make_access_jwt

        token = make_access_jwt(str(inactive_user.id), inactive_user.role.slug)
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        data = response.json()
        if "detail" in data:
            assert "user_inactive" in data["detail"]

    async def test_get_me_includes_profile(
        self, client: AsyncClient, auth_headers_admin: dict, admin_user: User
    ):
        response = await client.get("/auth/me", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert "display_name" in data["user"]
        assert data["user"]["display_name"] is not None

    async def test_get_me_includes_role(
        self, client: AsyncClient, auth_headers_admin: dict, admin_user: User
    ):
        response = await client.get("/auth/me", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert "role" in data["user"]
        assert data["user"]["role"] == admin_user.role.slug


@pytest.mark.auth
class TestChangePassword:
    async def test_change_password_success(
        self,
        client: AsyncClient,
        auth_headers_student: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        payload = {
            "current_password": "password123",
            "new_password": "newpassword123",
        }
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] is True
        assert "password_changed" in data["message"]

        student_user = await db_session.merge(student_user)
        await db_session.refresh(student_user)
        assert verify_password("newpassword123", student_user.hashed_password)

    async def test_change_password_wrong_current_password(
        self, client: AsyncClient, auth_headers_student: dict
    ):
        payload = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
        }
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 403
        data = response.json()
        assert "wrong_password" in data["detail"]

    async def test_change_password_same_as_current(
        self, client: AsyncClient, auth_headers_student: dict
    ):
        payload = {
            "current_password": "password123",
            "new_password": "password123",
        }
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 400
        data = response.json()
        assert "password_same" in data["detail"]

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        payload = {
            "current_password": "password123",
            "new_password": "newpassword123",
        }
        response = await client.post("/auth/change-password", json=payload)
        assert response.status_code == 401

    async def test_change_password_revokes_refresh_tokens(
        self,
        client: AsyncClient,
        auth_headers_student: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        refresh_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=student_user.id,
            token_hash="somehash123",
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(days=30),
        )
        db_session.add(refresh_token)
        await db_session.flush()

        payload = {
            "current_password": "password123",
            "new_password": "newpassword123",
        }
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 200

        await db_session.refresh(refresh_token)
        assert refresh_token.revoked_at is not None

    async def test_change_password_sets_must_change_password_false(
        self,
        client: AsyncClient,
        auth_headers_student: dict,
        student_user: User,
        db_session: AsyncSession,
    ):
        student_user.must_change_password = True
        await db_session.flush()

        payload = {
            "current_password": "password123",
            "new_password": "newpassword123",
        }
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 200

        student_user = await db_session.merge(student_user)
        await db_session.refresh(student_user)
        assert student_user.must_change_password is False

    async def test_change_password_validation_too_short(
        self, client: AsyncClient, auth_headers_student: dict
    ):
        payload = {"current_password": "password123", "new_password": "short"}
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 422

    async def test_change_password_missing_fields(
        self, client: AsyncClient, auth_headers_student: dict
    ):
        payload = {"current_password": "password123"}
        response = await client.post(
            "/auth/change-password", json=payload, headers=auth_headers_student
        )
        assert response.status_code == 422


@pytest.mark.auth
class TestJWKS:
    async def test_jwks_endpoint_rs256(self, client: AsyncClient):
        from app.core.config import settings

        if settings.jwt_alg != "RS256":
            pytest.skip("JWKS only available for RS256")

        response = await client.get("/auth/.well-known/jwks.json")
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert len(data["keys"]) > 0

        key = data["keys"][0]
        assert key["kty"] == "RSA"
        assert key["use"] == "sig"
        assert key["alg"] == "RS256"
        assert "n" in key
        assert "e" in key

    async def test_jwks_not_available_for_symmetric(self, client: AsyncClient):
        from app.core.config import settings

        if settings.jwt_alg == "RS256":
            pytest.skip("Test only for symmetric algorithms")

        response = await client.get("/auth/.well-known/jwks.json")
        assert response.status_code == 404


@pytest.mark.auth
class TestAuthEdgeCases:
    async def test_login_sets_cookies_with_proper_attributes(
        self, client: AsyncClient, admin_user: User
    ):
        payload = {"username": admin_user.username, "password": "password123"}
        response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200

        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    async def test_register_trims_and_formats_display_name(
        self, client: AsyncClient, student_role: Role, db_session: AsyncSession
    ):
        payload = {
            "username": f"spacing_{uuid.uuid4().hex[:8]}",
            "password": "password123",
            "email": f"spacing_{uuid.uuid4().hex[:8]}@test.com",
            "first_name": "  First  ",
            "last_name": "  Last  ",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 201

        user = await db_session.scalar(
            select(User).options(selectinload(User.profile)).where(User.username == payload["username"])
        )
        assert user.profile.display_name.strip() == "First     Last"
