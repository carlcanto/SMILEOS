"""Configuración leída solo de variables de entorno.

El mismo código corre en el perfil ``local`` (clínica) y en el perfil ``cloud``
(presentación); lo único que cambia son estas variables.
"""

from functools import lru_cache
from typing import Annotated, Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

SUPABASE_HOST_SUFFIXES = (".supabase.com", ".supabase.co")
ASYNCPG_PREFIX = "postgresql+asyncpg://"


def normalize_database_url(value: str) -> str:
    """Acepta la cadena de conexión tal como la entregan Supabase, Render o Prisma.

    - ``postgresql://`` y ``postgres://`` se convierten al driver asíncrono.
    - ``sslmode=`` (libpq) pasa a ``ssl=`` (asyncpg) y se descarta ``pgbouncer=true``.
    - Un host de Supabase sin ``ssl`` usa ``ssl=require``: el tráfico va cifrado.
    - El *Transaction pooler* de Supabase (puerto 6543) no admite sentencias preparadas,
      que SQLAlchemy usa siempre: se rechaza con un mensaje claro en vez de fallar luego.
    """
    for prefix in ("postgresql://", "postgres://"):
        if value.startswith(prefix):
            value = ASYNCPG_PREFIX + value[len(prefix) :]
    if not value.startswith(ASYNCPG_PREFIX):
        return value
    try:
        url = make_url(value)
    except ArgumentError as error:
        raise ValueError("DATABASE_URL no tiene un formato válido") from error

    host = url.host or ""
    is_supabase = host.endswith(SUPABASE_HOST_SUFFIXES)
    if is_supabase and host.endswith(".pooler.supabase.com") and url.port == 6543:
        raise ValueError(
            "DATABASE_URL usa el Transaction pooler de Supabase (puerto 6543), que no admite "
            "sentencias preparadas. Use el Session pooler (puerto 5432) desde el botón Connect."
        )

    query = dict(url.query)
    changed = False
    if "sslmode" in query:
        query["ssl"] = query.pop("sslmode")
        changed = True
    if "pgbouncer" in query:
        del query["pgbouncer"]
        changed = True
    if is_supabase and "ssl" not in query:
        query["ssl"] = "require"
        changed = True
    if not changed:
        return value
    return url.set(query=query).render_as_string(hide_password=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_profile: Literal["local", "cloud"] = "local"
    database_url: str
    # Lista separada por comas. Solo hace falta en la nube (Vercel y Render
    # tienen orígenes distintos); en local nginx sirve todo desde un origen.
    cors_origins: Annotated[list[str], NoDecode] = []
    storage_backend: Literal["local", "supabase"] = "local"
    storage_local_path: str = "/srv/uploads"
    log_level: str = "INFO"
    worker_poll_seconds: float = 30.0
    # Firma de los tokens de acceso. Obligatorio y distinto en cada instalación.
    jwt_secret: str
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    # Funciones que el frontend consulta en GET /api/v1/config/public.
    feature_patient_portal: bool = False
    # Aplica las migraciones al arrancar la API. Pensado para la nube, donde no hay una
    # terminal para correr `alembic`: basta apuntar DATABASE_URL a cualquier base vacía.
    run_migrations_on_start: bool = False
    # Si la base no tiene usuarios, crea este administrador al arrancar. Opcionales, pero
    # se definen las tres juntas. Una vez entrado al sistema conviene borrarlas.
    bootstrap_admin_email: str | None = None
    bootstrap_admin_name: str | None = None
    bootstrap_admin_password: str | None = None

    @model_validator(mode="after")
    def bootstrap_admin_is_all_or_nothing(self) -> Self:
        given = [
            self.bootstrap_admin_email,
            self.bootstrap_admin_name,
            self.bootstrap_admin_password,
        ]
        if any(given) and not all(given):
            raise ValueError(
                "BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_NAME y BOOTSTRAP_ADMIN_PASSWORD "
                "se definen las tres juntas o ninguna"
            )
        return self

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_is_long_enough(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres")
        return value

    @field_validator("database_url")
    @classmethod
    def use_asyncpg_driver(cls, value: str) -> str:
        return normalize_database_url(value)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
