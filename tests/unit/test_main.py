"""Pruebas del cableado de la aplicación."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from assignments.config import Settings
from assignments.main import create_app


def test_create_app_builds_database_and_cache_checks_when_not_injected() -> None:
    settings = Settings(database_url="postgresql://unused", redis_url="redis://cache")
    database_check = MagicMock(name="database_check")
    cache_check = MagicMock(name="cache_check")
    engine = MagicMock(name="engine")
    redis_client = MagicMock(name="redis_client")

    with (
        patch("assignments.main.build_engine", return_value=engine) as build_engine,
        patch(
            "assignments.main.build_database_health_check",
            return_value=database_check,
        ) as build_database_check,
        patch("assignments.main.build_redis_client", return_value=redis_client),
        patch("assignments.main.build_cache_health_check", return_value=cache_check),
    ):
        app = create_app(settings=settings)

    build_engine.assert_called_once_with(settings)
    build_database_check.assert_called_once_with(engine)
    assert app.config["READINESS_CHECKS"] == [database_check, cache_check]


def test_create_app_omits_unconfigured_cache_check() -> None:
    settings = Settings(database_url="postgresql://unused")
    database_check = MagicMock(name="database_check")

    with (
        patch("assignments.main.build_engine"),
        patch("assignments.main.build_database_health_check", return_value=database_check),
        patch("assignments.main.build_redis_client", return_value=None),
        patch("assignments.main.build_cache_health_check", return_value=None),
    ):
        app = create_app(settings=settings)

    assert app.config["READINESS_CHECKS"] == [database_check]
