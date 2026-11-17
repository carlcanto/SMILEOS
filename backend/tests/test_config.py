import pytest
from pydantic import ValidationError

from app.shared.config import Settings


def build(**env: str) -> Settings:
    return Settings(_env_file=None, **env)  # type: ignore[arg-type]


def test_arranque_falla_si_falta_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)
    assert "database_url" in str(error.value)


def test_perfil_por_defecto_es_local() -> None:
    assert build(database_url="postgresql+asyncpg://u:p@db/x").app_profile == "local"


def test_perfil_invalido_se_rechaza() -> None:
    with pytest.raises(ValidationError):
        build(database_url="postgresql+asyncpg://u:p@db/x", app_profile="nube")


@pytest.mark.parametrize("prefix", ["postgresql://", "postgres://"])
def test_url_de_supabase_se_convierte_a_asyncpg(prefix: str) -> None:
    settings = build(database_url=f"{prefix}u:p@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_url_asyncpg_no_se_modifica() -> None:
    url = "postgresql+asyncpg://u:p@db/x"
    assert build(database_url=url).database_url == url


def test_cors_se_lee_separado_por_comas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@db/x")
    monkeypatch.setenv("CORS_ORIGINS", "https://a.vercel.app, https://b.example.com ,")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["https://a.vercel.app", "https://b.example.com"]


def test_cors_vacio_por_defecto() -> None:
    assert build(database_url="postgresql+asyncpg://u:p@db/x").cors_origins == []
