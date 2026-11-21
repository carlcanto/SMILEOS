from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.cli import main
from app.shared.config import get_settings
from tests.conftest import (
    DEFAULT_PASSWORD,
    TEST_DATABASE_URL,
    TEST_JWT_SECRET,
    login,
    requires_database,
    run_sql,
)

pytestmark = requires_database


@pytest.fixture
def cli_env(monkeypatch: pytest.MonkeyPatch, clean_database: None) -> Iterator[None]:
    assert TEST_DATABASE_URL is not None
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("ADMIN_PASSWORD", DEFAULT_PASSWORD)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_create_admin_crea_un_administrador_que_puede_entrar(
    cli_env: None, client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["create-admin", "--email", "Dra@Clinica.local", "--name", "Doctora Prueba"])
    assert code == 0
    assert "dra@clinica.local" in capsys.readouterr().out
    tokens = login(client, "dra@clinica.local")
    assert tokens["user"]["roles"] == ["admin"]
    assert run_sql("SELECT details->>'via' FROM audit_log WHERE action = 'user_created'") == [
        ("cli",)
    ]


def test_create_admin_con_correo_repetido_falla_con_mensaje(
    cli_env: None, capsys: pytest.CaptureFixture[str]
) -> None:
    args = ["create-admin", "--email", "dra@clinica.local", "--name", "Doctora"]
    assert main(args) == 0
    capsys.readouterr()
    assert main(args) == 1
    assert "Ya existe un usuario" in capsys.readouterr().err


def test_create_admin_con_contrasena_debil_falla(
    cli_env: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "corta")
    code = main(["create-admin", "--email", "dra@clinica.local", "--name", "Doctora"])
    assert code == 1
    assert "10 caracteres" in capsys.readouterr().err
    assert run_sql("SELECT count(*) FROM users")[0][0] == 0
