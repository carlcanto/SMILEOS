"""Puertos de identidad: lo que los casos de uso piden al exterior."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.identity.domain.entities import RefreshToken, User


class UserRepository(Protocol):
    async def get(self, user_id: UUID) -> User | None: ...

    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None:
        """Lanza ``DomainError('email_already_exists')`` si el correo ya está registrado."""
        ...

    async def save(self, user: User) -> None: ...

    async def list_page(
        self, *, page: int, per_page: int, active: bool | None
    ) -> tuple[list[User], int]: ...

    async def lock_active_admins(self) -> list[UUID]:
        """Ids de los administradores activos, bloqueando sus filas hasta el ``commit``."""
        ...


class RefreshTokenRepository(Protocol):
    async def add(self, token: RefreshToken) -> None: ...

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def revoke(self, token_id: UUID, at: datetime) -> None: ...

    async def revoke_all_for_user(self, user_id: UUID, at: datetime) -> None: ...


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...

    async def verify(self, password_hash: str | None, password: str) -> bool:
        """Con ``None`` verifica contra un hash falso (mismo tiempo) y devuelve ``False``."""
        ...

    def needs_rehash(self, password_hash: str) -> bool: ...


class AccessTokenService(Protocol):
    def issue(self, user_id: UUID) -> tuple[str, int]:
        """Devuelve el token de acceso y su vida en segundos."""
        ...

    def decode(self, token: str) -> UUID:
        """Devuelve el id del usuario o lanza ``DomainError('invalid_token')``."""
        ...


class RefreshTokenGenerator(Protocol):
    def generate(self) -> str: ...

    def hash(self, token: str) -> str: ...
