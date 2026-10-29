"""Pruebas de /ready con verificaciones de dependencias falsas."""

from __future__ import annotations

from collections.abc import Callable

from flask import Flask

from tests.unit.fakes import FakeHealthCheck


def test_ready_returns_200_when_all_checks_pass(
    make_app: Callable[[list[FakeHealthCheck]], Flask],
) -> None:
    app = make_app([FakeHealthCheck("database", True), FakeHealthCheck("cache", True)])
    client = app.test_client()

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "UP"
    assert body["dependencies"] == {"database": True, "cache": True}


def test_ready_returns_503_when_a_check_fails(
    make_app: Callable[[list[FakeHealthCheck]], Flask],
) -> None:
    app = make_app([FakeHealthCheck("database", True), FakeHealthCheck("cache", False)])
    client = app.test_client()

    response = client.get("/ready")

    assert response.status_code == 503
    body = response.get_json()
    assert body["status"] == "DOWN"
    assert body["dependencies"]["cache"] is False
