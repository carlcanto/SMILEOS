import asyncio
import os
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.cli import create_user
from app.main import create_app
from app.modules.identity.domain.entities import Role, User
from app.shared.config import Settings, get_settings
from app.shared.db import create_engine

BACKEND = Path(__file__).resolve().parents[1]

# Base real para las pruebas de integración; en CI viene del servicio de Postgres.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
# Puerto 1: nada escucha, la conexión se rechaza de inmediato.
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://smileos:x@127.0.0.1:1/none"
TEST_JWT_SECRET = "clave-de-pruebas-que-supera-los-32-caracteres"
DEFAULT_PASSWORD = "contrasena-larga-123"
OTHER_PASSWORD = "otra-contrasena-valida-2"

requires_database = pytest.mark.skipif(
    TEST_DATABASE_URL is None, reason="TEST_DATABASE_URL no está definida"
)


def alembic_config() -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    return config


def migrate(direction: str, revision: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Corre Alembic contra la base de pruebas con la configuración de pruebas."""
    assert TEST_DATABASE_URL is not None
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)
    get_settings.cache_clear()
    try:
        runner = command.upgrade if direction == "up" else command.downgrade
        runner(alembic_config(), revision)
    finally:
        get_settings.cache_clear()


def run_sql(sql: str, **params: object) -> list[tuple[Any, ...]]:
    assert TEST_DATABASE_URL is not None

    async def execute() -> list[tuple[Any, ...]]:
        engine = create_engine(TEST_DATABASE_URL)
        try:
            async with engine.begin() as connection:
                result = await connection.execute(text(sql), params)
                return [tuple(row) for row in result.fetchall()] if result.returns_rows else []
        finally:
            await engine.dispose()

    return asyncio.run(execute())


@pytest.fixture(scope="session")
def migrated_database() -> None:
    """Deja la base de pruebas en la última migración, partiendo de cero."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        migrate("down", "base", monkeypatch)
        migrate("up", "head", monkeypatch)


@pytest.fixture
def clean_database(migrated_database: None) -> None:
    run_sql("TRUNCATE refresh_tokens, user_roles, audit_log, users RESTART IDENTITY CASCADE")


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL or UNREACHABLE_DATABASE_URL,
        jwt_secret=TEST_JWT_SECRET,
        _env_file=None,
    )


@pytest.fixture
def unreachable_settings() -> Settings:
    return Settings(
        database_url=UNREACHABLE_DATABASE_URL,
        jwt_secret=TEST_JWT_SECRET,
        worker_poll_seconds=0.05,
        _env_file=None,
    )


@pytest.fixture
def client(settings: Settings, clean_database: None) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


UserFactory = Callable[..., User]


@pytest.fixture
def make_user(settings: Settings, clean_database: None) -> UserFactory:
    def factory(
        email: str = "admin@example.com",
        roles: Iterable[Role] = (Role.ADMIN,),
        password: str = DEFAULT_PASSWORD,
        full_name: str = "Persona de Prueba",
    ) -> User:
        return asyncio.run(
            create_user(settings, email=email, full_name=full_name, password=password, roles=roles)
        )

    return factory


def login(
    client: TestClient, email: str = "admin@example.com", password: str = DEFAULT_PASSWORD
) -> dict[str, Any]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def bearer(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
