from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.app import create_app
from app.common.db.session import SessionLocal, get_db
from app.core.security import hash_password, make_access_jwt
from app.modules.roles.models import Role
from app.modules.users.models import User, UserProfile


@pytest.fixture(scope="function")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def app():
    return create_app()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session
        break


@pytest_asyncio.fixture(scope="function")
async def client(app, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_role() -> Role:
    async with SessionLocal() as session:
        # Check if admin role already exists
        existing = await session.scalar(select(Role).where(Role.slug == "admin"))
        if existing:
            return existing
        role = Role(slug="admin", name="Administrator", is_system=True)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role


@pytest_asyncio.fixture
async def student_role() -> Role:
    async with SessionLocal() as session:
        # Check if student role already exists
        existing = await session.scalar(select(Role).where(Role.slug == "student"))
        if existing:
            return existing
        role = Role(slug="student", name="Student", is_system=False)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role


@pytest_asyncio.fixture
async def teacher_role() -> Role:
    async with SessionLocal() as session:
        # Check if teacher role already exists
        existing = await session.scalar(select(Role).where(Role.slug == "teacher"))
        if existing:
            return existing
        role = Role(slug="teacher", name="Teacher", is_system=False)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role


@pytest_asyncio.fixture
async def admin_user(admin_role: Role) -> User:
    async with SessionLocal() as session:
        # Merge the role into this session
        admin_role = await session.merge(admin_role)
        user = User(
            username=f"admin_user_{uuid.uuid4().hex[:8]}",
            email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=hash_password("password123"),
            role=admin_role,
            is_verified=True,
            is_active=True,
        )
        profile = UserProfile(
            user=user, first_name="Admin", last_name="User", display_name="Admin User"
        )
        session.add(user)
        session.add(profile)
        await session.commit()
        await session.refresh(user)
        # Access role to load it before session closes
        _ = user.role.slug
        return user


@pytest_asyncio.fixture
async def student_user(student_role: Role) -> User:
    async with SessionLocal() as session:
        # Merge the role into this session
        student_role = await session.merge(student_role)
        user = User(
            username=f"student_user_{uuid.uuid4().hex[:8]}",
            email=f"student_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=hash_password("password123"),
            role=student_role,
            is_verified=True,
            is_active=True,
        )
        profile = UserProfile(
            user=user,
            first_name="Student",
            last_name="User",
            display_name="Student User",
        )
        session.add(user)
        session.add(profile)
        await session.commit()
        await session.refresh(user)
        # Access role to load it before session closes
        _ = user.role.slug
        return user


@pytest_asyncio.fixture
async def unverified_user(student_role: Role) -> User:
    async with SessionLocal() as session:
        # Merge the role into this session
        student_role = await session.merge(student_role)
        user = User(
            username=f"unverified_user_{uuid.uuid4().hex[:8]}",
            email=f"unverified_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=hash_password("password123"),
            role=student_role,
            is_verified=False,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # Access role to load it before session closes
        _ = user.role.slug
        return user


@pytest_asyncio.fixture
async def inactive_user(student_role: Role) -> User:
    async with SessionLocal() as session:
        # Merge the role into this session
        student_role = await session.merge(student_role)
        user = User(
            username=f"inactive_user_{uuid.uuid4().hex[:8]}",
            email=f"inactive_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=hash_password("password123"),
            role=student_role,
            is_verified=True,
            is_active=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # Access role to load it before session closes
        _ = user.role.slug
        return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return make_access_jwt(str(admin_user.id), admin_user.role.slug)


@pytest.fixture
def student_token(student_user: User) -> str:
    return make_access_jwt(str(student_user.id), student_user.role.slug)


@pytest.fixture
def auth_headers_admin(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_student(student_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {student_token}"}
