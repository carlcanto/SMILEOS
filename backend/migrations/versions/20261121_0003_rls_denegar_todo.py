"""Activa RLS (sin políticas) en todas las tablas: la API de datos de Supabase no las ve.

Supabase puede exponer las tablas del esquema ``public`` por su API REST con una llave
pública. SmileOS no usa esa API: solo se conecta como dueño de las tablas (que ignora
RLS). Activar RLS sin políticas deja a los demás roles sin acceso a ninguna fila.
Cada migración que cree una tabla debe hacer lo mismo; una prueba lo verifica.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("roles", "users", "user_roles", "refresh_tokens", "audit_log", "alembic_version")


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
