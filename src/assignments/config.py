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

    # URL base de los servicios de Vehiculos y Conductores (otros microservicios
    # de FleetOps). None mientras no se conecten con un ambiente real: en ese
    # caso, crear una asignacion siempre falla con 503 (servicio no disponible).
    vehiculos_url: str | None = Field(default=None, validation_alias="VEHICULOS_URL")
    conductores_url: str | None = Field(default=None, validation_alias="CONDUCTORES_URL")
    http_timeout_ms: int = Field(default=3000, validation_alias="HTTP_TIMEOUT_MS")


def get_settings() -> Settings:
    """Construye la configuracion a partir del entorno actual."""
    return Settings()
