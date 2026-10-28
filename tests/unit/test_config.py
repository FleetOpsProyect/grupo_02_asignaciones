"""Pruebas de configuración."""

from __future__ import annotations

from assignments.config import Settings, get_settings


def test_settings_reads_database_url_alias_and_defaults() -> None:
    settings = Settings(database_url="postgresql://unused")

    assert settings.app_name == "ms-asignaciones"
    assert settings.app_port == 8000
    assert settings.database_pool_size == 5


def test_get_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://from-env")

    assert get_settings().database_url == "postgresql://from-env"
