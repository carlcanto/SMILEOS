import os

import pytest

from app.shared.config import Settings

# Base real para las pruebas de integración; en CI viene del servicio de Postgres.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
# Puerto 1: nada escucha, la conexión se rechaza de inmediato.
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://smileos:x@127.0.0.1:1/none"

requires_database = pytest.mark.skipif(
    TEST_DATABASE_URL is None, reason="TEST_DATABASE_URL no está definida"
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL or UNREACHABLE_DATABASE_URL,
        _env_file=None,
    )


@pytest.fixture
def unreachable_settings() -> Settings:
    return Settings(
        database_url=UNREACHABLE_DATABASE_URL,
        worker_poll_seconds=0.05,
        _env_file=None,
    )
