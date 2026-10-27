"""Pruebas del formato de error estandar ante un 404 de una ruta inexistente."""

from __future__ import annotations

from flask.testing import FlaskClient


def test_unknown_route_returns_404_with_standard_error_format(client: FlaskClient) -> None:
    response = client.get("/ruta-que-no-existe")

    assert response.status_code == 404
    body = response.get_json()
    assert set(body.keys()) == {"codigo", "mensaje", "timestamp", "ruta", "correlation_id"}
    assert body["codigo"] == "RECURSO_NO_ENCONTRADO"
    assert body["ruta"] == "/ruta-que-no-existe"
