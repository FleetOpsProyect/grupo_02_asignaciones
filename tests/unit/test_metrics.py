"""Pruebas de /metrics."""

from __future__ import annotations

from flask.testing import FlaskClient


def test_metrics_returns_prometheus_format(client: FlaskClient) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"# HELP" in response.data
    assert b"# TYPE" in response.data
