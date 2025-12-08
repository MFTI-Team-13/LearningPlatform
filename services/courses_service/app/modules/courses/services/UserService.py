from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError

from repositories.user_repository import UserRepository, get_user_repository
from schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserRoleUpdate
from enums.course_enums import UserRole


class UserService:
  def __init__(self, user_repo: UserRepository):
    self.user_repo = user_repo

  async def create_user(self, user_data: UserCreate) -> UserResponse:
    try:
      if await self.user_repo.exists_by_login(user_data.login):
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Пользователь с таким логином уже существует"
        )

      user_dict = user_data.model_dump()
      user = await self.user_repo.create(user_dict)

      return UserResponse(
        id=user.id,
        display_name=user.display_name,
        login=user.login,
        role=user.role,
        is_deleted=user.delete_flg,
        created_at=user.created_at,
        updated_at=user.updated_at
      )
    except IntegrityError:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Ошибка при создании пользователя"
      )

  async def get_user(self, user_id: UUID) -> UserResponse:
    user = await self.user_repo.get_by_id(user_id)

    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    return UserResponse(
      id=user.id,
      display_name=user.display_name,
      login=user.login,
      role=user.role,
      is_deleted=user.delete_flg,
      created_at=user.created_at,
      updated_at=user.updated_at
    )

  async def get_user_by_login(self, login: str) -> Optional[UserResponse]:
    user = await self.user_repo.get_by_login(login)

    if not user:
      return None

    return UserResponse(
      id=user.id,
      display_name=user.display_name,
      login=user.login,
      role=user.role,
      is_deleted=user.delete_flg,
      created_at=user.created_at,
      updated_at=user.updated_at
    )

  async def update_user(self, user_id: UUID, update_data: UserUpdate) -> UserResponse:
    user = await self.user_repo.get_by_id(user_id)

    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    if update_data.login and update_data.login != user.login:
      existing_user = await self.user_repo.get_by_login(update_data.login)
      if existing_user and existing_user.id != user_id:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Пользователь с таким логином уже существует"
        )

    updated_user = await self.user_repo.update(
      user_id,
      update_data.model_dump(exclude_unset=True)
    )

    if not updated_user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    return UserResponse(
      id=updated_user.id,
      display_name=updated_user.display_name,
      login=updated_user.login,
      role=updated_user.role,
      is_deleted=updated_user.delete_flg,
      created_at=updated_user.created_at,
      updated_at=updated_user.updated_at
    )

  async def delete_user(self, user_id: UUID, current_user_id: UUID) -> Dict[str, Any]:
    if user_id == current_user_id:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Нельзя удалить самого себя"
      )

    user = await self.user_repo.get_by_id(user_id)

    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    success = await self.user_repo.soft_delete(user_id)

    if not success:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Ошибка при удалении пользователя"
      )

    return {
      "success": True,
      "message": "Пользователь успешно удален",
      "user_id": user_id
    }

  async def restore_user(self, user_id: UUID) -> Dict[str, Any]:
    success = await self.user_repo.restore(user_id)

    if not success:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    return {
      "success": True,
      "message": "Пользователь успешно восстановлен",
      "user_id": user_id
    }

  async def change_user_role(self, user_id: UUID, role_data: UserRoleUpdate,
                             current_user_id: UUID) -> Dict[str, Any]:
    if user_id == current_user_id:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Нельзя изменить роль самому себе"
      )

    user = await self.user_repo.get_by_id(user_id)

    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    if user.role == role_data.role:
      return {
        "success": True,
        "message": "Роль уже установлена",
        "user_id": user_id,
        "role": user.role.value
      }

    success = await self.user_repo.change_role(user_id, role_data.role)

    if not success:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Ошибка при изменении роли"
      )

    return {
      "success": True,
      "message": "Роль успешно изменена",
      "user_id": user_id,
      "old_role": user.role.value,
      "new_role": role_data.role.value
    }

  async def get_users(
    self,
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    include_deleted: bool = False,
    current_user_role: UserRole = UserRole.STUDENT
  ) -> List[UserResponse]:
    if current_user_role not in [UserRole.ADMIN, UserRole.TEACHER]:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Недостаточно прав для просмотра пользователей"
      )

    users = await self.user_repo.get_all(skip, limit, include_deleted)

    if role:
      users = await self.user_repo.get_by_role(role, skip, limit, include_deleted)

    return [
      UserResponse(
        id=user.id,
        display_name=user.display_name,
        login=user.login,
        role=user.role,
        is_deleted=user.delete_flg,
        created_at=user.created_at,
        updated_at=user.updated_at
      )
      for user in users
    ]

  async def search_users(
    self,
    search_term: str,
    skip: int = 0,
    limit: int = 100,
    current_user_role: UserRole = UserRole.STUDENT
  ) -> List[UserResponse]:
    if current_user_role not in [UserRole.ADMIN, UserRole.TEACHER]:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Недостаточно прав для поиска пользователей"
      )

    users = await self.user_repo.search_users(search_term, skip, limit)

    return [
      UserResponse(
        id=user.id,
        display_name=user.display_name,
        login=user.login,
        role=user.role,
        is_deleted=user.delete_flg,
        created_at=user.created_at,
        updated_at=user.updated_at
      )
      for user in users
    ]

  async def get_user_statistics(self, current_user_role: UserRole) -> Dict[str, Any]:
    if current_user_role != UserRole.ADMIN:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Недостаточно прав для просмотра статистики"
      )

    total_users = await self.user_repo.count_users()
    active_users = await self.user_repo.count_users(include_deleted=False)
    deleted_users = await self.user_repo.count_users(include_deleted=True) - active_users

    roles_stats = {}
    for role in UserRole:
      count = await self.user_repo.count_users(role, include_deleted=False)
      roles_stats[role.value] = count

    return {
      "total_users": total_users,
      "active_users": active_users,
      "deleted_users": deleted_users,
      "roles_distribution": roles_stats
    }

  async def get_current_user_profile(self, user_id: UUID) -> UserResponse:
    user = await self.user_repo.get_by_id(user_id)

    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    return UserResponse(
      id=user.id,
      display_name=user.display_name,
      login=user.login,
      role=user.role,
      is_deleted=user.delete_flg,
      created_at=user.created_at,
      updated_at=user.updated_at
    )

  async def update_current_user_profile(
    self,
    user_id: UUID,
    update_data: UserUpdate
  ) -> UserResponse:
    user = await self.user_repo.get_by_id(user_id)

    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    if update_data.login and update_data.login != user.login:
      existing_user = await self.user_repo.get_by_login(update_data.login)
      if existing_user and existing_user.id != user_id:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Пользователь с таким логином уже существует"
        )

    update_dict = update_data.model_dump(exclude_unset=True)

    if "role" in update_dict:
      del update_dict["role"]

    updated_user = await self.user_repo.update(user_id, update_dict)

    if not updated_user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пользователь не найден"
      )

    return UserResponse(
      id=updated_user.id,
      display_name=updated_user.display_name,
      login=updated_user.login,
      role=updated_user.role,
      is_deleted=updated_user.delete_flg,
      created_at=updated_user.created_at,
      updated_at=updated_user.updated_at
    )


async def get_user_service(
  user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
  return UserService(user_repo)
