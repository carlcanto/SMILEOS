import asyncio

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.modules.audit.infrastructure import orm as _audit_orm  # noqa: F401
from app.modules.identity.infrastructure import orm as _identity_orm  # noqa: F401
from app.shared.db import Base, create_engine
from tests.conftest import TEST_DATABASE_URL, alembic_config, migrate, requires_database

HEAD = ScriptDirectory.from_config(alembic_config()).get_current_head()


def current_versions(url: str) -> list[str]:
    async def query() -> list[str]:
        engine = create_engine(url)
        try:
            async with engine.connect() as connection:
                rows = await connection.execute(text("SELECT version_num FROM alembic_version"))
                return [row[0] for row in rows]
        finally:
            await engine.dispose()

    return asyncio.run(query())


@requires_database
def test_las_migraciones_suben_y_bajan(monkeypatch: pytest.MonkeyPatch) -> None:
    assert TEST_DATABASE_URL is not None
    try:
        migrate("up", "head", monkeypatch)
        assert current_versions(TEST_DATABASE_URL) == [HEAD]
        migrate("down", "base", monkeypatch)
        assert current_versions(TEST_DATABASE_URL) == []
    finally:
        # Las demás pruebas esperan la base en la última migración.
        migrate("up", "head", monkeypatch)


@requires_database
def test_los_modelos_coinciden_con_las_migraciones(migrated_database: None) -> None:
    """Si alguien cambia un modelo y olvida la migración, esta prueba falla."""
    assert TEST_DATABASE_URL is not None

    async def diff() -> list[object]:
        engine = create_engine(TEST_DATABASE_URL)
        try:
            async with engine.connect() as connection:
                return await connection.run_sync(
                    lambda sync: list(
                        compare_metadata(MigrationContext.configure(sync), Base.metadata)
                    )
                )
        finally:
            await engine.dispose()

    assert asyncio.run(diff()) == []
