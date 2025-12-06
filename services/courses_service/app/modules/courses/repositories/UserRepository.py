from typing import Optional, List
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from enums.course_enums import UserRole
from database import get_session


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID, include_deleted: bool = True) -> Optional[User]:
        query = select(User).where(User.id == user_id)

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str, include_deleted: bool = True) -> Optional[User]:
        query = select(User).where(User.login == login)

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_display_name(self, display_name: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(User.display_name == display_name)

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_login(self, login: str) -> bool:
        user = await self.get_by_login(login)
        return user is not None

    async def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[User]:
        query = select(User).order_by(User.created_at.desc())

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 100,
                                                include_deleted: bool = False) -> List[User]:
        query = select(User).where(User.role == role)

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(
            query.order_by(User.created_at.desc())
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, user_data: dict) -> Optional[User]:
        user = await self.get_by_id(user_id)

        if not user:
            return None

        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def soft_delete(self, user_id: UUID) -> bool:
        user = await self.get_by_id(user_id)

        if not user:
            return False

        user.delete_flg = True
        await self.db.commit()
        return True

    async def hard_delete(self, user_id: UUID) -> bool:
        user = await self.get_by_id(user_id, include_deleted=True)

        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def restore(self, user_id: UUID) -> bool:
        user = await self.get_by_id(user_id, include_deleted=True)

        if not user:
            return False

        user.delete_flg = False
        await self.db.commit()
        return True

    async def search_users(self, search_term: str, skip: int = 0, limit: int = 100,
                                                 include_deleted: bool = False) -> List[User]:
        query = select(User).where(
            or_(
                User.display_name.ilike(f"%{search_term}%"),
                User.login.ilike(f"%{search_term}%")
            )
        )

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(
            query.order_by(User.created_at.desc())
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def change_role(self, user_id: UUID, new_role: UserRole) -> bool:
        user = await self.get_by_id(user_id)

        if not user:
            return False

        user.role = new_role
        await self.db.commit()
        return True

    async def count_users(self, role: Optional[UserRole] = None, include_deleted: bool = False) -> int:
        query = select(User)

        if role:
            query = query.where(User.role == role)

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(query)
        users = result.scalars().all()
        return len(users)

    async def get_users_created_in_period(self, start_date, end_date, include_deleted: bool = False) -> List[User]:
        query = select(User).where(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        )

        if not include_deleted:
            query = query.where(User.delete_flg == False)

        result = await self.db.execute(
            query.order_by(User.created_at.desc())
        )
        return result.scalars().all()


async def get_user_repository(
    db: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(db)
