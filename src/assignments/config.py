"""Configuracion del servicio, leida de variables de entorno o de un archivo .env."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno soportadas por el arquetipo.

    Las variables especificas de negocio (BROKER_URL, VEHICULOS_URL,
    CONDUCTORES_URL, HTTP_TIMEOUT_MS, ...) se agregan aqui cuando se
    implementen los adapters que las necesitan.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ms-asignaciones"
    app_port: int = 8000
    log_level: str = "INFO"

    # Usamos credenciales genericas estándar de Postgres como default.
    # En runtime o Docker, Pydantic sobrescribirá esto automáticamente con tu DATABASE_URL real.
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/assignments",
        validation_alias="DATABASE_URL",
    )

    redis_url: str | None = None

    database_pool_size: int = 5
    database_pool_timeout_seconds: int = 5


def get_settings() -> Settings:
    """Construye la configuracion a partir del entorno actual."""
    return Settings()
