"""Entorno de Alembic (asíncrono). Lee DATABASE_URL de la misma configuración que la API."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importar los modelos de cada módulo los registra en Base.metadata.
from app.migrations import MIGRATION_LOCK_ID
from app.modules.audit.infrastructure import orm as _audit_orm  # noqa: F401, I001
from app.modules.identity.infrastructure import orm as _identity_orm  # noqa: F401, I001
from app.shared.config import get_settings
from app.shared.db import Base

config = context.config
# Cuando la API aplica las migraciones al arrancar no se toca la configuración de logs.
if config.config_file_name is not None and config.attributes.get("configure_logging", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# La URL puede venir de quien invoca (app.migrations) o del entorno (CLI de Alembic).
database_url: str = config.attributes.get("database_url") or get_settings().database_url
# configparser interpreta "%" como interpolación: se escapa para contraseñas con "%".
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        connection.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": MIGRATION_LOCK_ID})
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
