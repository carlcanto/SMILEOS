"""Casos de uso de sesión: iniciar, renovar, cerrar y cambiar contraseña."""

from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from app.modules.audit.application.ports import AuditRecorder
from app.modules.audit.domain.events import AuditEvent
from app.modules.identity.application.ports import (
    AccessTokenService,
    PasswordHasher,
    RefreshTokenGenerator,
    RefreshTokenRepository,
    UserRepository,
)
from app.modules.identity.domain.entities import RefreshToken, User
from app.modules.identity.domain.password_policy import normalize_email, validate_password
from app.shared.domain import DomainError, RequestContext
from app.shared.ports import Clock, UnitOfWork

INVALID_TOKEN = DomainError("invalid_token", "La sesión no es válida o expiró.")
BAD_CREDENTIALS_MESSAGE = "Correo o contraseña incorrectos."


@dataclass(frozen=True)
class AuthSession:
    access_token: str
    refresh_token: str
    expires_in: int
    user: User


def _invalid_token() -> DomainError:
    return DomainError(INVALID_TOKEN.code, INVALID_TOKEN.message)


class SessionIssuer:
    """Crea el par de tokens de una sesión y guarda el hash del de refresco."""

    def __init__(
        self,
        access_tokens: AccessTokenService,
        refresh_generator: RefreshTokenGenerator,
        refresh_tokens: RefreshTokenRepository,
        clock: Clock,
        refresh_token_days: int,
    ) -> None:
        self._access_tokens = access_tokens
        self._generator = refresh_generator
        self._refresh_tokens = refresh_tokens
        self._clock = clock
        self._refresh_days = refresh_token_days

    async def issue(self, user: User) -> AuthSession:
        raw_refresh = self._generator.generate()
        await self._refresh_tokens.add(
            RefreshToken(
                id=uuid4(),
                user_id=user.id,
                token_hash=self._generator.hash(raw_refresh),
                expires_at=self._clock.now() + timedelta(days=self._refresh_days),
            )
        )
        access, expires_in = self._access_tokens.issue(user.id)
        return AuthSession(access, raw_refresh, expires_in, user)


class Login:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        issuer: SessionIssuer,
        audit: AuditRecorder,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._issuer = issuer
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(self, email: str, password: str, ctx: RequestContext) -> AuthSession:
        user = await self._users.get_by_email(normalize_email(email))
        # Siempre se verifica un hash (real o falso): la respuesta no revela si el correo existe.
        password_ok = await self._hasher.verify(user.password_hash if user else None, password)
        reason = None
        if user is None:
            reason = "unknown_user"
        elif not password_ok:
            reason = "bad_password"
        elif not user.is_active:
            reason = "inactive"
        if reason is not None or user is None:
            await self._audit.record(
                AuditEvent(
                    action="login_failed",
                    actor_user_id=user.id if user else None,
                    entity_type="user",
                    entity_id=str(user.id) if user else None,
                    details={"reason": reason},
                    ip=ctx.ip,
                    request_id=ctx.request_id,
                )
            )
            await self._uow.commit()
            raise DomainError("invalid_credentials", BAD_CREDENTIALS_MESSAGE)

        if self._hasher.needs_rehash(user.password_hash):
            user.password_hash = await self._hasher.hash(password)
        user.last_login_at = self._clock.now()
        await self._users.save(user)
        session = await self._issuer.issue(user)
        await self._audit.record(
            AuditEvent(
                action="login_success",
                actor_user_id=user.id,
                entity_type="user",
                entity_id=str(user.id),
                ip=ctx.ip,
                request_id=ctx.request_id,
            )
        )
        await self._uow.commit()
        return session


class RefreshSession:
    """Renueva la sesión rotando el token de refresco.

    Un token ya usado que vuelve a presentarse indica que pudo ser robado: se revocan
    todos los tokens del usuario y se registra el evento.
    """

    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        refresh_generator: RefreshTokenGenerator,
        issuer: SessionIssuer,
        audit: AuditRecorder,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._generator = refresh_generator
        self._issuer = issuer
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(self, refresh_token: str, ctx: RequestContext) -> AuthSession:
        now = self._clock.now()
        stored = await self._refresh_tokens.get_by_hash(self._generator.hash(refresh_token))
        if stored is None:
            raise _invalid_token()
        if stored.revoked_at is not None:
            await self._refresh_tokens.revoke_all_for_user(stored.user_id, now)
            await self._audit.record(
                AuditEvent(
                    action="refresh_reuse_detected",
                    actor_user_id=stored.user_id,
                    entity_type="user",
                    entity_id=str(stored.user_id),
                    ip=ctx.ip,
                    request_id=ctx.request_id,
                )
            )
            await self._uow.commit()
            raise _invalid_token()
        if stored.expires_at <= now:
            raise _invalid_token()
        user = await self._users.get(stored.user_id)
        if user is None or not user.is_active:
            raise _invalid_token()

        await self._refresh_tokens.revoke(stored.id, now)
        session = await self._issuer.issue(user)
        await self._uow.commit()
        return session


class Logout:
    def __init__(
        self,
        refresh_tokens: RefreshTokenRepository,
        refresh_generator: RefreshTokenGenerator,
        audit: AuditRecorder,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._refresh_tokens = refresh_tokens
        self._generator = refresh_generator
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(self, actor: User, refresh_token: str, ctx: RequestContext) -> None:
        """Idempotente: un token desconocido o ajeno no produce error ni se revoca."""
        stored = await self._refresh_tokens.get_by_hash(self._generator.hash(refresh_token))
        if stored is not None and stored.user_id == actor.id and stored.revoked_at is None:
            await self._refresh_tokens.revoke(stored.id, self._clock.now())
        await self._audit.record(
            AuditEvent(
                action="logout",
                actor_user_id=actor.id,
                entity_type="user",
                entity_id=str(actor.id),
                ip=ctx.ip,
                request_id=ctx.request_id,
            )
        )
        await self._uow.commit()


class ChangePassword:
    def __init__(
        self,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        hasher: PasswordHasher,
        audit: AuditRecorder,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._hasher = hasher
        self._audit = audit
        self._uow = uow
        self._clock = clock

    async def execute(
        self, actor: User, current_password: str, new_password: str, ctx: RequestContext
    ) -> None:
        if not await self._hasher.verify(actor.password_hash, current_password):
            raise DomainError("wrong_current_password", "La contraseña actual no es correcta.")
        validate_password(new_password, email=actor.email)
        if new_password == current_password:
            raise DomainError(
                "weak_password", "La nueva contraseña debe ser distinta de la actual."
            )
        actor.password_hash = await self._hasher.hash(new_password)
        await self._users.save(actor)
        # Cierra las demás sesiones: quien tuviera la contraseña vieja pierde el acceso.
        await self._refresh_tokens.revoke_all_for_user(actor.id, self._clock.now())
        await self._audit.record(
            AuditEvent(
                action="password_changed",
                actor_user_id=actor.id,
                entity_type="user",
                entity_id=str(actor.id),
                ip=ctx.ip,
                request_id=ctx.request_id,
            )
        )
        await self._uow.commit()


class AuthenticateAccessToken:
    """Resuelve el usuario de una petición. La base es la autoridad: si se desactiva
    al usuario o se le cambian los roles, el efecto es inmediato aunque el token siga vigente."""

    def __init__(self, access_tokens: AccessTokenService, users: UserRepository) -> None:
        self._access_tokens = access_tokens
        self._users = users

    async def execute(self, token: str) -> User:
        user_id = self._access_tokens.decode(token)
        user = await self._users.get(user_id)
        if user is None or not user.is_active:
            raise _invalid_token()
        return user
