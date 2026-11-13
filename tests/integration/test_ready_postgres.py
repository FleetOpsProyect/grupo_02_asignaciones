"""Pruebas de integracion de /ready contra un PostgreSQL real (Testcontainers)."""

from __future__ import annotations

import pytest
from testcontainers.community.postgres import PostgresContainer

from assignments.adapters.outbound.persistence import build_engine
from assignments.adapters.outbound.persistence.health import build_database_health_check
from assignments.config import Settings
from assignments.main import create_app


@pytest.mark.integration
def test_ready_returns_200_against_a_real_database() -> None:
    with PostgresContainer("postgres:16-alpine", driver="psycopg") as postgres:
        settings = Settings(database_url=postgres.get_connection_url())
        engine = build_engine(settings)
        app = create_app(settings=settings, readiness_checks=[build_database_health_check(engine)])
        client = app.test_client()

        response = client.get("/ready")

        assert response.status_code == 200
        assert response.get_json()["dependencies"]["database"] is True


@pytest.mark.integration
def test_ready_returns_503_when_database_is_unreachable() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:1/doesnotexist",
        database_pool_timeout_seconds=1,
    )
    engine = build_engine(settings)
    app = create_app(settings=settings, readiness_checks=[build_database_health_check(engine)])
    client = app.test_client()

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.get_json()["dependencies"]["database"] is False
