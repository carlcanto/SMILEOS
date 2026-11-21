"""Administrador inicial: permite arrancar en la nube sin acceso a una terminal."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.identity.composition import IdentityRuntime, make_create_user, make_list_users
from app.modules.identity.domain.entities import Role
from app.shared.config import Settings
from app.shared.domain import DomainError, RequestContext

logger = logging.getLogger("app.bootstrap")


async def ensure_bootstrap_admin(
    settings: Settings,
    runtime: IdentityRuntime,
    session_factory: async_sessionmaker[AsyncSession],
) -> bool:
    """Crea el administrador de ``BOOTSTRAP_ADMIN_*`` solo si la base aún no tiene usuarios.

    Nunca modifica ni reemplaza a un usuario existente, así que dejar las variables
    definidas es inofensivo (aunque conviene borrarlas). Devuelve si creó el usuario.
    """
    email = settings.bootstrap_admin_email
    name = settings.bootstrap_admin_name
    password = settings.bootstrap_admin_password
    if not (email and name and password):
        return False
    async with session_factory() as session:
        _, total = await make_list_users(session).execute(page=1, per_page=1, active=None)
        if total > 0:
            return False
        try:
            await make_create_user(session, runtime).execute(
                None,
                email=email,
                full_name=name,
                password=password,
                roles=[Role.ADMIN],
                ctx=RequestContext(),
                via="bootstrap",
            )
        except DomainError as error:
            if error.code == "email_already_exists":
                # Otra instancia lo creó un instante antes: es el resultado esperado.
                return False
            raise
    return True
