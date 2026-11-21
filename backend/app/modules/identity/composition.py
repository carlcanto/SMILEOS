"""Raíz de composición de identidad: une los casos de uso con sus adaptadores concretos."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.infrastructure.recorder import SqlAuditRecorder
from app.modules.identity.application.auth import (
    AuthenticateAccessToken,
    ChangePassword,
    Login,
    Logout,
    RefreshSession,
    SessionIssuer,
)
from app.modules.identity.application.users import (
    CreateUser,
    ListUsers,
    SetUserActive,
    UpdateUser,
)
from app.modules.identity.infrastructure.repositories import (
    SqlRefreshTokenRepository,
    SqlUserRepository,
)
from app.modules.identity.infrastructure.security import (
    Argon2PasswordHasher,
    JwtAccessTokenService,
    SecureTokenGenerator,
)
from app.shared.config import Settings
from app.shared.infrastructure import SqlUnitOfWork, SystemClock


@dataclass(frozen=True)
class IdentityRuntime:
    """Piezas sin estado por petición: se crean una vez al arrancar la aplicación."""

    hasher: Argon2PasswordHasher
    access_tokens: JwtAccessTokenService
    token_generator: SecureTokenGenerator
    clock: SystemClock
    refresh_token_days: int


def build_runtime(settings: Settings) -> IdentityRuntime:
    clock = SystemClock()
    return IdentityRuntime(
        hasher=Argon2PasswordHasher(),
        access_tokens=JwtAccessTokenService(
            settings.jwt_secret, settings.access_token_minutes, clock
        ),
        token_generator=SecureTokenGenerator(),
        clock=clock,
        refresh_token_days=settings.refresh_token_days,
    )


class _Deps:
    """Adaptadores ligados a una sesión de base de datos (una por petición)."""

    def __init__(self, session: AsyncSession, runtime: IdentityRuntime) -> None:
        self.runtime = runtime
        self.users = SqlUserRepository(session)
        self.refresh_tokens = SqlRefreshTokenRepository(session)
        self.audit = SqlAuditRecorder(session)
        self.uow = SqlUnitOfWork(session)
        self.issuer = SessionIssuer(
            runtime.access_tokens,
            runtime.token_generator,
            self.refresh_tokens,
            runtime.clock,
            runtime.refresh_token_days,
        )


def make_login(session: AsyncSession, runtime: IdentityRuntime) -> Login:
    d = _Deps(session, runtime)
    return Login(d.users, runtime.hasher, d.issuer, d.audit, d.uow, runtime.clock)


def make_refresh(session: AsyncSession, runtime: IdentityRuntime) -> RefreshSession:
    d = _Deps(session, runtime)
    return RefreshSession(
        d.users,
        d.refresh_tokens,
        runtime.token_generator,
        d.issuer,
        d.audit,
        d.uow,
        runtime.clock,
    )


def make_logout(session: AsyncSession, runtime: IdentityRuntime) -> Logout:
    d = _Deps(session, runtime)
    return Logout(d.refresh_tokens, runtime.token_generator, d.audit, d.uow, runtime.clock)


def make_change_password(session: AsyncSession, runtime: IdentityRuntime) -> ChangePassword:
    d = _Deps(session, runtime)
    return ChangePassword(d.users, d.refresh_tokens, runtime.hasher, d.audit, d.uow, runtime.clock)


def make_authenticate(session: AsyncSession, runtime: IdentityRuntime) -> AuthenticateAccessToken:
    return AuthenticateAccessToken(runtime.access_tokens, SqlUserRepository(session))


def make_create_user(session: AsyncSession, runtime: IdentityRuntime) -> CreateUser:
    d = _Deps(session, runtime)
    return CreateUser(d.users, runtime.hasher, d.audit, d.uow, runtime.clock)


def make_list_users(session: AsyncSession) -> ListUsers:
    return ListUsers(SqlUserRepository(session))


def make_update_user(session: AsyncSession, runtime: IdentityRuntime) -> UpdateUser:
    d = _Deps(session, runtime)
    return UpdateUser(d.users, d.audit, d.uow)


def make_set_user_active(session: AsyncSession, runtime: IdentityRuntime) -> SetUserActive:
    d = _Deps(session, runtime)
    return SetUserActive(d.users, d.refresh_tokens, d.audit, d.uow, runtime.clock)
