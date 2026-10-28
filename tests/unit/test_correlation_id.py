"""Pruebas del correlation id: se devuelve el recibido o se genera uno nuevo."""

from __future__ import annotations

from flask.testing import FlaskClient


def test_correlation_id_received_is_echoed_back(client: FlaskClient) -> None:
    correlation_id = "11111111-1111-1111-1111-111111111111"

    response = client.get("/health", headers={"X-Correlation-Id": correlation_id})

    assert response.headers["X-Correlation-Id"] == correlation_id


def test_correlation_id_is_generated_when_missing(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.headers["X-Correlation-Id"] != ""
