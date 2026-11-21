"""Configuración leída solo de variables de entorno.

El mismo código corre en el perfil ``local`` (clínica) y en el perfil ``cloud``
(presentación); lo único que cambia son estas variables.
"""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_is_long_enough(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres")
        return value

    @field_validator("database_url")
    @classmethod
    def use_asyncpg_driver(cls, value: str) -> str:
        """Supabase y Render entregan ``postgresql://``; SQLAlchemy async necesita asyncpg."""
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix) :]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
