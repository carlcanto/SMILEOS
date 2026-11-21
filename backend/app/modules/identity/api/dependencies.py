"""Dependencias de FastAPI: sesión de base de datos, usuario autenticado y roles exigidos."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.composition import IdentityRuntime, make_authenticate
from app.modules.identity.domain.entities import Role, User
from app.shared.db import get_session
from app.shared.domain import DomainError, RequestContext

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_runtime(request: Request) -> IdentityRuntime:
    runtime: IdentityRuntime = request.app.state.identity
    return runtime


RuntimeDep = Annotated[IdentityRuntime, Depends(get_runtime)]


def get_context(request: Request) -> RequestContext:
    return RequestContext(
        ip=request.client.host if request.client else None,
        request_id=getattr(request.state, "request_id", None),
    )


ContextDep = Annotated[RequestContext, Depends(get_context)]

# auto_error=False: el error lo produce la aplicación, con el formato único de error.
_bearer = HTTPBearer(auto_error=False)


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: SessionDep,
    runtime: RuntimeDep,
) -> User:
    if credentials is None:
        raise DomainError("not_authenticated", "Debe iniciar sesión.")
    return await make_authenticate(session, runtime).execute(credentials.credentials)


CurrentUser = Annotated[User, Depends(current_user)]


def require_roles(*roles: Role) -> Callable[[User], Awaitable[User]]:
    """Exige que el usuario tenga alguno de los roles indicados."""

    async def checker(user: CurrentUser) -> User:
        if not user.has_any_role(*roles):
            raise DomainError("forbidden", "No tiene permiso para realizar esta acción.")
        return user

    return checker


AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
