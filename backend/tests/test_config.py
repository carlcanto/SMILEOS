import pytest
from pydantic import ValidationError

from app.shared.config import Settings

SECRET = "x" * 40


def build(**env: str) -> Settings:
    env.setdefault("jwt_secret", SECRET)
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
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("CORS_ORIGINS", "https://a.vercel.app, https://b.example.com ,")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["https://a.vercel.app", "https://b.example.com"]


def test_cors_vacio_por_defecto() -> None:
    assert build(database_url="postgresql+asyncpg://u:p@db/x").cors_origins == []


def test_arranque_falla_si_falta_el_secreto_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url="postgresql+asyncpg://u:p@db/x")
    assert "jwt_secret" in str(error.value)


def test_secreto_jwt_corto_se_rechaza() -> None:
    with pytest.raises(ValidationError):
        build(database_url="postgresql+asyncpg://u:p@db/x", jwt_secret="corto")


def test_vida_de_los_tokens_por_defecto() -> None:
    settings = build(database_url="postgresql+asyncpg://u:p@db/x")
    assert settings.access_token_minutes == 15
    assert settings.refresh_token_days == 7


SUPABASE_SESSION = (
    "postgresql://postgres.abcdef:pw@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
)


def test_sslmode_de_libpq_se_traduce_al_ssl_de_asyncpg() -> None:
    settings = build(database_url="postgresql://u:p@db.example.com:5432/x?sslmode=require")
    assert settings.database_url == "postgresql+asyncpg://u:p@db.example.com:5432/x?ssl=require"


def test_el_parametro_pgbouncer_de_prisma_se_descarta() -> None:
    settings = build(database_url="postgresql://u:p@db.example.com:5432/x?pgbouncer=true")
    assert settings.database_url == "postgresql+asyncpg://u:p@db.example.com:5432/x"


def test_un_host_de_supabase_usa_ssl_por_defecto() -> None:
    settings = build(database_url=SUPABASE_SESSION)
    assert settings.database_url.endswith("/postgres?ssl=require")
    assert settings.database_url.startswith("postgresql+asyncpg://postgres.abcdef:pw@")


def test_el_ssl_explicito_se_respeta() -> None:
    settings = build(database_url=SUPABASE_SESSION + "?ssl=verify-full")
    assert settings.database_url.endswith("?ssl=verify-full")


def test_la_contrasena_con_caracteres_especiales_se_conserva() -> None:
    from sqlalchemy.engine import make_url

    url = "postgresql://postgres.abc:p%40ss%23w%2Frd@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    settings = build(database_url=url)
    assert make_url(settings.database_url).password == "p@ss#w/rd"


def test_el_transaction_pooler_de_supabase_se_rechaza_con_un_mensaje_claro() -> None:
    with pytest.raises(ValidationError, match="Session pooler"):
        build(database_url=SUPABASE_SESSION.replace(":5432", ":6543"))


def test_el_puerto_6543_en_otro_servidor_no_se_toca() -> None:
    url = "postgresql+asyncpg://u:p@mi-servidor.example.com:6543/x"
    assert build(database_url=url).database_url == url


def test_una_url_con_puerto_invalido_da_un_error_de_configuracion() -> None:
    with pytest.raises(ValidationError):
        build(database_url="postgresql://u:p@host:no-es-puerto/x?sslmode=require")


def test_las_migraciones_al_arrancar_estan_apagadas_por_defecto() -> None:
    assert build(database_url="postgresql+asyncpg://u:p@db/x").run_migrations_on_start is False


def test_el_administrador_inicial_se_define_completo_o_no_se_define() -> None:
    url = "postgresql+asyncpg://u:p@db/x"
    with pytest.raises(ValidationError, match="las tres juntas"):
        build(database_url=url, bootstrap_admin_email="a@example.com")
    complete = build(
        database_url=url,
        bootstrap_admin_email="a@example.com",
        bootstrap_admin_name="Admin",
        bootstrap_admin_password="una-contrasena-larga",
    )
    assert complete.bootstrap_admin_email == "a@example.com"
    # Variables vacías (como las deja un panel sin valor) cuentan como no definidas.
    build(
        database_url=url,
        bootstrap_admin_email="",
        bootstrap_admin_name="",
        bootstrap_admin_password="",
    )
