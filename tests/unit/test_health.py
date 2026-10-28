"""Pruebas de /health."""

from __future__ import annotations

from flask.testing import FlaskClient


def test_health_returns_200_with_expected_body(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "UP", "service": "ms-asignaciones"}
