from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.modules.identity.application.auth import AuthSession
from app.modules.identity.domain.entities import Role, User

# Validación deliberadamente simple: un correo interno como admin@clinica.local es válido.
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+$",
    ),
]
# El tope de 256 solo acota el costo de procesar la entrada; la política real está en el dominio.
Password = Annotated[str, Field(min_length=1, max_length=256)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class LoginRequest(BaseModel):
    email: Email
    password: Password


class RefreshRequest(BaseModel):
    refresh_token: Annotated[str, Field(min_length=1, max_length=512)]


class ChangePasswordRequest(BaseModel):
    current_password: Password
    new_password: Password


class CreateUserRequest(BaseModel):
    email: Email
    full_name: FullName
    password: Password
    roles: Annotated[list[Role], Field(min_length=1)]


class UpdateUserRequest(BaseModel):
    full_name: FullName | None = None
    roles: Annotated[list[Role], Field(min_length=1)] | None = None


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    roles: list[Role]
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserOut":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=sorted(user.roles),
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut

    @classmethod
    def from_session(cls, session: AuthSession) -> "TokenResponse":
        return cls(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in,
            user=UserOut.from_user(session.user),
        )


class RoleOut(BaseModel):
    code: Role
    description: str
