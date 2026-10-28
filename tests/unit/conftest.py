"""Fixtures compartidas por las pruebas unitarias del arquetipo."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from flask import Flask
from flask.testing import FlaskClient

from assignments.config import Settings
from assignments.main import create_app
from tests.unit.fakes import FakeHealthCheck


@pytest.fixture
def make_app() -> Callable[[list[FakeHealthCheck]], Flask]:
    """Fabrica una app Flask con verificaciones de /ready inyectadas a mano."""

    def _make_app(checks: list[FakeHealthCheck]) -> Flask:
        settings = Settings(database_url="postgresql+psycopg://unused:unused@unused/unused")
        return create_app(settings=settings, readiness_checks=list(checks))

    return _make_app


@pytest.fixture
def healthy_app(make_app: Callable[[list[FakeHealthCheck]], Flask]) -> Flask:
    return make_app([FakeHealthCheck("database", True), FakeHealthCheck("cache", True)])


@pytest.fixture
def client(healthy_app: Flask) -> FlaskClient:
    return healthy_app.test_client()
