from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from services.courses_service.app.modules.courses.enums import UserRole


class UserBase(BaseModel):
    display_name: str | None = None
    login: str | None = None
    role: UserRole

    @field_validator('display_name', 'login')
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and isinstance(v, str):
            if not v.strip():
                raise ValueError('Поле не может быть пустым или состоять только из пробелов')
        return v

    @field_validator('role', mode='before')
    @classmethod
    def validate_role_on_create(cls, v):
        if isinstance(v, str):
            v = v.lower()
        try:
            return UserRole(v)
        except ValueError:
            raise ValueError(f'Роль должна быть одной из: {", ".join([role.value for role in UserRole])}')


class UserCreate(UserBase):
  pass



class UserUpdate(BaseModel):
    display_name: str | None = None
    login: str | None = None
    role: UserRole | None = None

    @field_validator('display_name', 'login')
    @classmethod
    def validate_not_empty_on_update(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Поле не может быть пустым или состоять только из пробелов')
        return v

    @field_validator('role', mode='before')
    @classmethod
    def validate_role_on_update(cls, v):
        if v is not None:
            if isinstance(v, str):
                v = v.lower()
            try:
                return UserRole(v)
            except ValueError:
                raise ValueError(f'Роль должна быть одной из: {", ".join([role.value for role in UserRole])}')
        return v

    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        if all(value is None for value in [self.display_name, self.login, self.role]):
            raise ValueError('Хотя бы одно поле должно быть указано для обновления')
        return self

    model_config = ConfigDict(extra='forbid')


class UserResponse(BaseModel):
    id: UUID
    display_name: str | None = None
    login: str | None = None
    role: UserRole
    deleted_flg: bool = False
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

