"""Aplicación de las migraciones desde código: la usan la API (al arrancar) y el CLI.

El mismo esquema se crea en cualquier base de Postgres vacía, sea el contenedor de la
clínica o un proyecto de Supabase de cualquier cuenta: solo cambia ``DATABASE_URL``.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[1]
# Candado de la base: evita que dos instancias apliquen las migraciones a la vez.
MIGRATION_LOCK_ID = 7_283_105_194


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.attributes["database_url"] = database_url
    config.attributes["configure_logging"] = False
    return config


def upgrade_to_head(database_url: str) -> None:
    """Lleva la base a la última migración. Es idempotente y segura con varias instancias."""
    command.upgrade(alembic_config(database_url), "head")
