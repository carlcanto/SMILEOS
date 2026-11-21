"""Comandos de administración: ``create-admin`` y ``migrate`` (``python -m app.cli ...``).

El primer administrador no puede crearse por la API (haría falta uno para crearlo), y
nunca se deja una contraseña fija en el código: se pide por teclado o por ADMIN_PASSWORD.
"""

import argparse
import asyncio
import getpass
import os
import sys
from collections.abc import Iterable

from app.migrations import upgrade_to_head
from app.modules.identity.composition import build_runtime, make_create_user
from app.modules.identity.domain.entities import Role, User
from app.shared.config import Settings, get_settings
from app.shared.db import create_engine, create_session_factory
from app.shared.domain import DomainError, RequestContext


async def create_user(
    settings: Settings,
    *,
    email: str,
    full_name: str,
    password: str,
    roles: Iterable[Role],
) -> User:
    engine = create_engine(settings.database_url)
    try:
        async with create_session_factory(engine)() as session:
            return await make_create_user(session, build_runtime(settings)).execute(
                None,
                email=email,
                full_name=full_name,
                password=password,
                roles=roles,
                ctx=RequestContext(),
                via="cli",
            )
    finally:
        await engine.dispose()


def _read_password() -> str:
    from_env = os.environ.get("ADMIN_PASSWORD")
    if from_env:
        return from_env
    first = getpass.getpass("Contraseña: ")
    if first != getpass.getpass("Repita la contraseña: "):
        raise DomainError("weak_password", "Las contraseñas no coinciden.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin", help="Crea un usuario con el rol administrador")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True, help="Nombre completo")
    commands.add_parser("migrate", help="Crea o actualiza las tablas de la base de datos")
    args = parser.parse_args(argv)

    if args.command == "migrate":
        upgrade_to_head(get_settings().database_url)
        print("Base de datos al día.")
        return 0

    try:
        user = asyncio.run(
            create_user(
                get_settings(),
                email=args.email,
                full_name=args.name,
                password=_read_password(),
                roles=[Role.ADMIN],
            )
        )
    except DomainError as error:
        print(f"Error: {error.message}", file=sys.stderr)
        return 1
    print(f"Administrador creado: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
