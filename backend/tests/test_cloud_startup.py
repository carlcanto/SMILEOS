"""La API crea el esquema y el administrador inicial en cualquier base vacía.

Es lo que permite enlazar un proyecto de Supabase de cualquier cuenta: basta apuntar
``DATABASE_URL`` a él. Estas pruebas parten de una base sin tablas y la dejan al final
en la última migración, como esperan las demás pruebas.
"""

import asyncio
import os
import sys
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.cli import main
from app.main import create_app
from app.migrations import BACKEND_DIR, MIGRATION_LOCK_ID
from app.shared.config import Settings, get_settings
from app.shared.db import create_engine
from tests.conftest import (
    DEFAULT_PASSWORD,
    TEST_DATABASE_URL,
    TEST_JWT_SECRET,
    UNREACHABLE_DATABASE_URL,
    login,
    migrate,
    requires_database,
    run_sql,
)
from tests.test_migrations import HEAD

pytestmark = requires_database

APP_TABLES = ("audit_log", "refresh_tokens", "roles", "user_roles", "users")


@pytest.fixture
def empty_database(migrated_database: None, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    migrate("down", "base", monkeypatch)
    yield
    migrate("up", "head", monkeypatch)


def existing_tables() -> list[str]:
    rows = run_sql(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = ANY(:names) ORDER BY 1",
        names=list(APP_TABLES),
    )
    return [row[0] for row in rows]


def cloud_settings(settings: Settings, **extra: object) -> Settings:
    return settings.model_copy(
        update={"app_profile": "cloud", "run_migrations_on_start": True, **extra}
    )


def bootstrap(**overrides: str) -> dict[str, str]:
    return {
        "bootstrap_admin_email": "Demo@Tesis.example",
        "bootstrap_admin_name": "Administrador Demo",
        "bootstrap_admin_password": "contrasena-demo-1234",
        **overrides,
    }


def test_sin_la_opcion_la_api_no_toca_el_esquema(empty_database: None, settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        assert client.get("/health/ready").status_code == 200  # la conexión funciona
    assert existing_tables() == []


def test_la_api_crea_todas_las_tablas_en_una_base_vacia(
    empty_database: None, settings: Settings
) -> None:
    assert existing_tables() == []
    with TestClient(create_app(cloud_settings(settings))) as client:
        assert client.get("/health/ready").json()["profile"] == "cloud"
    assert existing_tables() == list(APP_TABLES)
    assert run_sql("SELECT version_num FROM alembic_version") == [(HEAD,)]
    assert run_sql("SELECT code FROM roles ORDER BY 1") == [
        ("admin",),
        ("odontologo",),
        ("recepcion",),
    ]


def test_arrancar_varias_veces_no_falla_ni_duplica(
    empty_database: None, settings: Settings
) -> None:
    for _ in range(3):
        with TestClient(create_app(cloud_settings(settings))):
            pass
    assert run_sql("SELECT count(*) FROM roles")[0][0] == 3
    assert run_sql("SELECT version_num FROM alembic_version") == [(HEAD,)]


def test_una_instancia_espera_el_candado_si_otra_esta_migrando(empty_database: None) -> None:
    """Se retiene el candado como lo haría otra instancia a mitad de migración.

    Una segunda instancia (proceso aparte, como en producción) debe esperar y, al
    liberarse el candado, terminar sin error ni tablas duplicadas.
    """
    assert TEST_DATABASE_URL is not None
    env = {**os.environ, "DATABASE_URL": TEST_DATABASE_URL, "JWT_SECRET": TEST_JWT_SECRET}

    async def scenario() -> None:
        engine = create_engine(TEST_DATABASE_URL)
        try:
            async with engine.connect() as holder:
                await holder.execute(
                    text("SELECT pg_advisory_xact_lock(:id)"), {"id": MIGRATION_LOCK_ID}
                )
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "app.cli",
                    "migrate",
                    cwd=BACKEND_DIR,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.sleep(5)
                assert process.returncode is None, "debía esperar el candado"
                tables = await holder.execute(
                    text(
                        "SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_name = 'users'"
                    )
                )
                assert tables.scalar_one() == 0
                await holder.commit()  # libera el candado
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            assert process.returncode == 0, stderr.decode()
        finally:
            await engine.dispose()

    asyncio.run(scenario())
    assert existing_tables() == list(APP_TABLES)
    assert run_sql("SELECT version_num FROM alembic_version") == [(HEAD,)]


def test_el_administrador_inicial_puede_iniciar_sesion(
    empty_database: None, settings: Settings
) -> None:
    configured = cloud_settings(settings, **bootstrap())
    with TestClient(create_app(configured)) as client:
        tokens = login(client, "demo@tesis.example", "contrasena-demo-1234")
    assert tokens["user"]["roles"] == ["admin"]
    assert run_sql("SELECT details->>'via' FROM audit_log WHERE action = 'user_created'") == [
        ("bootstrap",)
    ]


def test_el_administrador_inicial_no_se_repite_ni_pisa_a_nadie(
    empty_database: None, settings: Settings
) -> None:
    configured = cloud_settings(settings, **bootstrap())
    with TestClient(create_app(configured)) as client:
        login(client, "demo@tesis.example", "contrasena-demo-1234")
        client.post(  # el administrador cambia su contraseña
            "/api/v1/auth/change-password",
            json={"current_password": "contrasena-demo-1234", "new_password": DEFAULT_PASSWORD},
            headers={
                "Authorization": "Bearer "
                + login(client, "demo@tesis.example", "contrasena-demo-1234")["access_token"]
            },
        )
    # Reinicios con las mismas variables, o con otro correo, no crean ni cambian nada.
    for overrides in ({}, {"bootstrap_admin_email": "otro@tesis.example"}):
        with TestClient(create_app(cloud_settings(settings, **bootstrap(**overrides)))) as client:
            login(client, "demo@tesis.example", DEFAULT_PASSWORD)
    assert run_sql("SELECT count(*) FROM users")[0][0] == 1


def test_sin_variables_de_administrador_no_se_crea_ninguno(
    empty_database: None, settings: Settings
) -> None:
    with TestClient(create_app(cloud_settings(settings))):
        pass
    assert run_sql("SELECT count(*) FROM users")[0][0] == 0


def test_si_la_base_no_responde_el_arranque_falla_con_claridad(settings: Settings) -> None:
    broken = cloud_settings(settings, database_url=UNREACHABLE_DATABASE_URL)
    with pytest.raises(OSError), TestClient(create_app(broken)):
        pass


def test_el_cli_migrate_crea_las_tablas(
    empty_database: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert TEST_DATABASE_URL is not None
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)
    get_settings.cache_clear()
    try:
        assert main(["migrate"]) == 0
    finally:
        get_settings.cache_clear()
    assert "al día" in capsys.readouterr().out
    assert existing_tables() == list(APP_TABLES)


def test_todas_las_tablas_tienen_rls_activado(migrated_database: None) -> None:
    """Defensa para Supabase: la API de datos no ve tablas. Un modelo nuevo sin RLS falla aquí."""
    without_rls = run_sql(
        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity ORDER BY 1"
    )
    assert without_rls == []
