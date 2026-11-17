import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.shared.config import get_settings
from app.shared.db import create_engine
from tests.conftest import TEST_DATABASE_URL, requires_database

BACKEND = Path(__file__).resolve().parents[1]


def alembic_config() -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    return config


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
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    get_settings.cache_clear()
    try:
        command.upgrade(alembic_config(), "head")
        assert current_versions(TEST_DATABASE_URL) == ["0001"]
        command.downgrade(alembic_config(), "base")
        assert current_versions(TEST_DATABASE_URL) == []
    finally:
        get_settings.cache_clear()
