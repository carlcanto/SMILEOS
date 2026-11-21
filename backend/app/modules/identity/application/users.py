"""Casos de uso de administración de usuarios."""

from collections.abc import Iterable
from uuid import UUID, uuid4

from app.modules.audit.application.ports import AuditRecorder
from app.modules.audit.domain.events import AuditEvent
from app.modules.identity.application.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    UserRepository,
)
from app.modules.identity.domain.entities import Role, User
from app.modules.identity.domain.password_policy import normalize_email, validate_password
from app.shared.domain import DomainError, RequestContext
from app.shared.ports import Clock, UnitOfWork

USER_NOT_FOUND = "No existe un usuario con ese identificador."


def _user_event(
    action: str,
    actor: User | None,
    target: User,
    ctx: RequestContext,
    details: dict[str, object] | None = None,
) -> AuditEvent:
    return AuditEvent(
        action=action,
        actor_user_id=actor.id if actor else None,
        entity_type="user",
        entity_id=str(target.id),
        details=details or {},
        ip=ctx.ip,
        request_id=ctx.request_id,
    )


async def _ensure_not_last_admin(users: UserRepository, target: User) -> None:
    """Siempre debe quedar al menos un administrador activo (si no, nadie podría administrar)."""
    admin_ids = await users.lock_active_admins()
    if target.id in admin_ids and len(admin_ids) == 1:
        raise DomainError("last_admin", "Debe quedar al menos un administrador activo.")


class CreateUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        audit: AuditRecorder,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(
        self,
        actor: User | None,
        *,
        email: str,
        full_name: str,
        password: str,
        roles: Iterable[Role],
        ctx: RequestContext,
        via: str = "api",
    ) -> User:
        email = normalize_email(email)
        validate_password(password, email=email)
        if await self._users.get_by_email(email) is not None:
            raise DomainError("email_already_exists", "Ya existe un usuario con ese correo.")
        user = User(
            id=uuid4(),
            email=email,
            full_name=full_name.strip(),
            password_hash=await self._hasher.hash(password),
            is_active=True,
            roles=frozenset(roles),
            created_at=self._clock.now(),
        )
        await self._users.add(user)
        await self._audit.record(
            _user_event(
                "user_created",
                actor,
                user,
                ctx,
                {"roles": sorted(role.value for role in user.roles), "via": via},
            )
        )
        await self._uow.commit()
        return user


class ListUsers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(
        self, *, page: int, per_page: int, active: bool | None
    ) -> tuple[list[User], int]:
        return await self._users.list_page(page=page, per_page=per_page, active=active)


class UpdateUser:
    def __init__(self, users: UserRepository, audit: AuditRecorder, uow: UnitOfWork) -> None:
        self._users = users
        self._audit = audit
        self._uow = uow

    async def execute(
        self,
        actor: User,
        user_id: UUID,
        *,
        full_name: str | None,
        roles: frozenset[Role] | None,
        ctx: RequestContext,
    ) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise DomainError("user_not_found", USER_NOT_FOUND)
        changed: list[str] = []
        if full_name is not None and full_name.strip() != user.full_name:
            user.full_name = full_name.strip()
            changed.append("full_name")
        if roles is not None and roles != user.roles:
            if Role.ADMIN in user.roles and Role.ADMIN not in roles:
                await _ensure_not_last_admin(self._users, user)
            user.roles = roles
            changed.append("roles")
        if changed:
            await self._users.save(user)
            await self._audit.record(
                _user_event(
                    "user_updated",
                    actor,
                    user,
                    ctx,
                    {"changed": changed, "roles": sorted(role.value for role in user.roles)},
                )
            )
            await self._uow.commit()
        return user


class SetUserActive:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        audit: AuditRecorder,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(
        self, actor: User, user_id: UUID, *, active: bool, ctx: RequestContext
    ) -> User:
        user = await self._users.get(user_id)
        if user is None:
            raise DomainError("user_not_found", USER_NOT_FOUND)
        if user.is_active == active:
            return user
        if not active:
            if user.id == actor.id:
                raise DomainError("self_deactivation", "No puede desactivar su propia cuenta.")
            if Role.ADMIN in user.roles:
                await _ensure_not_last_admin(self._users, user)
        user.is_active = active
        await self._users.save(user)
        if not active:
            await self._refresh_tokens.revoke_all_for_user(user.id, self._clock.now())
        await self._audit.record(
            _user_event("user_activated" if active else "user_deactivated", actor, user, ctx)
        )
        await self._uow.commit()
        return user
