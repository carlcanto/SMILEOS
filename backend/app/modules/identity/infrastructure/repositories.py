from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.entities import RefreshToken, Role, User
from app.modules.identity.infrastructure.orm import (
    RefreshTokenRecord,
    UserRecord,
    UserRoleRecord,
)
from app.shared.domain import DomainError


def _to_user(record: UserRecord) -> User:
    return User(
        id=record.id,
        email=record.email,
        full_name=record.full_name,
        password_hash=record.password_hash,
        is_active=record.is_active,
        roles=frozenset(Role(link.role_code) for link in record.role_links),
        created_at=record.created_at,
        last_login_at=record.last_login_at,
    )


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> User | None:
        record = await self._session.get(UserRecord, user_id)
        return _to_user(record) if record else None

    async def get_by_email(self, email: str) -> User | None:
        record = await self._session.scalar(select(UserRecord).where(UserRecord.email == email))
        return _to_user(record) if record else None

    async def add(self, user: User) -> None:
        record = UserRecord(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
        record.role_links = [
            UserRoleRecord(user_id=user.id, role_code=role.value) for role in user.roles
        ]
        self._session.add(record)
        try:
            await self._session.flush()
        except IntegrityError as error:
            # Dos altas simultáneas con el mismo correo: la llave única de la base decide.
            await self._session.rollback()
            if "uq_users_email" in str(error.orig):
                raise DomainError(
                    "email_already_exists", "Ya existe un usuario con ese correo."
                ) from error
            raise

    async def save(self, user: User) -> None:
        record = await self._session.get(UserRecord, user.id)
        if record is None:
            raise LookupError(f"Usuario {user.id} no existe")
        record.email = user.email
        record.full_name = user.full_name
        record.password_hash = user.password_hash
        record.is_active = user.is_active
        record.last_login_at = user.last_login_at
        wanted = {role.value for role in user.roles}
        for link in list(record.role_links):
            if link.role_code not in wanted:
                record.role_links.remove(link)
        present = {link.role_code for link in record.role_links}
        for code in wanted - present:
            record.role_links.append(UserRoleRecord(user_id=record.id, role_code=code))
        await self._session.flush()

    async def list_page(
        self, *, page: int, per_page: int, active: bool | None
    ) -> tuple[list[User], int]:
        query = select(UserRecord)
        if active is not None:
            query = query.where(UserRecord.is_active.is_(active))
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self._session.scalars(
            query.order_by(UserRecord.created_at, UserRecord.id)
            .limit(per_page)
            .offset((page - 1) * per_page)
        )
        return [_to_user(record) for record in rows], total or 0

    async def lock_active_admins(self) -> list[UUID]:
        rows = await self._session.scalars(
            select(UserRecord.id)
            .join(UserRoleRecord, UserRoleRecord.user_id == UserRecord.id)
            .where(UserRoleRecord.role_code == Role.ADMIN.value, UserRecord.is_active.is_(True))
            .with_for_update(of=UserRecord)
        )
        return list(rows)


class SqlRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: RefreshToken) -> None:
        self._session.add(
            RefreshTokenRecord(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                revoked_at=token.revoked_at,
            )
        )
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        record = await self._session.scalar(
            select(RefreshTokenRecord).where(RefreshTokenRecord.token_hash == token_hash)
        )
        if record is None:
            return None
        return RefreshToken(
            id=record.id,
            user_id=record.user_id,
            token_hash=record.token_hash,
            expires_at=record.expires_at,
            revoked_at=record.revoked_at,
        )

    async def revoke(self, token_id: UUID, at: datetime) -> None:
        await self._session.execute(
            update(RefreshTokenRecord)
            .where(RefreshTokenRecord.id == token_id)
            .values(revoked_at=at)
        )

    async def revoke_all_for_user(self, user_id: UUID, at: datetime) -> None:
        await self._session.execute(
            update(RefreshTokenRecord)
            .where(RefreshTokenRecord.user_id == user_id, RefreshTokenRecord.revoked_at.is_(None))
            .values(revoked_at=at)
        )
