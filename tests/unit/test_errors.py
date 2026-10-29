"""Pruebas del formato de error estandar ante un 404 de una ruta inexistente."""

from __future__ import annotations

from flask import abort
from flask.testing import FlaskClient


def test_unknown_route_returns_404_with_standard_error_format(client: FlaskClient) -> None:
    response = client.get("/ruta-que-no-existe")

    assert response.status_code == 404
    body = response.get_json()
    assert set(body.keys()) == {"codigo", "mensaje", "timestamp", "ruta", "correlation_id"}
    assert body["codigo"] == "RECURSO_NO_ENCONTRADO"
    assert body["ruta"] == "/ruta-que-no-existe"


def test_http_exception_uses_status_phrase_for_unmapped_status(client: FlaskClient) -> None:
    client.application.add_url_rule("/teapot", view_func=lambda: abort(418))

    response = client.get("/teapot")

    assert response.status_code == 418
    assert response.get_json()["codigo"] == "I'M_A_TEAPOT"


def test_unexpected_exception_returns_internal_error(client: FlaskClient) -> None:
    def raise_error() -> None:
        raise RuntimeError("boom")

    client.application.add_url_rule("/unexpected", view_func=raise_error)

    response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.get_json()["codigo"] == "ERROR_INTERNO"
    assert response.get_json()["mensaje"] == "Ha ocurrido un error inesperado"
